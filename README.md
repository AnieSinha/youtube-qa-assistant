# TubeAI — YouTube AI Assistant

## Project Overview

TubeAI is an AI-powered application that allows users to provide a YouTube video URL and ask questions about the video content in real-time.

The system extracts audio from the video, generates transcripts using Groq's Whisper API (`whisper-large-v3-turbo`), converts transcript chunks into embeddings, stores them in a FAISS vector database, and enables semantic retrieval for accurate question answering with clickable source timestamps.

---

## Features

* 🎬 YouTube video URL input with embedded player
* 🎧 Audio extraction via yt-dlp
* 🎙️ Cloud-based transcription using Groq Whisper API (~7s processing)
* 📝 Smart transcript chunking (1000 chars, 200 overlap)
* 🧠 Embedding generation via Sentence Transformers (`all-MiniLM-L6-v2`)
* 💾 Vector database integration using FAISS
* 💬 Real-time streaming answers via SSE (Server-Sent Events)
* ⏱️ Clickable timestamp navigation (seeks to the relevant video moment)
* 🌗 Dark/Light theme toggle with persistence
* 📐 Resizable chat panel with drag-to-resize
* ⚛️ Modern React.js frontend (Vite build)

---

## Technologies Used

* **Backend**: Python, FastAPI, Uvicorn
* **Transcription**: Groq Whisper API (`whisper-large-v3-turbo`)
* **LLM**: Groq (`llama-3.3-70b-versatile`)
* **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`)
* **Vector Store**: FAISS (CPU)
* **Audio Download**: yt-dlp, imageio-ffmpeg
* **Frontend**: React.js, Vite, marked.js
* **Fonts**: Plus Jakarta Sans, JetBrains Mono

---

## Project Workflow

```
YouTube URL
    ↓
Audio Download          (download_video.py)
    ↓
Groq Whisper API        (transcriber.py)     → transcript.txt + segments.json
    ↓
Transcript Chunking     (chunker.py)
    ↓
Embedding Generation    (embeddings.py)
    ↓
FAISS Vector Storage    (vector_store.py)    → data/faiss_index/
    ↓
Retrieval Pipeline      (retriever.py)       → top-5 relevant chunks
    ↓
LLM Streaming Answer    (qa_engine.py)       → Groq llama-3.3-70b
    ↓
Timestamp Mapping       (timestamp_mapper.py) → MM:SS clickable timestamps
```

---

## Project Structure

```bash
TubeAI/
│
├── api/
│   └── main.py               # FastAPI backend (REST + SSE streaming)
│
├── app/
│   ├── main.py               # Full pipeline + interactive CLI Q&A
│   ├── download_video.py     # YouTube audio downloader
│   ├── transcriber.py        # Groq Whisper cloud transcription
│   ├── chunker.py            # LangChain text splitter
│   ├── embeddings.py         # Sentence Transformer embeddings
│   ├── vector_store.py       # FAISS index build & persist
│   ├── retriever.py          # Query embedding + FAISS search
│   ├── qa_engine.py          # LLM answer generation (streaming)
│   └── timestamp_mapper.py   # Whisper segment timestamp lookup
│
├── client/                   # React.js frontend (Vite)
│   ├── src/
│   │   ├── App.jsx           # Root component (state management)
│   │   ├── components/
│   │   │   ├── TopNav.jsx        # Navigation bar + URL input + theme toggle
│   │   │   ├── VideoSection.jsx  # YouTube player + empty state
│   │   │   ├── ChatSection.jsx   # Chat UI + streaming + timestamps
│   │   │   ├── ProcessingBar.jsx # Non-blocking progress indicator
│   │   │   └── ResizeHandle.jsx  # Draggable panel resizer
│   │   └── index.css         # Design tokens (dark + light themes)
│   ├── vite.config.js        # Vite config (proxy + build output)
│   └── package.json
│
├── frontend/                 # Production build output (served by FastAPI)
│
├── data/
│   ├── audio/                # Downloaded audio files (gitignored)
│   ├── transcripts/          # transcript.txt + segments.json (gitignored)
│   └── faiss_index/          # FAISS index + chunks.pkl (gitignored)
│
├── .env                      # Environment variables (GROQ_API_KEY)
├── run.py                    # Startup script
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository-url>
cd TubeAI
```

### 2. Create Virtual Environment

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies (optional — for development)

```bash
cd client
npm install
cd ..
```

> **Note:** The production-built frontend is already in `frontend/`. You only need this step if you want to modify the React code.

### 5. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get your **free** Groq API key (no credit card required) at: https://console.groq.com

---

## Run Project

### Start the server (production)

```bash
venv\Scripts\python run.py
```

This starts both the API and serves the React frontend at **http://localhost:8000**.

### Start with a custom port

```bash
venv\Scripts\python run.py --port 9000
```

### Frontend development mode (hot-reload)

In one terminal, start the API:
```bash
venv\Scripts\python run.py
```

In another terminal, start the Vite dev server:
```bash
cd client
npm run dev
```

The React dev server runs at **http://localhost:3000** and proxies API calls to `:8000`.

### Rebuild frontend for production

```bash
cd client
npm run build
```

This outputs the built files to `frontend/`, which FastAPI serves automatically.

### CLI mode (no frontend)

```bash
python app/main.py             # Full pipeline + Q&A
python app/main.py --qa-only   # Reuse saved FAISS index
```

---

## Team Members

* Anisha Sinha — Project Setup, Whisper Integration, Chunking, Embeddings (US-01 to US-05)
* Archit Agarwal — FAISS Vector Store, Retrieval Pipeline, Q&A Engine, Timestamp Mapping (US-06 to US-09)
* Mayank Chopra — Frontend, Backend APIs, Deployment (US-10 to US-13)

---

## Future Improvements

* Multi-video indexing
* User authentication & rate-limiting
* Cloud deployment (Docker + CI/CD)
* Mobile-optimized responsive layout
