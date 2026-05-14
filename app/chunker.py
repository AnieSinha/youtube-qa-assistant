from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text):
    """
    Split transcript text into overlapping chunks for embedding.

    Uses larger chunks (1000 chars) with generous overlap (200 chars) so each
    chunk carries enough context for the LLM to produce high-quality answers.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    chunks = splitter.split_text(text)

    return chunks