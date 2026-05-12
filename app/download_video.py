import os
from yt_dlp import YoutubeDL

def download_audio(url):

    # Delete old audio files first
    audio_folder = "data/audio"

    for file in os.listdir(audio_folder):
        file_path = os.path.join(audio_folder, file)
        os.remove(file_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'data/audio/audio.%(ext)s',
        'quiet': False
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("Audio downloaded successfully")