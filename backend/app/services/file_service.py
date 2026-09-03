from app.database.supabase import get_supabase
from app.rag.pipeline import process_document
from app.core.exceptions import AppException


def upload_file(filename: str, file_bytes: bytes, conversation_id: str) -> dict:
    """Ingest a file through the RAG pipeline and return the document record."""
    document = process_document(
        filename=filename,
        file_bytes=file_bytes,
        conversation_id=conversation_id,
    )
    return document


def list_files(conversation_id: str) -> list[dict]:
    """List all documents uploaded to a conversation."""
    db = get_supabase()
    result = (
        db.table("documents")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []


def delete_file(file_id: str) -> None:
    """Delete a document and its chunks (cascade handled by DB)."""
    db = get_supabase()
    result = db.table("documents").delete().eq("id", file_id).execute()
    if not result.data:
        raise AppException(status_code=404, detail="File not found")
