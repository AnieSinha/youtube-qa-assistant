import json
import os
import shutil
import sys
import whisper
import imageio_ffmpeg

# ---------------------------------------------------------------------------
# Ensure `ffmpeg.exe` is discoverable by Whisper.
#
# imageio_ffmpeg ships the binary as "ffmpeg-win-x86_64-v7.1.exe", but
# Whisper hard-codes the subprocess call to "ffmpeg".  Simply adding the
# directory to PATH does NOT work because the filename doesn't match.
#
# Fix: copy the bundled binary into the venv's Scripts/ folder as
# `ffmpeg.exe`.  That directory is already on PATH, and the name is correct.
# ---------------------------------------------------------------------------
_ffmpeg_src = imageio_ffmpeg.get_ffmpeg_exe()
_scripts_dir = os.path.dirname(sys.executable)          # …/venv/Scripts/
_ffmpeg_dst  = os.path.join(_scripts_dir, "ffmpeg.exe")

if not os.path.exists(_ffmpeg_dst):
    shutil.copy2(_ffmpeg_src, _ffmpeg_dst)

model = whisper.load_model("base")


def generate_transcript(audio_path: str) -> tuple[str, list[dict]]:
    """
    Transcribe audio using Whisper and persist both the full transcript text
    and segment-level timestamps.

    Args:
        audio_path: Path to the audio file.

    Returns:
        (transcript_text, segments) where segments is a list of dicts:
        [{start: float, end: float, text: str}, ...]
    """
    result = model.transcribe(audio_path)

    transcript = result["text"]

    # Extract segment timestamps for US-09 (timestamp-based answers)
    segments = [
        {
            "start": seg["start"],
            "end":   seg["end"],
            "text":  seg["text"].strip(),
        }
        for seg in result.get("segments", [])
    ]

    os.makedirs("data/transcripts", exist_ok=True)

    # Save full transcript text
    with open("data/transcripts/transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript)

    # Save segment timestamps as JSON
    with open("data/transcripts/segments.json", "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    print(f"Transcript generated successfully ({len(segments)} segments saved).")

    return transcript, segments