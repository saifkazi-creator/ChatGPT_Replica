from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import get_current_user
from app.core.exceptions import AppException

_bearer = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """
    FastAPI dependency — validates the Bearer token via Supabase Auth and
    returns the authenticated user's UUID string.
    Raises 401 if the token is missing, invalid, or expired.
    """
    token = credentials.credentials
    user = get_current_user(token)
    return user["user_id"]
