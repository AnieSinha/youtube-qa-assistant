FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/    ./api/
COPY app/    ./app/
COPY frontend/ ./frontend/
COPY run.py  .

RUN mkdir -p data/audio data/transcripts data/faiss_index \
    && touch data/audio/.gitkeep data/transcripts/.gitkeep data/faiss_index/.gitkeep

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
