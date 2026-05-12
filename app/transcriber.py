import whisper

model = whisper.load_model("base")

def generate_transcript(audio_path):

    result = model.transcribe(audio_path)

    transcript = result["text"]

    with open("data/transcripts/transcript.txt", "w", encoding="utf-8") as f:
        f.write(transcript)

    print("Transcript generated successfully")

    return transcript