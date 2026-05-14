import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Groq client — uses OpenAI-compatible API (free, no credit card required)
# Get your free API key at: https://console.groq.com
# ---------------------------------------------------------------------------
_client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

# Free models available on Groq (as of May 2026):
#   "llama-3.1-8b-instant"          — fast, lightweight  (replaces llama3-8b-8192)
#   "llama-3.3-70b-versatile"       — more powerful      (replaces llama3-70b-8192)
#   "meta-llama/llama-4-scout-17b-16e-instruct" — large context
MODEL = "llama-3.3-70b-versatile"

_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based on a YouTube video transcript. "
    "Use the provided transcript context to give detailed, accurate answers. "
    "Synthesize information from all provided chunks to form a complete answer. "
    "If the transcript mentions related topics, include them. "
    "If the answer truly cannot be found in the context at all, say so clearly."
)


def answer_question(question: str, retrieved_chunks: list[dict]) -> str:
    """
    Generate an answer to the user's question using the retrieved transcript
    chunks as context, via Groq's free LLM API.

    Args:
        question:         The user's question string.
        retrieved_chunks: List of chunk dicts returned by retriever.retrieve_chunks().
                          Each dict must have a 'text' key.

    Returns:
        The LLM-generated answer as a plain string.
    """
    if not retrieved_chunks:
        return "No relevant transcript content was found to answer your question."

    # Build a single context block from the top chunks
    context_parts = [
        f"[Chunk {i + 1}]:\n{chunk['text']}"
        for i, chunk in enumerate(retrieved_chunks)
    ]
    context = "\n\n".join(context_parts)

    user_message = (
        f"Video transcript context:\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Provide a thorough answer using the transcript context above. "
        "Include specific details, features, or examples mentioned in the video."
    )

    response = _client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()
