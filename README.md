# YouTube Video Q&A Assistant

## Project Overview

The YouTube Video Q&A Assistant is an AI-powered application that allows users to provide a YouTube video URL and ask questions about the video content.

The system extracts audio from the video, generates transcripts using Whisper, converts transcript chunks into embeddings, and enables semantic retrieval for accurate question answering.

---

# Features

* YouTube video URL input
* Audio extraction
* Speech-to-text transcription using Whisper
* Transcript chunking
* Embedding generation
* Vector database integration using FAISS
* Retrieval-based question answering
* Timestamp-based answers

---

# Technologies Used

* Python
* Whisper
* LangChain
* Sentence Transformers
* FAISS
* FastAPI
* yt-dlp

---

# Project Workflow

YouTube URL
↓
Audio Download
↓
Whisper Transcription
↓
Transcript Chunking
↓
Embedding Generation
↓
FAISS Vector Storage
↓
Retrieval Pipeline
↓
LLM Question Answering
↓
Timestamp-Based Response

---

# Project Structure

```bash
youtube-qa-assistant/
│
├── app/
│   ├── main.py
│   ├── download_video.py
│   ├── transcriber.py
│   ├── chunker.py
│   ├── embeddings.py
│
├── data/
│   ├── audio/
│   ├── transcripts/
│
├── requirements.txt
├── README.md
├── .gitignore
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

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run Project

```bash
python3 app/main.py
```

---

# Team Members

* Anisha Sinha — Project Setup, Whisper Integration, Chunking, Embeddings
* Archit Agrawal — FAISS, Retrieval Pipeline, Q&A
* Mayank Chopra — Frontend, Backend APIs, Deployment

---

# Future Improvements

* Real-time streaming support
* Multi-video indexing
* Better retrieval optimization
* Improved UI/UX
* Cloud deployment
