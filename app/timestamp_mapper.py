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

    Strategy: find the segment whose text appears as a substring within the
    chunk (or has the highest sequential word overlap with the chunk).
    This avoids the bug where set-based overlap always picks the same segment.

    Args:
        chunk_text: The retrieved chunk text to locate.
        segments:   (Optional) Pre-loaded segments list. Loaded from disk if None.

    Returns:
        A timestamp string in MM:SS format (e.g. "02:35"), or "00:00" if no
        match is found.
    """
    if segments is None:
        segments = load_segments()

    chunk_lower = chunk_text.lower().strip()

    # Strategy 1: Find segment whose text is a substring of the chunk.
    # Use the FIRST matching segment (earliest timestamp).
    for seg in segments:
        seg_text = seg["text"].lower().strip()
        if seg_text and seg_text in chunk_lower:
            return _format_timestamp(seg["start"])

    # Strategy 2: Find the segment with the longest common subsequence
    # of consecutive words (not just set overlap) with the chunk.
    chunk_words = chunk_lower.split()
    best_score = 0
    best_start = 0.0

    for seg in segments:
        seg_words = seg["text"].lower().strip().split()
        if not seg_words:
            continue

        # Count how many consecutive words from the segment appear in order
        # within the chunk (sliding window match)
        score = _sequential_overlap(chunk_words, seg_words)

        if score > best_score:
            best_score = score
            best_start = seg["start"]

    return _format_timestamp(best_start)


def _sequential_overlap(chunk_words: list[str], seg_words: list[str]) -> int:
    """
    Count how many words from seg_words appear sequentially in chunk_words.
    This is a simple longest-common-substring approach on word level.
    """
    best = 0
    seg_len = len(seg_words)
    chunk_len = len(chunk_words)

    for i in range(chunk_len - seg_len + 1):
        match = 0
        for j in range(seg_len):
            if i + j < chunk_len and chunk_words[i + j] == seg_words[j]:
                match += 1
            else:
                break
        best = max(best, match)

    return best


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
