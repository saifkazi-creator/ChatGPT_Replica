from fastapi import APIRouter, Depends
from typing import List
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
)
from app.schemas.chat import MessageResponse
from app.services import conversation_service
from app.services import title_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    body: ConversationCreate,
    user_id: str = Depends(get_current_user_id),
):
    return conversation_service.create_conversation(
        user_id=user_id,
        title=body.title or "New Conversation",
    )


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: str = Depends(get_current_user_id),
):
    return conversation_service.list_conversations(user_id=user_id)


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    # Verify ownership first
    conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    return conversation_service.list_messages(conversation_id=conversation_id)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    return conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    user_id: str = Depends(get_current_user_id),
):
    return conversation_service.update_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        title=body.title,
    )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    conversation_service.delete_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    return {"detail": "deleted"}


@router.post("/{conversation_id}/auto-title")
async def auto_title_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Generate and persist a short LLM-produced title for the conversation."""
    # Verify ownership first
    conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    new_title = title_service.generate_title(
        conversation_id=conversation_id,
        user_id=user_id,
    )
    return {"title": new_title}
