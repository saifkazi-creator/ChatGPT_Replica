from pydantic import BaseModel
from datetime import datetime


class FileResponse(BaseModel):
    id: str
    conversation_id: str
    filename: str
    created_at: datetime


class FileUploadResponse(BaseModel):
    message: str
    file: FileResponse
