from app.database.supabase import get_supabase
from app.rag.embeddings import embed_query
from app.core.exceptions import AppException


def retrieve_relevant_chunks(
    conversation_id: str,
    query: str,
    top_k: int = 5,
) -> list[str]:
    """
    Embed the query, call the pgvector similarity search function,
    and return the top-k chunk texts scoped to the conversation.
    Returns an empty list if no documents exist for this conversation.
    """
    db = get_supabase()

    # Check if any documents exist for this conversation first
    docs = (
        db.table("documents")
        .select("id")
        .eq("conversation_id", conversation_id)
        .limit(1)
        .execute()
    )
    if not docs.data:
        return []

    # Embed the query
    query_vector = embed_query(query)

    # Call the match_document_chunks RPC function
    try:
        result = db.rpc(
            "match_document_chunks",
            {
                "query_embedding": query_vector,
                "conversation_id_filter": conversation_id,
                "match_count": top_k,
            },
        ).execute()
    except Exception as exc:
        raise AppException(status_code=502, detail=f"Retrieval error: {str(exc)}")

    if not result.data:
        return []

    return [row["content"] for row in result.data]
