from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List
from app.schemas.file import FileResponse, FileUploadResponse
from app.core.security import get_current_user_id
from app.services import file_service

router = APIRouter()


@router.post("", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
    user_id: str = Depends(get_current_user_id),
):
    file_bytes = await file.read()
    document = file_service.upload_file(
        filename=file.filename,
        file_bytes=file_bytes,
        conversation_id=conversation_id,
    )
    return {"message": "File uploaded and processed", "file": document}


@router.get("", response_model=List[FileResponse])
async def list_files(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    return file_service.list_files(conversation_id=conversation_id)


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    user_id: str = Depends(get_current_user_id),
):
    file_service.delete_file(file_id=file_id)
    return {"detail": "deleted"}
