"""
integrations/memory.py
─────────────────────
Long-term memory powered by the mem0 cloud API (MemoryClient).

Functions
---------
search_memories(user_id, query, top_k) → list[str]
    Semantic retrieval of the most relevant memories for a query.

add_memories(user_id, messages) → None
    Auto-extract and store memories from a user+assistant exchange.

add_explicit_fact(user_id, fact) → None
    Directly store a single fact string (used by the "remember that" trigger).

All functions no-op gracefully when MEM0_API_KEY is not configured.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_client():
    """
    Lazily initialise and cache the MemoryClient.
    Returns None if MEM0_API_KEY is not set so callers can short-circuit.
    """
    if not settings.MEM0_API_KEY:
        logger.warning(
            "MEM0_API_KEY is not set — long-term memory is disabled. "
            "Add MEM0_API_KEY to backend/.env to enable it."
        )
        return None
    try:
        from mem0 import MemoryClient  # type: ignore
        return MemoryClient(api_key=settings.MEM0_API_KEY)
    except Exception as exc:
        logger.error("Failed to initialise mem0 MemoryClient: %s", exc)
        return None


def search_memories(user_id: str, query: str, top_k: int = 5) -> list[str]:
    """
    Return the top_k memories most semantically relevant to *query* for this user.
    Returns an empty list when mem0 is disabled or on error.

    Handles multiple mem0 response shapes across library versions:
    - list of plain strings  (current MemoryClient)
    - list of dicts with a 'memory' / 'text' / 'content' key
    - wrapper dict  {\"results\": [...]}
    """
    client = _get_client()
    if client is None:
        return []
    try:
        raw = client.search(query, filters={"user_id": user_id}, limit=top_k)

        # Unwrap {"results": [...]} envelope if present
        if isinstance(raw, dict):
            items = raw.get("results", [])
        else:
            items = raw or []

        memories: list[str] = []
        for item in items:
            if isinstance(item, str):
                if item:
                    memories.append(item)
            elif isinstance(item, dict):
                text = (
                    item.get("memory")
                    or item.get("text")
                    or item.get("content")
                    or ""
                )
                if text:
                    memories.append(str(text))
        return memories
    except Exception as exc:
        logger.warning("mem0 search_memories failed: %s", exc)
        return []


def add_memories(user_id: str, messages: list[dict]) -> None:
    """
    Pass a list of {role, content} dicts to mem0 so it can automatically
    extract and store relevant facts from the exchange.
    Silently no-ops on error so it never blocks a chat response.
    """
    client = _get_client()
    if client is None or not messages:
        return
    try:
        filtered = [
            {"role": m["role"], "content": m["content"]}
            for m in messages
            if m.get("role") in ("user", "assistant") and m.get("content")
        ]
        if filtered:
            client.add(filtered, user_id=user_id)
    except Exception as exc:
        logger.warning("mem0 add_memories failed: %s", exc)


def add_explicit_fact(user_id: str, fact: str) -> None:
    """
    Directly add a single fact string to mem0.
    Used by the 'remember that …' explicit trigger.
    """
    fact = fact.strip()
    if not fact:
        return
    client = _get_client()
    if client is None:
        return
    try:
        client.add(fact, user_id=user_id)
    except Exception as exc:
        logger.warning("mem0 add_explicit_fact failed: %s", exc)
