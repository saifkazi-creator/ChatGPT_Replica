from typing import Optional
from app.database.supabase import get_supabase
from app.core.exceptions import AppException


def create_conversation(user_id: str, title: str = "New Conversation") -> dict:
    client = get_supabase()
    result = (
        client.table("conversations")
        .insert({"user_id": user_id, "title": title})
        .execute()
    )
    if not result.data:
        raise AppException(status_code=500, detail="Failed to create conversation")
    return result.data[0]


def list_conversations(user_id: str) -> list[dict]:
    client = get_supabase()
    result = (
        client.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data or []


def get_conversation(conversation_id: str, user_id: str) -> dict:
    client = get_supabase()
    result = (
        client.table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        raise AppException(status_code=404, detail="Conversation not found")
    return result.data


def update_conversation(conversation_id: str, user_id: str, title: str) -> dict:
    from datetime import datetime, timezone
    client = get_supabase()
    result = (
        client.table("conversations")
        .update({"title": title, "updated_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise AppException(status_code=404, detail="Conversation not found")
    return result.data[0]


def delete_conversation(conversation_id: str, user_id: str) -> None:
    client = get_supabase()
    client.table("conversations").delete().eq("id", conversation_id).eq(
        "user_id", user_id
    ).execute()


def create_message(conversation_id: str, role: str, content: str) -> dict:
    client = get_supabase()
    result = (
        client.table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
            }
        )
        .execute()
    )
    if not result.data:
        raise AppException(status_code=500, detail="Failed to save message")
    return result.data[0]


def list_messages(conversation_id: str) -> list[dict]:
    client = get_supabase()
    result = (
        client.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []
