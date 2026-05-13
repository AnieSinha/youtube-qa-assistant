"""
YouTube Video Q&A Assistant — Full Pipeline
==========================================
Steps:
  1. Download audio from a YouTube URL
  2. Transcribe audio with Whisper (saves transcript.txt + segments.json)
  3. Chunk transcript text
  4. Generate embeddings for each chunk
  5. Build & persist FAISS vector index  (US-06)
  6. Interactive Q&A loop:
       a. Embed user query and retrieve top-k relevant chunks  (US-07)
       b. Generate answer via OpenAI LLM                       (US-08)
       c. Display answer with source timestamps                 (US-09)
"""

import os
import sys

# Allow imports from the app/ directory regardless of CWD
sys.path.insert(0, os.path.dirname(__file__))

from download_video import download_audio
from transcriber import generate_transcript
from chunker import chunk_text
from embeddings import create_embeddings
from vector_store import build_vector_store
from retriever import retrieve_chunks
from qa_engine import answer_question
from timestamp_mapper import get_timestamps_for_chunks


def run_pipeline(url: str) -> tuple[list[str], object]:
    """
    Execute the full preprocessing pipeline for a given YouTube URL.

    Returns:
        (chunks, faiss_index) — the text chunks and the loaded FAISS index.
    """
    print("\n[1/5] Downloading audio...")
    download_audio(url)

    audio_file = os.listdir("data/audio")[0]
    audio_path = f"data/audio/{audio_file}"

    print("\n[2/5] Transcribing audio (this may take a minute)...")
    transcript, segments = generate_transcript(audio_path)
    print(f"      → {len(segments)} segments with timestamps saved.")

    print("\n[3/5] Chunking transcript...")
    chunks = chunk_text(transcript)
    print(f"      → {len(chunks)} chunks created.")

    print("\n[4/5] Generating embeddings...")
    embeddings = create_embeddings(chunks)
    print(f"      → Embedding shape: {embeddings.shape}")

    print("\n[5/5] Building FAISS vector index...")
    index = build_vector_store(chunks, embeddings)

    return chunks, index


def qa_loop(chunks: list[str], index) -> None:
    """Interactive question-answering loop."""
    print("\n" + "=" * 60)
    print("  YouTube Q&A Assistant — Ask anything about the video!")
    print("  Type 'quit' or 'exit' to stop.")
    print("=" * 60)

    while True:
        print()
        question = input("Your question: ").strip()

        if question.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        if not question:
            print("Please enter a question.")
            continue

        # --- US-07: Retrieval ---
        print("\nSearching transcript for relevant context...")
        retrieved = retrieve_chunks(question, index=index, chunks=chunks, top_k=3)

        if not retrieved:
            print("No relevant content found for your question.")
            continue

        # --- US-09: Timestamps ---
        timestamps = get_timestamps_for_chunks(retrieved)

        # --- US-08: LLM Answer ---
        print("Generating answer...\n")
        answer = answer_question(question, retrieved)

        # Display results
        print("-" * 60)
        print(f"Answer:\n{answer}")
        print()
        print("Sources (video timestamps):")
        for i, (chunk, ts) in enumerate(zip(retrieved, timestamps), start=1):
            preview = chunk["text"][:80].replace("\n", " ")
            print(f"  [{i}] ⏱ {ts}  — \"{preview}...\"")
        print("-" * 60)


def main():
    # -----------------------------------------------------------------------
    # Option A: Full pipeline (download + process + Q&A)
    # Option B: Q&A only (reload saved index — skip download/transcription)
    # -----------------------------------------------------------------------
    if len(sys.argv) > 1 and sys.argv[1] == "--qa-only":
        # Load existing index from disk
        from vector_store import load_vector_store
        print("Loading existing vector store...")
        index, chunks = load_vector_store()
        qa_loop(chunks, index)
        return

    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("No URL provided. Exiting.")
        return

    chunks, index = run_pipeline(url)
    qa_loop(chunks, index)


if __name__ == "__main__":
    main()