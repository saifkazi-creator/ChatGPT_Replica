from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import SignUpRequest, LoginRequest, AuthResponse
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter()
_bearer = HTTPBearer()


@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignUpRequest):
    return auth_service.signup(email=body.email, password=body.password)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    return auth_service.login(email=body.email, password=body.password)


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    auth_service.logout(access_token=credentials.credentials)
    return {"detail": "logged out"}


@router.get("/me", response_model=UserResponse)
async def me(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    return auth_service.get_current_user(access_token=credentials.credentials)
