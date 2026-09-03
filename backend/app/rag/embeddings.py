import google.generativeai as genai
from app.core.config import settings
from app.core.exceptions import AppException

genai.configure(api_key=settings.LLM_API_KEY)


def embed_text(text: str) -> list[float]:
    """
    Call the Gemini embedding API and return the embedding vector.
    Uses output_dimensionality to truncate to EMBEDDING_DIMENSIONS (768).
    """
    try:
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=text,
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=settings.EMBEDDING_DIMENSIONS,
        )
        return result["embedding"]
    except Exception as exc:
        raise AppException(
            status_code=502,
            detail=f"Embedding error: {str(exc)}",
        )


def embed_query(text: str) -> list[float]:
    """
    Embed a query string for retrieval (uses RETRIEVAL_QUERY task type).
    """
    try:
        result = genai.embed_content(
            model=settings.EMBEDDING_MODEL,
            content=text,
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=settings.EMBEDDING_DIMENSIONS,
        )
        return result["embedding"]
    except Exception as exc:
        raise AppException(
            status_code=502,
            detail=f"Embedding error: {str(exc)}",
        )
