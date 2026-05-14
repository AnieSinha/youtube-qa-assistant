"""
TubeAI — YouTube AI Assistant — FastAPI Backend
================================================
Supports 1–3 YouTube videos processed into a single unified FAISS index.

Endpoints:
  POST /api/process      — start the ingestion pipeline (1-3 YouTube URLs)
  GET  /api/status       — poll current pipeline state
  POST /api/ask          — answer a question (JSON response)
  POST /api/ask/stream   — answer a question (SSE streaming response)
  GET  /health           — health check
  GET  /                 — serve the frontend SPA
"""

import os
import sys
import json
import logging
import threading
from contextlib import asynccontextmanager
from typing import Optional, List

# ------------------------------------------------------------------
# Suppress noisy startup warnings before any heavy imports
# ------------------------------------------------------------------
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# ------------------------------------------------------------------
# Resolve project root and make app/ importable regardless of CWD
# ------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "app"))

# Force working directory to project root so relative data/ paths work
os.chdir(_PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from transcriber import generate_transcript
from chunker import chunk_text
from embeddings import create_embeddings
from vector_store import build_vector_store, load_vector_store
from retriever import retrieve_chunks
from qa_engine import answer_question, stream_answer


# ------------------------------------------------------------------
# In-memory pipeline state (thread-safe)
# ------------------------------------------------------------------
_state: dict = {
    "status":         "idle",
    "message":        "No video loaded yet.",
    "video_url":      None,       # first URL (backward compat)
    "video_urls":     [],         # all URLs in this session
    "video_titles":   {},         # {url: title}
    "error":          None,
    "index":          None,
    "chunks":         None,       # list[str]
    "chunk_meta":     None,       # list[dict] parallel to chunks: {url,title,video_idx}
    "video_segments": {},         # {url: segments_list}
}
_lock = threading.Lock()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _normalize_yt_url(url: str) -> str:
    """Convert YouTube Shorts / share URLs to standard watch URLs so yt-dlp and the frontend embed work uniformly."""
    import re
    # Shorts: https://youtube.com/shorts/VIDEO_ID[?...]
    m = re.match(r'https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]+)', url)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    # youtu.be short links → already handled by yt-dlp, but normalize for consistency
    m2 = re.match(r'https?://youtu\.be/([A-Za-z0-9_-]+)', url)
    if m2:
        return f"https://www.youtube.com/watch?v={m2.group(1)}"
    return url


def _find_timestamp(chunk_text: str, segments: list) -> str:
    """Word-overlap timestamp search within a given segment list."""
    if not segments:
        return "00:00"
    chunk_words = set(chunk_text.lower().split())
    best_score, best_start = 0, 0.0
    for seg in segments:
        seg_words = set(seg["text"].lower().split())
        overlap = len(chunk_words & seg_words)
        if overlap > best_score:
            best_score = overlap
            best_start = seg["start"]
    m, s = divmod(int(best_start), 60)
    return f"{m:02d}:{s:02d}"


def _build_sources(retrieved: list, chunk_meta: list, video_segments: dict, fallback_url: str) -> list:
    """Build source-reference dicts for API responses."""
    sources = []
    for chunk in retrieved:
        cid = chunk["chunk_id"]
        if chunk_meta and cid < len(chunk_meta):
            meta = chunk_meta[cid]
            ts = _find_timestamp(chunk["text"], video_segments.get(meta["url"], []))
            sources.append({
                "timestamp": ts,
                "preview":   chunk["text"][:200].replace("\n", " "),
                "url":       meta["url"],
                "title":     meta["title"],
                "video_idx": meta["video_idx"],
            })
        else:
            # Fallback for indexes loaded from disk (no metadata in memory)
            try:
                from timestamp_mapper import get_timestamps_for_chunks
                ts = get_timestamps_for_chunks([chunk])[0]
            except Exception:
                ts = "00:00"
            sources.append({
                "timestamp": ts,
                "preview":   chunk["text"][:200].replace("\n", " "),
                "url":       fallback_url or "",
                "title":     "Video",
                "video_idx": 0,
            })
    return sources


# ------------------------------------------------------------------
# Background model warm-up
# ------------------------------------------------------------------
def _warm_up_models():
    try:
        from embeddings import warm_up as warm_emb
        from transcriber import warm_up as warm_tr
        print("[warm-up] Pre-loading ML models...")
        warm_emb()
        warm_tr()
        print("[warm-up] Models ready.")
    except Exception as exc:
        print(f"[warm-up] Warning: {exc}")


# ------------------------------------------------------------------
# Lifespan: auto-load existing FAISS index + warm up models
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        index, chunks = load_vector_store()
        with _lock:
            _state.update({
                "status":  "ready",
                "message": f"Loaded existing index: {len(chunks)} chunks ready.",
                "index":   index,
                "chunks":  chunks,
            })
        print(f"[startup] Auto-loaded vector store — {len(chunks)} chunks.")
    except FileNotFoundError:
        print("[startup] No existing vector store — process a YouTube URL to get started.")

    threading.Thread(target=_warm_up_models, daemon=True).start()
    yield


# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------
app = FastAPI(
    title="TubeAI — YouTube AI Assistant",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Request models
# ------------------------------------------------------------------
class ProcessRequest(BaseModel):
    url:  Optional[str]       = None   # single URL (backward compat)
    urls: Optional[List[str]] = None   # multi-video (1–3)

    def resolve_urls(self) -> list[str]:
        raw = []
        if self.urls:
            raw = [u.strip() for u in self.urls if u.strip()][:3]
        elif self.url:
            raw = [self.url.strip()]
        return [_normalize_yt_url(u) for u in raw]


class QuestionRequest(BaseModel):
    question: str


# ------------------------------------------------------------------
# Background pipeline worker
# ------------------------------------------------------------------
def _pipeline_worker(urls: list[str]) -> None:
    try:
        from yt_dlp import YoutubeDL

        for d in ("data/audio", "data/transcripts", "data/faiss_index"):
            os.makedirs(d, exist_ok=True)

        # Remove old audio files
        audio_folder = "data/audio"
        for f in os.listdir(audio_folder):
            if f != ".gitkeep":
                try:
                    os.remove(os.path.join(audio_folder, f))
                except OSError:
                    pass

        all_chunks: list[str]  = []
        all_chunk_meta: list   = []
        all_segments: dict     = {}
        video_titles: dict     = {}
        n = len(urls)

        for idx, url in enumerate(urls):
            tag = f"[{idx + 1}/{n}] " if n > 1 else ""

            with _lock:
                _state["message"] = f"{tag}Downloading audio from YouTube..."

            ydl_opts = {
                "format":     "bestaudio/best",
                "outtmpl":    f"data/audio/video_{idx}.%(ext)s",
                "quiet":      True,
                "noplaylist": True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info  = ydl.extract_info(url, download=True)
                title = info.get("title", f"Video {idx + 1}")

            video_titles[url] = title

            # Locate the downloaded file
            audio_files = sorted(
                f for f in os.listdir(audio_folder)
                if f.startswith(f"video_{idx}.") and f != ".gitkeep"
            )
            if not audio_files:
                raise RuntimeError(f"Download produced no audio file for video {idx + 1}.")
            audio_path = os.path.join(audio_folder, audio_files[0])

            with _lock:
                short_title = title[:40] + ("…" if len(title) > 40 else "")
                _state["message"] = f"{tag}Transcribing '{short_title}'..."

            transcript, segments = generate_transcript(audio_path)
            all_segments[url] = segments

            video_chunks = chunk_text(transcript)
            all_chunks.extend(video_chunks)
            all_chunk_meta.extend(
                {"url": url, "title": title, "video_idx": idx}
                for _ in video_chunks
            )

        if not all_chunks:
            raise RuntimeError("No transcript content could be extracted from the provided video(s). "
                               "The video may be too short, audio-only, or blocked in your region.")

        with _lock:
            _state["message"] = f"Building unified index ({len(all_chunks)} chunks)…"

        embeddings = create_embeddings(all_chunks)
        index      = build_vector_store(all_chunks, embeddings)

        summary = f"{n} video{'s' if n > 1 else ''}, {len(all_chunks)} chunks indexed."
        with _lock:
            _state.update({
                "status":         "ready",
                "message":        f"Ready! {summary}",
                "video_url":      urls[0],
                "video_urls":     urls,
                "video_titles":   video_titles,
                "error":          None,
                "index":          index,
                "chunks":         all_chunks,
                "chunk_meta":     all_chunk_meta,
                "video_segments": all_segments,
            })

    except Exception as exc:
        with _lock:
            _state.update({
                "status":  "error",
                "error":   str(exc),
                "message": f"Pipeline failed: {exc}",
            })


# ------------------------------------------------------------------
# API routes
# ------------------------------------------------------------------
@app.post("/api/process")
async def process_video(req: ProcessRequest):
    """Start the ingestion pipeline for 1–3 YouTube URLs."""
    urls = req.resolve_urls()
    if not urls:
        raise HTTPException(status_code=422, detail="At least one YouTube URL is required.")
    if len(urls) > 3:
        raise HTTPException(status_code=422, detail="Maximum 3 URLs allowed.")

    with _lock:
        if _state["status"] == "processing":
            raise HTTPException(status_code=409, detail="Already processing — wait for it to finish.")
        _state.update({
            "status":         "processing",
            "message":        "Starting pipeline…",
            "video_url":      urls[0],
            "video_urls":     urls,
            "video_titles":   {},
            "error":          None,
            "index":          None,
            "chunks":         None,
            "chunk_meta":     None,
            "video_segments": {},
        })

    threading.Thread(target=_pipeline_worker, args=(urls,), daemon=True).start()
    count = len(urls)
    return {"status": "processing", "message": f"Processing {count} video{'s' if count > 1 else ''}. Poll /api/status."}


@app.get("/api/status")
async def get_status():
    with _lock:
        return {
            "status":       _state["status"],
            "message":      _state["message"],
            "video_url":    _state["video_url"],
            "video_urls":   _state["video_urls"],
            "video_titles": _state["video_titles"],
            "error":        _state["error"],
        }


@app.post("/api/ask")
async def ask_question_json(req: QuestionRequest):
    """Answer a question — JSON response."""
    with _lock:
        status       = _state["status"]
        index        = _state["index"]
        chunks       = _state["chunks"]
        chunk_meta   = _state["chunk_meta"]
        video_segs   = _state["video_segments"]
        fallback_url = _state["video_url"]

    if status != "ready":
        raise HTTPException(status_code=400, detail="No video is ready. Process a YouTube URL first.")
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    retrieved = retrieve_chunks(req.question, index=index, chunks=chunks, top_k=5)
    if not retrieved:
        return {"answer": "No relevant content found for your question.", "sources": []}

    answer  = answer_question(req.question, retrieved)
    sources = _build_sources(retrieved, chunk_meta, video_segs, fallback_url)
    return {"answer": answer, "sources": sources}


@app.post("/api/ask/stream")
async def ask_question_stream(req: QuestionRequest):
    """
    Answer a question with Server-Sent Events (SSE) streaming.

    Event types:
      sources — [ {timestamp, preview, url, title, video_idx} ]
      token   — { "content": "…" }
      done    — {}
      error   — { "detail": "…" }
    """
    with _lock:
        status       = _state["status"]
        index        = _state["index"]
        chunks       = _state["chunks"]
        chunk_meta   = _state["chunk_meta"]
        video_segs   = _state["video_segments"]
        fallback_url = _state["video_url"]

    def _err(msg):
        async def _gen():
            yield f"event: error\ndata: {json.dumps({'detail': msg})}\n\n"
        return StreamingResponse(_gen(), media_type="text/event-stream")

    if status != "ready":
        return _err("No video is ready. Process a YouTube URL first.")
    if not req.question.strip():
        return _err("Question cannot be empty.")

    retrieved = retrieve_chunks(req.question, index=index, chunks=chunks, top_k=5)

    if not retrieved:
        async def _empty():
            yield f"event: token\ndata: {json.dumps({'content': 'No relevant content found.'})}\n\n"
            yield f"event: sources\ndata: {json.dumps([])}\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(_empty(), media_type="text/event-stream")

    sources = _build_sources(retrieved, chunk_meta, video_segs, fallback_url)

    def _generate():
        try:
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"
            for token in stream_answer(req.question, retrieved):
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"
            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(_generate(), media_type="text/event-stream")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TubeAI"}


# ------------------------------------------------------------------
# Serve the frontend SPA (Vite build output)
# ------------------------------------------------------------------
_FRONTEND_DIR = os.path.join(_PROJECT_ROOT, "frontend")

if os.path.isdir(_FRONTEND_DIR):
    _assets_dir = os.path.join(_FRONTEND_DIR, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))
