from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.audit import log_audit_event
from app.models.user import User
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse)
async def register(req: UserRegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await AuthService.register_user(db, req)
    await log_audit_event(
        db,
        action="USER_REGISTER",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        details={"email": user.email}
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    agent = request.headers.get("user-agent")
    user, tokens = await AuthService.login_user(db, req, ip_address=ip, user_agent=agent)
    await log_audit_event(
        db,
        action="USER_LOGIN",
        user_id=user.id,
        ip_address=ip,
        user_agent=agent
    )
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh_tokens(db, req.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
async def logout(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await log_audit_event(db, action="USER_LOGOUT", user_id=user.id)
    return {"success": True, "message": "Logged out successfully"}
