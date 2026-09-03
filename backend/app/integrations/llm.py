from typing import Generator
import google.generativeai as genai
from app.core.config import settings
from app.core.exceptions import AppException

# Configure the Gemini client once at module load
genai.configure(api_key=settings.LLM_API_KEY)


def _build_chat(messages: list[dict]):
    """
    Shared helper: parse messages list into a Gemini (model, chat, last_part) tuple.
    Returns (chat_session, last_user_part).
    """
    history = []
    system_parts = []

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "system":
            system_parts.append(content)
        elif role == "user":
            history.append({"role": "user", "parts": [content]})
        elif role == "assistant":
            history.append({"role": "model", "parts": [content]})

    if not history:
        raise AppException(status_code=400, detail="No messages to send to LLM")

    last = history[-1]
    if last["role"] != "user":
        raise AppException(status_code=400, detail="Last message must be from the user")

    system_instruction = "\n\n".join(system_parts) if system_parts else None
    model = genai.GenerativeModel(
        model_name=settings.LLM_MODEL,
        system_instruction=system_instruction,
    )

    prior_history = history[:-1]
    chat = model.start_chat(history=prior_history)
    return chat, last["parts"][0]


def generate_reply(messages: list[dict]) -> str:
    """
    Call Gemini chat completions and return the full assistant reply text.

    `messages` is a list of dicts with keys 'role' and 'content'.
    Roles must be 'user', 'assistant', or 'system'.
    """
    try:
        chat, last_part = _build_chat(messages)
        response = chat.send_message(last_part)
        return response.text
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=502,
            detail=f"LLM error: {str(exc)}",
        )


def generate_reply_stream(messages: list[dict]) -> Generator[str, None, None]:
    """
    Call Gemini with streaming enabled and yield text chunks as they arrive.

    Raises AppException on failure; each yielded value is a plain string chunk.
    """
    try:
        chat, last_part = _build_chat(messages)
        response = chat.send_message(last_part, stream=True)
        for chunk in response:
            text = chunk.text
            if text:
                yield text
    except AppException:
        raise
    except Exception as exc:
        raise AppException(
            status_code=502,
            detail=f"LLM streaming error: {str(exc)}",
        )
