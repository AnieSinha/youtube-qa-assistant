from yt_dlp import YoutubeDL

def download_audio(url):

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'data/audio/audio.%(ext)s',
        'quiet': False
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    print("Audio downloaded successfully")