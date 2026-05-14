"""
TubeAI — YouTube AI Assistant -- FastAPI Backend
========================================
Wraps the existing CLI pipeline (app/) behind a REST API.

Endpoints:
  POST /api/process      -- start the ingestion pipeline for a YouTube URL
  GET  /api/status       -- poll current pipeline state
  POST /api/ask          -- answer a question (JSON response)
  POST /api/ask/stream   -- answer a question (SSE streaming response)
  GET  /health           -- health check
  GET  /                 -- serve the frontend SPA
"""

import os
import sys
import json
import logging
import threading
from contextlib import asynccontextmanager

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

# Force the working directory to project root so relative data/ paths work
os.chdir(_PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

from download_video import download_audio
from transcriber import generate_transcript
from chunker import chunk_text
from embeddings import create_embeddings
from vector_store import build_vector_store, load_vector_store
from retriever import retrieve_chunks
from qa_engine import answer_question, stream_answer
from timestamp_mapper import get_timestamps_for_chunks


# ------------------------------------------------------------------
# In-memory pipeline state (protected by a lock for thread safety)
# ------------------------------------------------------------------
_state: dict = {
    "status": "idle",       # idle | processing | ready | error
    "message": "No video loaded yet.",
    "video_url": None,
    "error": None,
    "index": None,
    "chunks": None,
}
_lock = threading.Lock()


# ------------------------------------------------------------------
# Background model warm-up -- loads ML models while the server is
# already accepting requests, so the first /api/process isn't slow.
# ------------------------------------------------------------------
def _warm_up_models():
    """Pre-load Whisper + SentenceTransformer in a background thread."""
    try:
        from embeddings import warm_up as warm_embeddings
        from transcriber import warm_up as warm_transcriber
        print("[warm-up] Pre-loading ML models in background...")
        warm_embeddings()
        warm_transcriber()
        print("[warm-up] All models ready.")
    except Exception as exc:
        print(f"[warm-up] Warning: model pre-load failed: {exc}")


# ------------------------------------------------------------------
# Lifespan: auto-load an existing FAISS index on startup if present
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        index, chunks = load_vector_store()
        with _lock:
            _state.update({
                "status": "ready",
                "message": f"Loaded existing index: {len(chunks)} chunks ready.",
                "index": index,
                "chunks": chunks,
            })
        print(f"[startup] Auto-loaded vector store -- {len(chunks)} chunks.")
    except FileNotFoundError:
        print("[startup] No existing vector store found -- process a YouTube URL to get started.")

    # Kick off model warm-up in background so the server starts immediately
    threading.Thread(target=_warm_up_models, daemon=True).start()

    yield  # server runs here


# ------------------------------------------------------------------
# App setup
# ------------------------------------------------------------------
app = FastAPI(
    title="TubeAI — YouTube AI Assistant",
    version="2.0.0",
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
# Request / response models
# ------------------------------------------------------------------
class ProcessRequest(BaseModel):
    url: str

class QuestionRequest(BaseModel):
    question: str


# ------------------------------------------------------------------
# Background pipeline worker (runs in a daemon thread)
# ------------------------------------------------------------------
def _pipeline_worker(url: str) -> None:
    try:
        # Ensure data directories exist (guards against missing .gitkeep files)
        for d in ("data/audio", "data/transcripts", "data/faiss_index"):
            os.makedirs(d, exist_ok=True)

        with _lock:
            _state["message"] = "Downloading audio from YouTube..."

        download_audio(url)

        audio_folder = os.path.join(_PROJECT_ROOT, "data", "audio")
        audio_files = [f for f in os.listdir(audio_folder) if f != ".gitkeep"]
        if not audio_files:
            raise RuntimeError("Audio download failed -- no file found in data/audio/.")
        audio_path = os.path.join(audio_folder, audio_files[0])

        with _lock:
            _state["message"] = "Transcribing audio with Whisper..."

        transcript, _ = generate_transcript(audio_path)

        with _lock:
            _state["message"] = "Building vector index..."

        chunks = chunk_text(transcript)
        embeddings = create_embeddings(chunks)
        index = build_vector_store(chunks, embeddings)

        with _lock:
            _state["status"] = "ready"
            _state["message"] = f"Ready! Indexed {len(chunks)} transcript chunks."
            _state["index"] = index
            _state["chunks"] = chunks

    except Exception as exc:
        with _lock:
            _state["status"] = "error"
            _state["error"] = str(exc)
            _state["message"] = f"Pipeline failed: {exc}"


# ------------------------------------------------------------------
# API routes
# ------------------------------------------------------------------
@app.post("/api/process")
async def process_video(req: ProcessRequest):
    """Start the ingestion pipeline for a YouTube URL."""
    with _lock:
        if _state["status"] == "processing":
            raise HTTPException(status_code=409, detail="A video is already being processed.")
        _state.update({
            "status": "processing",
            "message": "Starting pipeline...",
            "video_url": req.url,
            "error": None,
            "index": None,
            "chunks": None,
        })

    thread = threading.Thread(target=_pipeline_worker, args=(req.url,), daemon=True)
    thread.start()
    return {"status": "processing", "message": "Pipeline started. Poll /api/status for updates."}


@app.get("/api/status")
async def get_status():
    """Return the current pipeline state."""
    with _lock:
        return {
            "status": _state["status"],
            "message": _state["message"],
            "video_url": _state["video_url"],
            "error": _state["error"],
        }


@app.post("/api/ask")
async def ask_question_json(req: QuestionRequest):
    """Answer a question using the processed video transcript (JSON response)."""
    with _lock:
        status = _state["status"]
        index = _state["index"]
        chunks = _state["chunks"]

    if status != "ready":
        raise HTTPException(
            status_code=400,
            detail="No video is ready. Submit a YouTube URL to /api/process first.",
        )
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")

    retrieved = retrieve_chunks(req.question, index=index, chunks=chunks, top_k=5)
    if not retrieved:
        return {"answer": "No relevant content found for your question.", "sources": []}

    answer = answer_question(req.question, retrieved)
    timestamps = get_timestamps_for_chunks(retrieved)

    sources = [
        {
            "timestamp": ts,
            "preview": chunk["text"][:200].replace("\n", " "),
        }
        for chunk, ts in zip(retrieved, timestamps)
    ]

    return {"answer": answer, "sources": sources}


@app.post("/api/ask/stream")
async def ask_question_stream(req: QuestionRequest):
    """
    Answer a question with Server-Sent Events (SSE) streaming.

    Event types:
      - "token"   : { "content": "..." }   — a chunk of the answer
      - "sources" : [ {timestamp, preview}, ... ]  — source references
      - "done"    : {}                     — stream complete
      - "error"   : { "detail": "..." }    — error occurred
    """
    with _lock:
        status = _state["status"]
        index = _state["index"]
        chunks = _state["chunks"]

    if status != "ready":
        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'detail': 'No video is ready.'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    if not req.question.strip():
        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'detail': 'Question cannot be empty.'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    retrieved = retrieve_chunks(req.question, index=index, chunks=chunks, top_k=5)

    if not retrieved:
        async def empty_stream():
            yield f"event: token\ndata: {json.dumps({'content': 'No relevant content found for your question.'})}\n\n"
            yield f"event: sources\ndata: {json.dumps([])}\n\n"
            yield "event: done\ndata: {}\n\n"
        return StreamingResponse(empty_stream(), media_type="text/event-stream")

    # Compute sources up front
    timestamps = get_timestamps_for_chunks(retrieved)
    sources = [
        {
            "timestamp": ts,
            "preview": chunk["text"][:200].replace("\n", " "),
        }
        for chunk, ts in zip(retrieved, timestamps)
    ]

    def generate():
        try:
            # Send sources first so the UI can display them alongside the answer
            yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

            # Stream answer tokens
            for token in stream_answer(req.question, retrieved):
                yield f"event: token\ndata: {json.dumps({'content': token})}\n\n"

            yield "event: done\ndata: {}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "TubeAI"}


# ------------------------------------------------------------------
# Serve the frontend SPA (supports both dev /static/ and Vite /assets/)
# ------------------------------------------------------------------
_FRONTEND_DIR = os.path.join(_PROJECT_ROOT, "frontend")

if os.path.isdir(_FRONTEND_DIR):
    # Vite builds to /assets/ — serve those
    _assets_dir = os.path.join(_FRONTEND_DIR, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    # Legacy /static/ mount for backward compat
    app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))
