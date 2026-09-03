from fastapi import APIRouter
from app.database.supabase import get_supabase

router = APIRouter()


@router.get("")
async def health_check():
    return {"status": "ok"}


@router.get("/db")
async def db_health():
    try:
        client = get_supabase()
        # A lightweight query to verify DB connectivity
        client.table("conversations").select("id").limit(1).execute()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": str(exc)}
