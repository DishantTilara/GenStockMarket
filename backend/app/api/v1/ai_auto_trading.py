import uuid
from decimal import Decimal
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.user import User
from app.services.ai_permission_service import AIPermissionService
from app.services.risk_service import RiskService
from app.schemas.risk import RiskValidationRequest
from app.providers.broker.factory import get_broker_provider
from app.services.order_state_machine import OrderStateMachine
from app.models.order import Order
from app.api.deps import get_current_user

router = APIRouter(prefix="/ai/auto-trading", tags=["AI Auto-Trading Engine"])


class AIPermissionUpdateRequest(BaseModel):
    auto_trading_enabled: Optional[bool] = None
    auto_buy_enabled: Optional[bool] = None
    auto_sell_enabled: Optional[bool] = None
    require_risk_approval: Optional[bool] = None
    max_order_value: Optional[float] = Field(None, ge=100.0, le=500000.0)
    max_daily_loss: Optional[float] = Field(None, ge=100.0, le=100000.0)
    max_position_value: Optional[float] = Field(None, ge=100.0, le=500000.0)
    max_open_positions: Optional[int] = Field(None, ge=1, le=20)
    max_daily_orders: Optional[int] = Field(None, ge=1, le=100)
    allowed_symbols: Optional[List[str]] = None
    allowed_exchanges: Optional[List[str]] = None
    allowed_order_types: Optional[List[str]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    kill_switch_enabled: Optional[bool] = None


class AISignalPayload(BaseModel):
    symbol: str
    exchange: str = "NSE"
    action: str  # BUY, SELL, WATCH, NO_TRADE, INSUFFICIENT_DATA
    quantity: int = Field(..., gt=0)
    entry_price: float = Field(..., gt=0.0)
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    order_type: str = "LIMIT"
    strategy: Optional[str] = "GENAI_MOMENTUM"
    reason: Optional[str] = None


@router.get("/settings")
async def get_ai_trading_settings(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch current user's AI Auto-Trading configuration and permissions."""
    perm = await AIPermissionService.get_or_create_permission(db, user.id)
    return {
        "user_id": str(user.id),
        "auto_trading_enabled": perm.auto_trading_enabled,
        "auto_buy_enabled": perm.auto_buy_enabled,
        "auto_sell_enabled": perm.auto_sell_enabled,
        "require_risk_approval": perm.require_risk_approval,
        "max_order_value": float(perm.max_order_value),
        "max_daily_loss": float(perm.max_daily_loss),
        "max_position_value": float(perm.max_position_value),
        "max_open_positions": perm.max_open_positions,
        "max_daily_orders": perm.max_daily_orders,
        "allowed_symbols": perm.allowed_symbols,
        "allowed_exchanges": perm.allowed_exchanges,
        "allowed_order_types": perm.allowed_order_types,
        "start_time": perm.start_time,
        "end_time": perm.end_time,
        "kill_switch_enabled": perm.kill_switch_enabled,
        "updated_at": perm.updated_at.isoformat()
    }


@router.put("/settings")
async def update_ai_trading_settings(
    req: AIPermissionUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update AI Auto-Trading permissions and limits."""
    updates = req.model_dump(exclude_unset=True)
    perm = await AIPermissionService.update_permission(db, user.id, updates)
    return {
        "status": "UPDATED",
        "auto_trading_enabled": perm.auto_trading_enabled,
        "auto_buy_enabled": perm.auto_buy_enabled,
        "auto_sell_enabled": perm.auto_sell_enabled,
        "kill_switch_enabled": perm.kill_switch_enabled
    }


@router.post("/emergency-stop")
async def trigger_emergency_stop(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Immediate Emergency Stop: completely halts all AI trading automation."""
    perm = await AIPermissionService.emergency_stop(db, user.id, reason="User clicked Emergency Stop button")
    return {
        "status": "EMERGENCY_STOP_ENGAGED",
        "auto_trading_enabled": perm.auto_trading_enabled,
        "auto_buy_enabled": perm.auto_buy_enabled,
        "auto_sell_enabled": perm.auto_sell_enabled,
        "kill_switch_enabled": perm.kill_switch_enabled
    }


@router.post("/evaluate-signal")
async def evaluate_ai_signal(
    signal: AISignalPayload,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    End-to-End AI Trading Pipeline:
    Signal -> AI Permission Engine -> Risk Engine -> Order Validator -> Execution Engine -> Broker.
    """
    # Step 1: AI Permission Engine
    allowed, perm_reason, meta = await AIPermissionService.evaluate_ai_signal(
        db=db,
        user_id=user.id,
        signal=signal.model_dump()
    )
    if not allowed:
        return {
            "status": "BLOCKED_BY_AI_PERMISSIONS",
            "reason": perm_reason,
            "executed": False
        }

    # Step 2: Risk Engine Pre-Flight Check (with is_ai_order=True)
    risk_req = RiskValidationRequest(
        symbol=signal.symbol,
        side=signal.action,
        order_type=signal.order_type,
        quantity=signal.quantity,
        price=Decimal(str(signal.entry_price)),
        stop_loss=Decimal(str(signal.stop_loss)) if signal.stop_loss else None,
        target=Decimal(str(signal.target)) if signal.target else None
    )
    risk_res = await RiskService.validate_pre_flight(db, user.id, risk_req, is_ai_order=True)
    if not risk_res.approved:
        return {
            "status": "BLOCKED_BY_RISK_ENGINE",
            "reason": risk_res.rejection_reason,
            "rejection_code": risk_res.rejection_code,
            "executed": False
        }

    # Step 3: Execution via Broker Adapter
    broker = get_broker_provider()
    broker_order = await broker.place_order({
        "symbol": signal.symbol,
        "side": signal.action,
        "order_type": signal.order_type,
        "quantity": signal.quantity,
        "price": signal.entry_price
    })

    # Step 4: Record in DB
    order = Order(
        user_id=user.id,
        symbol=signal.symbol.upper(),
        side=signal.action.upper(),
        order_type=signal.order_type.upper(),
        quantity=signal.quantity,
        price=Decimal(str(signal.entry_price)),
        stop_loss=Decimal(str(signal.stop_loss)) if signal.stop_loss else None,
        target=Decimal(str(signal.target)) if signal.target else None,
        status=broker_order.get("status", "OPEN"),
        broker_order_id=broker_order.get("broker_order_id"),
        risk_approved=True,
        user_confirmed=True
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    return {
        "status": "EXECUTED",
        "order_id": str(order.id),
        "broker_order_id": order.broker_order_id,
        "symbol": order.symbol,
        "side": order.side,
        "quantity": order.quantity,
        "price": float(order.price),
        "order_status": order.status,
        "executed": True
    }
