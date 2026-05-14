import json
import os
import shutil
import sys
import imageio_ffmpeg

# ---------------------------------------------------------------------------
# Ensure `ffmpeg.exe` is discoverable for audio processing.
# ---------------------------------------------------------------------------
_ffmpeg_src = imageio_ffmpeg.get_ffmpeg_exe()
_scripts_dir = os.path.dirname(sys.executable)          # .../venv/Scripts/
_ffmpeg_dst  = os.path.join(_scripts_dir, "ffmpeg.exe")

if not os.path.exists(_ffmpeg_dst):
    shutil.copy2(_ffmpeg_src, _ffmpeg_dst)

# When running via `venv\Scripts\python run.py` (without `activate`), the
# Scripts directory is NOT on PATH.  Add it so subprocess calls to `ffmpeg`
# can find the binary.
if _scripts_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _scripts_dir + os.pathsep + os.environ.get("PATH", "")


# ---------------------------------------------------------------------------
# Groq Whisper API — uses whisper-large-v3-turbo on Groq's cloud.
# Transcribes in ~5-10 seconds (vs 2+ minutes locally) with better accuracy.
# The user's GROQ_API_KEY (used for the LLM) also works for transcription.
# ---------------------------------------------------------------------------

def warm_up():
    """No-op for API-based transcription (no local model to pre-load)."""
    pass


def generate_transcript(audio_path: str) -> tuple[str, list[dict]]:
    """
    Transcribe audio using Groq's Whisper API and persist both the full
    transcript text and segment-level timestamps.

    Args:
        audio_path: Path to the audio file.

    Returns:
        (transcript_text, segments) where segments is a list of dicts:
        [{start: float, end: float, text: str}, ...]
    """
    from openai import OpenAI
    from dotenv import load_dotenv

    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )

    print("[whisper] Transcribing via Groq API (whisper-large-v3-turbo)...")

    with open(audio_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), audio_file.read()),
            model="whisper-large-v3-turbo",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
            language="en",
            temperature=0.0,
        )

    transcript = result.text

    # Extract segment timestamps
    segments = []
    for seg in getattr(result, "segments", []) or []:
        segments.append({
            "start": seg.get("start", seg["start"]) if isinstance(seg, dict) else seg.start,
            "end":   seg.get("end", seg["end"]) if isinstance(seg, dict) else seg.end,
            "text":  (seg.get("text", "") if isinstance(seg, dict) else seg.text).strip(),
        })

    os.makedirs("data/transcripts", exist_ok=True)

    # Save full transcript text
    with open("data/transcripts/transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript)

    # Save segment timestamps as JSON
    with open("data/transcripts/segments.json", "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    print(f"Transcript generated successfully ({len(segments)} segments saved).")

    return transcript, segments