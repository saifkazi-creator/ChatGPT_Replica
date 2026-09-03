from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service
from app.core.security import get_current_user_id

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def send_message(
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    return chat_service.send_message(
        conversation_id=body.conversation_id,
        user_content=body.message,
        user_id=user_id,
    )


@router.post("/stream")
async def send_message_stream(
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Stream the LLM reply chunk-by-chunk as plain text."""
    generator = chat_service.send_message_stream(
        conversation_id=body.conversation_id,
        user_content=body.message,
        user_id=user_id,
    )
    return StreamingResponse(generator, media_type="text/plain")
