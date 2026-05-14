import warnings
import numpy as np
from sentence_transformers import SentenceTransformer

# Suppress benign FutureWarning about renamed method
warnings.filterwarnings("ignore", category=FutureWarning, module="sentence_transformers")

# ---------------------------------------------------------------------------
# Lazy-loaded singleton — the model is only downloaded/loaded the first time
# get_model() is called, NOT at import time.  This lets the server start
# instantly and avoids duplicate downloads.
# ---------------------------------------------------------------------------
_model = None


def get_model() -> SentenceTransformer:
    """Return the shared SentenceTransformer model (lazy-loaded singleton)."""
    global _model
    if _model is None:
        print("[embeddings] Loading SentenceTransformer model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[embeddings] Model loaded.")
    return _model


def warm_up():
    """Pre-load the embedding model so the first request isn't slow."""
    get_model()


def create_embeddings(chunks: list[str]) -> np.ndarray:
    """Return a (N, 384) float32 numpy array of sentence embeddings."""
    embeddings = get_model().encode(chunks, convert_to_numpy=True, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)