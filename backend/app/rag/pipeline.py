import io
from pypdf import PdfReader
from app.database.supabase import get_supabase
from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_text
from app.core.exceptions import AppException


def _extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract plain text from a .txt or .pdf file."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    elif lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise AppException(
            status_code=400,
            detail=f"Unsupported file type: {filename}. Only .txt and .pdf are accepted.",
        )


def process_document(
    filename: str,
    file_bytes: bytes,
    conversation_id: str,
) -> dict:
    """
    Full RAG ingestion pipeline:
    1. Extract text from file
    2. Chunk the text
    3. Embed each chunk
    4. Insert a row into `documents` and rows into `document_chunks`
    Returns the inserted document record.
    """
    db = get_supabase()

    # 1. Extract text
    text = _extract_text(filename, file_bytes)
    if not text.strip():
        raise AppException(status_code=400, detail="File appears to be empty or unreadable")

    # 2. Insert document record first (we need the document id for chunks)
    doc_result = (
        db.table("documents")
        .insert({"conversation_id": conversation_id, "filename": filename})
        .execute()
    )
    if not doc_result.data:
        raise AppException(status_code=500, detail="Failed to create document record")
    document = doc_result.data[0]
    document_id = document["id"]

    # 3. Chunk the text
    chunks = chunk_text(text)
    if not chunks:
        raise AppException(status_code=400, detail="No text chunks could be extracted")

    # 4. Embed each chunk and collect rows for bulk insert
    chunk_rows = []
    for chunk in chunks:
        vector = embed_text(chunk)
        chunk_rows.append(
            {
                "document_id": document_id,
                "content": chunk,
                "embedding": vector,
            }
        )

    # 5. Bulk insert chunks
    db.table("document_chunks").insert(chunk_rows).execute()

    return document
