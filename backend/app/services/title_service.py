"""
services/title_service.py
─────────────────────────
Generates a short, descriptive title for a conversation using the LLM,
then persists it via conversation_service.
"""

from app.services.conversation_service import list_messages, update_conversation
from app.integrations.llm import generate_reply
from app.core.exceptions import AppException
import logging

logger = logging.getLogger(__name__)

_TITLE_SYSTEM = (
    "You are a conversation title generator. "
    "Your ONLY job is to output a SHORT title (3–6 words) for a conversation. "
    "Rules:\n"
    "- Output ONLY the title. No explanation, no punctuation at the end, no quotes.\n"
    "- Use the EXACT words from the conversation topic — do not paraphrase or invent words.\n"
    "- Keep it factual and specific (e.g. 'Ronaldo Total Career Goals', 'Python List Sorting Help').\n"
    "- If you cannot determine the topic, output: General Chat"
)

_TITLE_USER_TEMPLATE = (
    "Generate a title for this conversation:\n\n{convo_text}\n\n"
    "Title (3-6 words only, no punctuation):"
)


def generate_title(conversation_id: str, user_id: str) -> str:
    """
    Fetch the first few messages of *conversation_id*, ask the LLM to produce
    a short title, persist it, and return the new title string.

    Falls back to "New Conversation" if anything goes wrong so it is always
    safe to call from a fire-and-forget context.
    """
    try:
        messages = list_messages(conversation_id)
        if not messages:
            return "New Conversation"

        # Use the first 6 messages (3 turns) for context — enough to capture topic
        sample = messages[:6]
        convo_text = "\n".join(
            f"{m['role'].capitalize()}: {m['content'][:300]}"
            for m in sample
            if m["role"] in ("user", "assistant")
        )

        llm_messages = [
            {"role": "system", "content": _TITLE_SYSTEM},
            {"role": "user", "content": _TITLE_USER_TEMPLATE.format(convo_text=convo_text)},
        ]

        raw_title = generate_reply(llm_messages).strip()

        # Strip surrounding quotes or punctuation the model might add
        title = raw_title.strip('"\' ').strip('.,!?').strip()

        # Sanity check: if output looks like a full sentence (too many words),
        # fall back to a plain summary built from the first user message
        words = title.split()
        if len(words) > 10 or not title:
            first_user = next(
                (m["content"] for m in sample if m["role"] == "user"), ""
            )
            title = " ".join(first_user.split()[:6]).strip('.,!?') or "New Conversation"

        # Cap at 60 chars so it fits the sidebar
        title = title[:60]

        # Persist
        update_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            title=title,
        )
        return title

    except AppException:
        raise
    except Exception as exc:
        logger.warning("generate_title failed for %s: %s", conversation_id, exc)
        return "New Conversation"
