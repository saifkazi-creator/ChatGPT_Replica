from tavily import TavilyClient
from app.core.config import settings
from app.core.exceptions import AppException

_client: TavilyClient | None = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        if not settings.WEB_SEARCH_API_KEY:
            raise AppException(
                status_code=500,
                detail="WEB_SEARCH_API_KEY is not configured",
            )
        _client = TavilyClient(api_key=settings.WEB_SEARCH_API_KEY)
    return _client


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web using Tavily and return a list of result dicts
    with keys: title, url, snippet.
    """
    try:
        client = _get_client()
        response = client.search(query=query, max_results=max_results)
        results = []
        for item in response.get("results", []):
            results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                }
            )
        return results
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=502,
            detail=f"Web search error: {str(exc)}",
        )
