import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.errors import AppError, UnauthorizedError
from app.models.user import User, UserSession
from app.models.wallet import Wallet
from app.models.scanner import Watchlist, WatchlistItem
from app.models.portfolio import Portfolio
from app.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse


class AuthService:
    @staticmethod
    async def register_user(db: AsyncSession, req: UserRegisterRequest) -> User:
        # Check existing user
        result = await db.execute(select(User).where(User.email == req.email.lower()))
        if result.scalar_one_or_none():
            raise AppError(code="EMAIL_EXISTS", message="An account with this email already exists")

        # Create user
        new_user = User(
            email=req.email.lower(),
            hashed_password=get_password_hash(req.password),
            full_name=req.full_name,
            role="trader",
            is_active=True,
            is_verified=True,
        )
        db.add(new_user)
        await db.flush()

        # Initialize default user wallet with starting demo trading balance
        wallet = Wallet(
            user_id=new_user.id,
            available_balance=100000.00,  # 1 Lakh INR starting demo balance
            locked_balance=0.00,
            currency="INR"
        )
        db.add(wallet)

        # Initialize default user portfolio
        portfolio = Portfolio(
            user_id=new_user.id,
            name="Main Portfolio",
            initial_cash=1000000.00
        )
        db.add(portfolio)

        # Initialize default Watchlist
        watchlist = Watchlist(
            user_id=new_user.id,
            name="Nifty Bluechips",
            description="Top Indian market leaders"
        )
        db.add(watchlist)
        await db.flush()

        # Seed initial items in watchlist
        for sym in ["RELIANCE", "TCS", "HDFCBANK", "INFY", "TATAMOTORS"]:
            item = WatchlistItem(watchlist_id=watchlist.id, symbol=sym)
            db.add(item)

        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def login_user(db: AsyncSession, req: UserLoginRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Tuple[User, TokenResponse]:
        result = await db.execute(select(User).where(User.email == req.email.lower()))
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.hashed_password):
            raise UnauthorizedError(message="Invalid email or password")

        if not user.is_active:
            raise AppError(code="USER_INACTIVE", message="User account is deactivated")

        # Generate tokens
        access_token = create_access_token(subject=user.id, claims={"role": user.role, "email": user.email})
        refresh_token = create_refresh_token(subject=user.id)

        # Persist session
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=get_password_hash(refresh_token[:16]),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=False
        )
        db.add(session)
        await db.commit()

        token_resp = TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600
        )
        return user, token_resp

    @staticmethod
    async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedError(message="Invalid token type")

        user_id = uuid.UUID(payload.get("sub"))
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError(message="User not found or inactive")

        # Issue rotated tokens
        new_access = create_access_token(subject=user.id, claims={"role": user.role, "email": user.email})
        new_refresh = create_refresh_token(subject=user.id)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=3600
        )
