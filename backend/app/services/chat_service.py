from app.services.conversation_service import create_message, list_messages
from app.integrations.llm import generate_reply, generate_reply_stream
from app.integrations.web_search import search_web
from app.integrations.memory import search_memories, add_memories, add_explicit_fact
from app.rag.retrieval import retrieve_relevant_chunks
from app.core.exceptions import AppException
from typing import Generator

# Keywords that suggest the user needs current/live information
_SEARCH_TRIGGERS = {
    "latest", "current", "today", "recent", "now", "news",
    "who is", "what is happening", "right now", "this week",
    "this month", "this year", "2024", "2025", "2026",
    "price of", "stock", "weather", "score", "update",
}

# Prefixes that explicitly ask to save a memory fact
_MEMORY_PREFIXES = ("remember that ", "remember: ")


def _should_search(message: str) -> bool:
    """Simple keyword heuristic — return True if message likely needs live data."""
    lower = message.lower()
    return any(trigger in lower for trigger in _SEARCH_TRIGGERS)


def _extract_fact(message: str) -> str | None:
    """
    If the message starts with a memory-save prefix, return the fact text.
    Otherwise return None.
    """
    lower = message.lower()
    for prefix in _MEMORY_PREFIXES:
        if lower.startswith(prefix):
            return message[len(prefix):].strip()
    return None


def _build_llm_messages(
    conversation_id: str,
    user_content: str,
    user_id: str,
) -> list[dict]:
    """
    Build the full augmented message list (mem0 memories + RAG + web search)
    that gets passed to the LLM for a given user turn.

    Order of system blocks (all prepended, last-prepended appears first):
        1. Web search results (most ephemeral)
        2. RAG document context
        3. mem0 long-term memories (most stable)
    """
    # Conversation history (already saved to DB at this point)
    history = list_messages(conversation_id)
    llm_messages = [{"role": m["role"], "content": m["content"]} for m in history]

    # ── 1. mem0 semantic memory retrieval ─────────────────────────────────────
    memories = search_memories(user_id=user_id, query=user_content)
    if memories:
        mem_text = "\n".join(f"- {m}" for m in memories)
        llm_messages.insert(
            0,
            {
                "role": "system",
                "content": (
                    "The following are relevant long-term memories about this user "
                    "retrieved from past conversations. Use them to personalise your "
                    "responses where appropriate.\n\n"
                    f"USER MEMORIES:\n{mem_text}"
                ),
            },
        )

    # ── 2. RAG document context ────────────────────────────────────────────────
    chunks = retrieve_relevant_chunks(
        conversation_id=conversation_id,
        query=user_content,
    )
    if chunks:
        context_text = "\n\n---\n\n".join(chunks)
        llm_messages.insert(
            0,
            {
                "role": "system",
                "content": (
                    "Use the following document context to help answer the user's "
                    "question. If the context is not relevant, answer from your own "
                    "knowledge.\n\n"
                    f"DOCUMENT CONTEXT:\n{context_text}"
                ),
            },
        )

    # ── 3. Web search ──────────────────────────────────────────────────────────
    if _should_search(user_content):
        try:
            results = search_web(query=user_content)
            if results:
                snippets = "\n\n".join(
                    f"[{r['title']}]({r['url']})\n{r['snippet']}"
                    for r in results
                )
                llm_messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": (
                            "IMPORTANT: The following are LIVE web search results fetched right now. "
                            "They are your PRIMARY and most authoritative source for this question. "
                            "You MUST:\n"
                            "- Report the EXACT numbers, names, and facts stated in these results.\n"
                            "- NOT round, estimate, or use your training data when the answer is present in the results.\n"
                            "- Cite the source URL when giving specific statistics.\n"
                            "- If results disagree, use the most recent or highest figure and note the discrepancy.\n\n"
                            f"WEB SEARCH RESULTS:\n{snippets}"
                        ),
                    },
                )
        except AppException:
            pass  # Search failure is non-fatal

    return llm_messages


def send_message(conversation_id: str, user_content: str, user_id: str) -> dict:
    """
    Full pipeline (non-streaming):
    1. Save user message to DB.
    2. Handle 'remember that' trigger → explicit mem0 fact + short reply.
    3. Build augmented message list (mem0 memories + RAG + web search).
    4. Call LLM and save assistant reply.
    5. Feed the exchange to mem0 for automatic memory extraction.
    """
    # 1. Save user message
    user_msg = create_message(
        conversation_id=conversation_id,
        role="user",
        content=user_content,
    )

    # 2. Explicit memory-save shortcut
    fact_to_save = _extract_fact(user_content)
    if fact_to_save:
        add_explicit_fact(user_id=user_id, fact=fact_to_save)
        reply_text = f"Got it! I'll remember that: \"{fact_to_save}\""
        assistant_msg = create_message(
            conversation_id=conversation_id,
            role="assistant",
            content=reply_text,
        )
        return {"user_message": user_msg, "assistant_message": assistant_msg}

    # 3. Build augmented context
    llm_messages = _build_llm_messages(conversation_id, user_content, user_id)

    # 4. Call LLM
    reply_text = generate_reply(llm_messages)
    assistant_msg = create_message(
        conversation_id=conversation_id,
        role="assistant",
        content=reply_text,
    )

    # 5. Feed exchange to mem0 for automatic memory extraction (non-blocking)
    add_memories(
        user_id=user_id,
        messages=[
            {"role": "user", "content": user_content},
            {"role": "assistant", "content": reply_text},
        ],
    )

    return {"user_message": user_msg, "assistant_message": assistant_msg}


def send_message_stream(
    conversation_id: str,
    user_content: str,
    user_id: str,
) -> Generator[str, None, None]:
    """
    Streaming variant of send_message.

    1. Saves the user message to the DB.
    2. Handles 'remember that' trigger (yields single chunk, no LLM call).
    3. Builds the augmented message list (mem0 memories + RAG + web search).
    4. Yields LLM text chunks as they arrive.
    5. After stream exhausted: saves full reply to DB + feeds exchange to mem0.
    """
    # 1. Save user message
    create_message(
        conversation_id=conversation_id,
        role="user",
        content=user_content,
    )

    # 2. Explicit memory-save shortcut
    fact_to_save = _extract_fact(user_content)
    if fact_to_save:
        add_explicit_fact(user_id=user_id, fact=fact_to_save)
        reply_text = f"Got it! I'll remember that: \"{fact_to_save}\""
        create_message(
            conversation_id=conversation_id,
            role="assistant",
            content=reply_text,
        )
        yield reply_text
        return

    # 3. Build augmented context
    llm_messages = _build_llm_messages(conversation_id, user_content, user_id)

    # 4. Stream and accumulate
    full_reply: list[str] = []
    for chunk in generate_reply_stream(llm_messages):
        full_reply.append(chunk)
        yield chunk

    # 5. Persist full reply + feed exchange to mem0
    assembled = "".join(full_reply)
    if assembled:
        create_message(
            conversation_id=conversation_id,
            role="assistant",
            content=assembled,
        )
        add_memories(
            user_id=user_id,
            messages=[
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assembled},
            ],
        )


