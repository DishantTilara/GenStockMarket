import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.user import User
from app.models.risk import RiskSettings, KillSwitch, RiskEvent
from app.services.risk_service import RiskService
from app.api.deps import get_current_user

router = APIRouter(prefix="/risk", tags=["Risk Management & Kill Switches"])


class RiskSettingsUpdateRequest(BaseModel):
    max_order_value: Optional[float] = Field(None, ge=1000.0, le=5000000.0)
    max_daily_loss: Optional[float] = Field(None, ge=1000.0, le=1000000.0)
    max_portfolio_exposure_pct: Optional[float] = Field(None, ge=0.01, le=1.0)
    max_symbol_exposure_pct: Optional[float] = Field(None, ge=0.01, le=1.0)
    max_position_value: Optional[float] = Field(None, ge=1000.0, le=5000000.0)
    max_open_positions: Optional[int] = Field(None, ge=1, le=50)
    max_quantity: Optional[int] = Field(None, ge=1, le=10000)
    max_daily_orders: Optional[int] = Field(None, ge=1, le=200)


class KillSwitchToggleRequest(BaseModel):
    scope: str = Field("USER", description="PLATFORM, USER, AI_TRADING")
    is_active: bool
    reason: Optional[str] = None


@router.get("/settings")
async def get_risk_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    settings_obj = await RiskService.get_or_create_risk_settings(db, user.id)
    return {
        "user_id": str(user.id),
        "max_order_value": float(settings_obj.max_order_value),
        "max_daily_loss": float(settings_obj.max_daily_loss),
        "max_portfolio_exposure_pct": float(settings_obj.max_portfolio_exposure_pct),
        "max_symbol_exposure_pct": float(settings_obj.max_symbol_exposure_pct),
        "max_position_value": float(settings_obj.max_position_value),
        "max_open_positions": settings_obj.max_open_positions,
        "max_quantity": settings_obj.max_quantity,
        "max_daily_orders": settings_obj.max_daily_orders,
        "updated_at": settings_obj.updated_at.isoformat()
    }


@router.put("/settings")
async def update_risk_settings(
    req: RiskSettingsUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    settings_obj = await RiskService.get_or_create_risk_settings(db, user.id)
    if req.max_order_value is not None:
        settings_obj.max_order_value = Decimal(str(req.max_order_value))
    if req.max_daily_loss is not None:
        settings_obj.max_daily_loss = Decimal(str(req.max_daily_loss))
    if req.max_portfolio_exposure_pct is not None:
        settings_obj.max_portfolio_exposure_pct = Decimal(str(req.max_portfolio_exposure_pct))
    if req.max_symbol_exposure_pct is not None:
        settings_obj.max_symbol_exposure_pct = Decimal(str(req.max_symbol_exposure_pct))
    if req.max_position_value is not None:
        settings_obj.max_position_value = Decimal(str(req.max_position_value))
    if req.max_open_positions is not None:
        settings_obj.max_open_positions = req.max_open_positions
    if req.max_quantity is not None:
        settings_obj.max_quantity = req.max_quantity
    if req.max_daily_orders is not None:
        settings_obj.max_daily_orders = req.max_daily_orders

    await db.commit()
    await db.refresh(settings_obj)
    return {
        "status": "UPDATED",
        "max_order_value": float(settings_obj.max_order_value),
        "max_daily_loss": float(settings_obj.max_daily_loss),
        "max_open_positions": settings_obj.max_open_positions,
        "max_quantity": settings_obj.max_quantity
    }


@router.get("/kill-switch")
async def get_kill_switches(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(KillSwitch).where(
            (KillSwitch.scope == "PLATFORM") | (KillSwitch.user_id == user.id) | (KillSwitch.scope == "AI_TRADING")
        )
    )
    switches = res.scalars().all()
    return [
        {
            "id": str(s.id),
            "scope": s.scope,
            "is_active": s.is_active,
            "reason": s.reason,
            "activated_at": s.activated_at.isoformat() if s.activated_at else None
        }
        for s in switches
    ]


@router.post("/kill-switch")
async def toggle_kill_switch(
    req: KillSwitchToggleRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # If scope is PLATFORM and user is not admin, reject
    if req.scope.upper() == "PLATFORM" and user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin authorization required for platform kill switch")

    target_user_id = user.id if req.scope.upper() == "USER" else None
    ks = await RiskService.toggle_kill_switch(
        db=db,
        scope=req.scope,
        is_active=req.is_active,
        user_id=target_user_id,
        reason=req.reason
    )
    return {
        "status": "KILL_SWITCH_UPDATED",
        "scope": ks.scope,
        "is_active": ks.is_active,
        "reason": ks.reason
    }


@router.get("/events")
async def get_risk_events(
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(RiskEvent)
        .where(RiskEvent.user_id == user.id)
        .order_by(RiskEvent.created_at.desc())
        .limit(limit)
    )
    events = res.scalars().all()
    return [
        {
            "id": str(e.id),
            "symbol": e.symbol,
            "side": e.side,
            "check_name": e.check_name,
            "passed": e.passed,
            "severity": e.severity,
            "rejection_code": e.rejection_code,
            "rejection_reason": e.rejection_reason,
            "created_at": e.created_at.isoformat()
        }
        for e in events
    ]
