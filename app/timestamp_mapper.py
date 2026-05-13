import json
import os

SEGMENTS_PATH = "data/transcripts/segments.json"


def load_segments() -> list[dict]:
    """
    Load Whisper segment data from disk.

    Returns:
        List of segment dicts: [{start: float, end: float, text: str}, ...]

    Raises:
        FileNotFoundError: if segments.json doesn't exist yet.
    """
    if not os.path.exists(SEGMENTS_PATH):
        raise FileNotFoundError(
            "segments.json not found. Re-run the pipeline with the updated "
            "transcriber that saves segment timestamps."
        )
    with open(SEGMENTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format string."""
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes:02d}:{secs:02d}"


def find_timestamp(chunk_text: str, segments: list[dict] | None = None) -> str:
    """
    Find the best matching Whisper segment timestamp for a given chunk text.

    Uses character-level overlap to match the chunk against segments.  The
    segment whose text has the highest overlap with the chunk wins.

    Args:
        chunk_text: The retrieved chunk text to locate.
        segments:   (Optional) Pre-loaded segments list. Loaded from disk if None.

    Returns:
        A timestamp string in MM:SS format (e.g. "02:35"), or "00:00" if no
        match is found.
    """
    if segments is None:
        segments = load_segments()

    chunk_words = set(chunk_text.lower().split())
    best_score = 0
    best_start = 0.0

    for seg in segments:
        seg_words = set(seg["text"].lower().split())
        overlap = len(chunk_words & seg_words)
        if overlap > best_score:
            best_score = overlap
            best_start = seg["start"]

    return _format_timestamp(best_start)


def get_timestamps_for_chunks(retrieved_chunks: list[dict]) -> list[str]:
    """
    Return a timestamp string for each retrieved chunk.

    Args:
        retrieved_chunks: List of chunk dicts (each must have a 'text' key).

    Returns:
        List of MM:SS timestamp strings, parallel to retrieved_chunks.
    """
    segments = load_segments()
    return [find_timestamp(chunk["text"], segments) for chunk in retrieved_chunks]
