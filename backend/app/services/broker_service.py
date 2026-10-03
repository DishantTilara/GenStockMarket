import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.config import settings
from app.core.security import encrypt_broker_secret, decrypt_broker_secret
from app.core.audit import log_audit_event
from app.models.broker import BrokerAccount
from app.providers.broker.factory import get_broker_provider

logger = logging.getLogger("broker_service")


class BrokerService:
    """
    Broker Authentication and Lifecycle Service.
    - Encrypts credentials at rest (Fernet AES)
    - Zero plaintext secret leakage in API or logs
    - Manages connection, disconnection, reconnect
    - Queries broker margins, balances, and open positions
    """

    @classmethod
    def mask_secret(cls, secret: Optional[str]) -> str:
        if not secret or len(secret) < 4:
            return "••••••••"
        return f"••••••••{secret[-4:]}"

    @classmethod
    async def get_active_account(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[BrokerAccount]:
        stmt = select(BrokerAccount).where(
            and_(BrokerAccount.user_id == user_id, BrokerAccount.is_active == True)
        ).order_by(BrokerAccount.updated_at.desc())
        res = await db.execute(stmt)
        return res.scalars().first()

    @classmethod
    async def connect_broker(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        broker_name: str,
        environment: str,
        api_key: str,
        api_secret: str,
        client_id: Optional[str] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        env_upper = environment.upper()
        if env_upper not in ["SANDBOX", "LIVE", "PAPER"]:
            raise ValueError(f"Invalid broker environment: {environment}. Must be SANDBOX, LIVE, or PAPER")

        # Deactivate any previous active connection
        existing = await cls.get_active_account(db, user_id)
        if existing:
            existing.is_active = False

        enc_secret = encrypt_broker_secret(api_secret) if api_secret else None
        enc_token = encrypt_broker_secret(access_token) if access_token else None

        now = datetime.now(timezone.utc)
        account = BrokerAccount(
            user_id=user_id,
            broker_name=broker_name.lower(),
            environment=env_upper,
            client_id=client_id or f"CLI-{uuid.uuid4().hex[:6].upper()}",
            api_key=api_key,
            encrypted_secret=enc_secret,
            encrypted_access_token=enc_token,
            is_active=True,
            last_connected_at=now,
            token_expires_at=now + timedelta(hours=24)
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)

        # Connect adapter
        broker_provider = get_broker_provider(env_upper.lower())
        connected = await broker_provider.connect()

        await log_audit_event(
            db=db,
            action="BROKER_CONNECTED",
            user_id=user_id,
            resource_type="broker_account",
            resource_id=str(account.id),
            details={
                "broker": broker_name,
                "environment": env_upper,
                "client_id": account.client_id,
                "connected": connected
            }
        )

        return {
            "id": str(account.id),
            "broker_name": account.broker_name,
            "environment": account.environment,
            "client_id": account.client_id,
            "api_key_masked": cls.mask_secret(account.api_key),
            "is_active": account.is_active,
            "connected": connected,
            "last_connected_at": account.last_connected_at.isoformat() if account.last_connected_at else None,
            "token_expires_at": account.token_expires_at.isoformat() if account.token_expires_at else None
        }

    @classmethod
    async def disconnect_broker(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> bool:
        account = await cls.get_active_account(db, user_id)
        if not account:
            return False

        account.is_active = False
        await db.commit()

        broker_provider = get_broker_provider(account.environment.lower())
        await broker_provider.disconnect()

        await log_audit_event(
            db=db,
            action="BROKER_DISCONNECTED",
            user_id=user_id,
            resource_type="broker_account",
            resource_id=str(account.id),
            details={"broker": account.broker_name, "environment": account.environment}
        )
        return True

    @classmethod
    async def get_broker_status(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        account = await cls.get_active_account(db, user_id)
        broker_provider = get_broker_provider()
        account_info = await broker_provider.get_account()

        if not account:
            return {
                "has_account": False,
                "environment": settings.TRADING_MODE,
                "broker_name": settings.BROKER_PROVIDER,
                "is_connected": account_info.get("is_connected", False),
                "client_id": None,
                "api_key_masked": None,
                "token_expires_at": None
            }

        return {
            "has_account": True,
            "id": str(account.id),
            "broker_name": account.broker_name,
            "environment": account.environment,
            "client_id": account.client_id,
            "api_key_masked": cls.mask_secret(account.api_key),
            "is_active": account.is_active,
            "is_connected": account_info.get("is_connected", False),
            "last_connected_at": account.last_connected_at.isoformat() if account.last_connected_at else None,
            "token_expires_at": account.token_expires_at.isoformat() if account.token_expires_at else None
        }

    @classmethod
    async def get_broker_margins(cls) -> Dict[str, Any]:
        provider = get_broker_provider()
        return await provider.get_margins()

    @classmethod
    async def get_broker_positions(cls) -> List[Dict[str, Any]]:
        provider = get_broker_provider()
        return await provider.get_positions()
