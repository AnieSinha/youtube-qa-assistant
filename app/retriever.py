import numpy as np
from embeddings import get_model
from vector_store import load_vector_store


def retrieve_chunks(
    query: str,
    index=None,
    chunks: list[str] | None = None,
    top_k: int = 3,
) -> list[dict]:
    """
    Embed the user query and retrieve the most semantically similar
    transcript chunks from the FAISS index.

    Args:
        query:   The user's question string.
        index:   (Optional) A pre-loaded FAISS index. If None, loads from disk.
        chunks:  (Optional) Pre-loaded list of chunk texts. If None, loads from disk.
        top_k:   Number of top results to return (default 3).

    Returns:
        List of dicts, each containing:
            - 'text'     : the chunk text
            - 'score'    : L2 distance (lower = more similar)
            - 'chunk_id' : original index position in the chunk list
    """
    if index is None or chunks is None:
        index, chunks = load_vector_store()

    # Embed the query — reuses the same singleton model from embeddings.py
    query_embedding = get_model().encode([query]).astype(np.float32)

    # Search FAISS index
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            # FAISS returns -1 when there are fewer results than top_k
            continue
        results.append({
            "text": chunks[idx],
            "score": float(dist),
            "chunk_id": int(idx),
        })

    return results
