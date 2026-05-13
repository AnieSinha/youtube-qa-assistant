# YouTube Video Q&A Assistant

## Project Overview

The YouTube Video Q&A Assistant is an AI-powered application that allows users to provide a YouTube video URL and ask questions about the video content.

The system extracts audio from the video, generates transcripts using Whisper, converts transcript chunks into embeddings, stores them in a FAISS vector database, and enables semantic retrieval for accurate question answering with source timestamps.

---

# Features

* YouTube video URL input
* Audio extraction via yt-dlp
* Speech-to-text transcription using Whisper (with segment timestamps)
* Transcript chunking
* Embedding generation via Sentence Transformers
* Vector database integration using FAISS
* Retrieval-based question answering using OpenAI GPT
* Timestamp-based answers (shows where in the video each answer comes from)

---

# Technologies Used

* Python
* Whisper (OpenAI)
* LangChain + LangChain-OpenAI
* Sentence Transformers (`all-MiniLM-L6-v2`)
* FAISS (CPU)
* yt-dlp

---

# Project Workflow

```
YouTube URL
    ↓
Audio Download          (download_video.py)
    ↓
Whisper Transcription   (transcriber.py)     → transcript.txt + segments.json
    ↓
Transcript Chunking     (chunker.py)
    ↓
Embedding Generation    (embeddings.py)
    ↓
FAISS Vector Storage    (vector_store.py)    → data/faiss_index/
    ↓
Retrieval Pipeline      (retriever.py)       → top-k relevant chunks
    ↓
LLM Question Answering  (qa_engine.py)       → OpenAI GPT-3.5-turbo
    ↓
Timestamp-Based Response (timestamp_mapper.py) → MM:SS source timestamps
```

---

# Project Structure

```bash
youtube-qa-assistant/
│
├── app/
│   ├── main.py               # Full pipeline + interactive Q&A loop
│   ├── download_video.py     # YouTube audio downloader
│   ├── transcriber.py        # Whisper transcription (saves text + segments.json)
│   ├── chunker.py            # LangChain text splitter
│   ├── embeddings.py         # Sentence Transformer embeddings
│   ├── vector_store.py       # FAISS index build & persist  [US-06]
│   ├── retriever.py          # Query embedding + FAISS search [US-07]
│   ├── qa_engine.py          # LLM answer generation          [US-08]
│   └── timestamp_mapper.py   # Whisper segment timestamp lookup [US-09]
│
├── data/
│   ├── audio/                # Downloaded audio files (gitignored)
│   ├── transcripts/          # transcript.txt + segments.json (gitignored)
│   └── faiss_index/          # FAISS index + chunks.pkl (gitignored)
│
├── .env.example              # Environment variable template
├── requirements.txt
├── README.md
└── .gitignore
```

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone <repository-url>
cd youtube-qa-assistant
```

## 2. Create Virtual Environment

### Mac/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get your **free** Groq API key (no credit card required) at: https://console.groq.com

---

# Run Project

## Full pipeline (download + process + Q&A)
```bash
python app/main.py
```

## Q&A only (skip re-downloading — reuse saved FAISS index)
```bash
python app/main.py --qa-only
```

---

# Team Members

* Anisha Sinha — Project Setup, Whisper Integration, Chunking, Embeddings (US-01 to US-05)
* Archit Agarwal — FAISS Vector Store, Retrieval Pipeline, Q&A Engine, Timestamp Mapping (US-06 to US-09)
* Mayank Chopra — Frontend, Backend APIs, Deployment (US-10 to US-13)

---

# Future Improvements

* Real-time streaming support
* Multi-video indexing
* Better retrieval optimization
* Improved UI/UX
* Cloud deployment

