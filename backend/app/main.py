from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#This code is so cooooooool!!!!!!!!!!!!!!!!!!!!
from app.core.exceptions import AppException, app_exception_handler
from app.api import health, auth, conversations, chat, files

app = FastAPI(title="chatgpt-replica", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)

app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
