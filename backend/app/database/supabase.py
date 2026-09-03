from supabase import create_client, Client
from app.core.config import settings

_client: Client | None = None


def get_supabase() -> Client:
    """Return the shared Supabase client (service role), creating it on first call."""
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in backend/.env"
            )
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    return _client


def get_authed_supabase(access_token: str) -> Client:
    """
    Return a Supabase client with the user's JWT set so that RLS policies
    and auth.uid() resolve correctly within PostgREST.
    Used for operations that need the auth context (e.g. inserting messages
    with a user_id FK to auth.users).
    """
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    client.postgrest.auth(access_token)
    return client
