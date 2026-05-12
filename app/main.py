from download_video import download_audio
from transcriber import generate_transcript
from chunker import chunk_text
from embeddings import create_embeddings

import os

url = input("Enter YouTube URL: ")

download_audio(url)

audio_file = os.listdir("data/audio")[0]

audio_path = f"data/audio/{audio_file}"

transcript = generate_transcript(audio_path)

chunks = chunk_text(transcript)

print("\nFIRST CHUNK:\n")
print(chunks[0])

print(f"\nTotal Chunks: {len(chunks)}")

embeddings = create_embeddings(chunks)

print("\nEmbedding Shape:")
print(embeddings.shape)