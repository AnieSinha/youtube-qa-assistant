import os
import pickle
import numpy as np
import faiss

# Paths for persisting the FAISS index and chunk texts
INDEX_DIR = "data/faiss_index"
INDEX_PATH = os.path.join(INDEX_DIR, "index.faiss")
CHUNKS_PATH = os.path.join(INDEX_DIR, "chunks.pkl")


def build_vector_store(chunks: list[str], embeddings: np.ndarray) -> faiss.Index:
    """
    Build a FAISS flat L2 index from embeddings and persist both the
    index and corresponding text chunks to disk.

    Args:
        chunks:     List of text chunk strings (parallel to embeddings rows).
        embeddings: 2-D numpy array of shape (n_chunks, embedding_dim).

    Returns:
        The constructed FAISS index.
    """
    os.makedirs(INDEX_DIR, exist_ok=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)

    # FAISS requires float32
    embeddings_f32 = embeddings.astype(np.float32)
    index.add(embeddings_f32)

    # Persist index
    faiss.write_index(index, INDEX_PATH)

    # Persist chunk texts alongside the index
    with open(CHUNKS_PATH, "wb") as f:
        pickle.dump(chunks, f)

    print(f"Vector store saved — {index.ntotal} vectors indexed.")
    return index


def load_vector_store() -> tuple[faiss.Index, list[str]]:
    """
    Load a previously saved FAISS index and its associated chunks from disk.

    Returns:
        (index, chunks) tuple.

    Raises:
        FileNotFoundError: if the index has not been built yet.
    """
    if not os.path.exists(INDEX_PATH) or not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError(
            "FAISS index not found. Run the full pipeline first to build it."
        )

    index = faiss.read_index(INDEX_PATH)

    with open(CHUNKS_PATH, "rb") as f:
        chunks = pickle.load(f)

    print(f"Vector store loaded — {index.ntotal} vectors, {len(chunks)} chunks.")
    return index, chunks
