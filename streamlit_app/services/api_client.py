import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000/api")


def _headers() -> dict:
    token = st.session_state.get("access_token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _handle(response: requests.Response) -> dict | list:
    """Raise a clean error on non-2xx; otherwise return JSON."""
    if not response.ok:
        detail = response.json().get("detail", response.text)
        raise RuntimeError(detail)
    return response.json()


# ── Auth ──────────────────────────────────────────────────────────────────────

def signup(email: str, password: str) -> dict:
    return _handle(requests.post(f"{BASE_URL}/auth/signup",
                                 json={"email": email, "password": password}))


def login(email: str, password: str) -> dict:
    return _handle(requests.post(f"{BASE_URL}/auth/login",
                                 json={"email": email, "password": password}))


def logout() -> None:
    requests.post(f"{BASE_URL}/auth/logout", headers=_headers())


def get_me() -> dict:
    return _handle(requests.get(f"{BASE_URL}/auth/me", headers=_headers()))


# ── Conversations ─────────────────────────────────────────────────────────────

def list_conversations() -> list:
    return _handle(requests.get(f"{BASE_URL}/conversations", headers=_headers()))


def create_conversation(title: str = "New Conversation") -> dict:
    return _handle(requests.post(f"{BASE_URL}/conversations",
                                 json={"title": title}, headers=_headers()))


def rename_conversation(conv_id: str, title: str) -> dict:
    return _handle(requests.patch(f"{BASE_URL}/conversations/{conv_id}",
                                  json={"title": title}, headers=_headers()))


def auto_title_conversation(conv_id: str) -> str:
    """Ask the backend to generate + persist a title; return the new title."""
    data = _handle(requests.post(
        f"{BASE_URL}/conversations/{conv_id}/auto-title",
        headers=_headers(),
    ))
    return data.get("title", "New Conversation")


def delete_conversation(conv_id: str) -> None:
    requests.delete(f"{BASE_URL}/conversations/{conv_id}", headers=_headers())


# ── Chat ──────────────────────────────────────────────────────────────────────

def send_chat_message(conversation_id: str, message: str) -> dict:
    return _handle(requests.post(f"{BASE_URL}/chat",
                                 json={"conversation_id": conversation_id,
                                       "message": message},
                                 headers=_headers()))


def send_chat_message_stream(conversation_id: str, message: str) -> requests.Response:
    """Return a streaming Response from POST /chat/stream. Caller iterates chunks."""
    response = requests.post(
        f"{BASE_URL}/chat/stream",
        json={"conversation_id": conversation_id, "message": message},
        headers=_headers(),
        stream=True,
        timeout=120,
    )
    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(detail)
    return response


def get_messages(conversation_id: str) -> list:
    return _handle(requests.get(
        f"{BASE_URL}/conversations/{conversation_id}/messages",
        headers=_headers(),
    ))


# ── Files ─────────────────────────────────────────────────────────────────────

def upload_file(conversation_id: str, file_name: str, file_bytes: bytes) -> dict:
    return _handle(requests.post(
        f"{BASE_URL}/files",
        data={"conversation_id": conversation_id},
        files={"file": (file_name, file_bytes, "application/octet-stream")},
        headers=_headers(),
    ))


def list_files(conversation_id: str) -> list:
    return _handle(requests.get(f"{BASE_URL}/files",
                                params={"conversation_id": conversation_id},
                                headers=_headers()))


def delete_file(file_id: str) -> None:
    requests.delete(f"{BASE_URL}/files/{file_id}", headers=_headers())
