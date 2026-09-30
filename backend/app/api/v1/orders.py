from typing import List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.audit import log_audit_event
from app.models.user import User
from app.models.order import Order
from app.services.risk_service import RiskService
from app.services.trade_setup_service import TradeSetupService
from app.schemas.risk import TradeSetupResponse, RiskValidationRequest, RiskValidationResponse, OrderExecuteRequest, OrderResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders & Risk Engine"])


@router.post("/trade-setup", response_model=TradeSetupResponse)
async def generate_trade_setup(
    symbol: str = Query(..., min_length=2),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await TradeSetupService.generate_setup(db, user.id, symbol)


@router.post("/validate-risk", response_model=RiskValidationResponse)
async def validate_risk(
    req: RiskValidationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await RiskService.validate_pre_flight(db, user.id, req)


@router.post("/execute", response_model=OrderResponse)
async def execute_confirmed_order(
    req: OrderExecuteRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await TradeSetupService.execute_confirmed_order(db, user.id, req)
    await log_audit_event(
        db,
        action="USER_ORDER_EXECUTED",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        resource_type="order",
        resource_id=str(order.id),
        details={"symbol": order.symbol, "side": order.side, "qty": order.quantity, "price": str(order.price)}
    )
    return order


@router.get("", response_model=List[OrderResponse])
async def list_orders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()))
    return list(res.scalars().all())
