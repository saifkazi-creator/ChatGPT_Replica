from app.database.supabase import get_supabase
from app.core.exceptions import AppException


def signup(email: str, password: str) -> dict:
    """Create a new user in Supabase Auth. Returns user_id, email, access_token."""
    client = get_supabase()
    try:
        response = client.auth.sign_up({"email": email, "password": password})
    except Exception as exc:
        raise AppException(status_code=400, detail=str(exc))

    if not response.user:
        raise AppException(status_code=400, detail="Sign-up failed — check email/password")

    session = response.session
    access_token = session.access_token if session else ""

    return {
        "user_id": str(response.user.id),
        "email": response.user.email,
        "access_token": access_token,
    }


def login(email: str, password: str) -> dict:
    """Sign in with email + password. Returns user_id, email, access_token."""
    client = get_supabase()
    try:
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except Exception as exc:
        raise AppException(status_code=401, detail=str(exc))

    if not response.user or not response.session:
        raise AppException(status_code=401, detail="Invalid credentials")

    return {
        "user_id": str(response.user.id),
        "email": response.user.email,
        "access_token": response.session.access_token,
    }


def logout(access_token: str) -> None:
    """Invalidate a Supabase session."""
    client = get_supabase()
    try:
        client.auth.sign_out()
    except Exception as exc:
        raise AppException(status_code=400, detail=str(exc))


def get_current_user(access_token: str) -> dict:
    """Verify a token and return the user's id and email."""
    client = get_supabase()
    try:
        response = client.auth.get_user(access_token)
    except Exception as exc:
        raise AppException(status_code=401, detail="Invalid or expired token")

    if not response.user:
        raise AppException(status_code=401, detail="Invalid or expired token")

    return {
        "user_id": str(response.user.id),
        "email": response.user.email,
    }
