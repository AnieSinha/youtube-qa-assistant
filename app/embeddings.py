import warnings
import numpy as np
from sentence_transformers import SentenceTransformer

# Suppress benign FutureWarning about renamed method
warnings.filterwarnings("ignore", category=FutureWarning, module="sentence_transformers")

model = SentenceTransformer('all-MiniLM-L6-v2')


def create_embeddings(chunks: list[str]) -> np.ndarray:
    """Return a (N, 384) float32 numpy array of sentence embeddings."""
    embeddings = model.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
    return np.array(embeddings, dtype=np.float32)