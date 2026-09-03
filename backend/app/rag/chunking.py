def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping character-based chunks.
    No external library required — pure Python.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks: list[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == length:
            break
        start += chunk_size - overlap  # slide forward with overlap

    return chunks
