import uuid
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.user import User
from app.services.broker_service import BrokerService
from app.api.deps import get_current_user

router = APIRouter(prefix="/broker", tags=["Broker Integration & Gateway"])


class BrokerConnectRequest(BaseModel):
    broker_name: str = Field("sandbox", description="zerodha, upstox, angelone, sandbox, paper")
    environment: str = Field("SANDBOX", description="SANDBOX, LIVE, PAPER")
    api_key: str = Field(..., min_length=4)
    api_secret: str = Field(..., min_length=4)
    client_id: Optional[str] = None
    access_token: Optional[str] = None


@router.get("/status")
async def get_broker_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve active broker gateway status, environment, and masked credentials."""
    return await BrokerService.get_broker_status(db, user.id)


@router.post("/connect", status_code=status.HTTP_201_CREATED)
async def connect_broker(
    req: BrokerConnectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Securely connect broker credentials. API secrets are encrypted at rest with AES-GCM."""
    try:
        return await BrokerService.connect_broker(
            db=db,
            user_id=user.id,
            broker_name=req.broker_name,
            environment=req.environment,
            api_key=req.api_key,
            api_secret=req.api_secret,
            client_id=req.client_id,
            access_token=req.access_token
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/disconnect")
async def disconnect_broker(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect active broker session and revoke authorization."""
    disconnected = await BrokerService.disconnect_broker(db, user.id)
    return {"status": "DISCONNECTED" if disconnected else "NO_ACTIVE_CONNECTION"}


@router.get("/margins")
async def get_broker_margins(
    user: User = Depends(get_current_user)
):
    """Query live margins directly from the connected broker gateway."""
    return await BrokerService.get_broker_margins()


@router.get("/positions")
async def get_broker_positions(
    user: User = Depends(get_current_user)
):
    """Query positions directly from the connected broker gateway."""
    return await BrokerService.get_broker_positions()


@router.post("/reconcile")
async def trigger_reconciliation(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger on-demand reconciliation between broker state and PostgreSQL internal orders/positions."""
    from app.services.broker_reconciliation_service import BrokerReconciliationService
    return await BrokerReconciliationService.reconcile_account(db, user.id, auto_correct=True)


@router.get("/reconcile/events")
async def get_reconciliation_events(
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List recent reconciliation discrepancy events and resolutions."""
    from app.services.broker_reconciliation_service import BrokerReconciliationService
    return await BrokerReconciliationService.get_reconciliation_events(db, user.id, limit=limit)

