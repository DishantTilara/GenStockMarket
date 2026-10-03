import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.audit import log_audit_event
from app.core.errors import AppError, ResourceNotFoundError
from app.models.user import User
from app.models.order import Order, OrderEvent
from app.services.risk_service import RiskService
from app.services.trade_setup_service import TradeSetupService
from app.services.paper_trading_service import PaperTradingService
from app.schemas.risk import (
    TradeSetupResponse,
    RiskValidationRequest,
    RiskValidationResponse,
    OrderExecuteRequest,
    OrderCreateRequest,
    OrderModifyRequest,
    OrderResponse,
    OrderEventResponse,
    PaperResetRequest
)
from app.api.deps import get_current_user

router = APIRouter(tags=["Orders & Paper Trading Engine"])


# 1. Trade Setup & Risk Validation Endpoints
@router.post("/orders/trade-setup", response_model=TradeSetupResponse)
async def generate_trade_setup(
    symbol: str = Query(..., min_length=2),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await TradeSetupService.generate_setup(db, user.id, symbol)


@router.post("/orders/validate-risk", response_model=RiskValidationResponse)
async def validate_risk(
    req: RiskValidationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await RiskService.validate_pre_flight(db, user.id, req)


@router.post("/orders/execute", response_model=OrderResponse)
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


# 2. Direct Paper Order Placement & Listing
@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_paper_order(
    req: OrderCreateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Place a paper order (MARKET or LIMIT) with automated pre-flight risk check."""
    # Determine effective price for risk check
    eff_price = req.price or req.limit_price
    if not eff_price:
        from app.providers.market_data.factory import get_market_data_provider
        q = await get_market_data_provider().get_quote(req.symbol)
        eff_price = Decimal(str(q["price"]))

    risk_req = RiskValidationRequest(
        symbol=req.symbol,
        side=req.side,
        order_type=req.order_type,
        quantity=req.quantity,
        price=eff_price,
        stop_loss=req.stop_loss,
        target=req.target_price
    )

    risk_res = await RiskService.validate_pre_flight(db, user.id, risk_req)
    if not risk_res.approved:
        raise AppError(
            code=risk_res.rejection_code or "RISK_VALIDATION_FAILED",
            message=risk_res.rejection_reason or "Order rejected by platform risk engine"
        )

    order = await PaperTradingService.create_paper_order(
        db=db,
        user_id=user.id,
        symbol=req.symbol,
        side=req.side,
        order_type=req.order_type,
        quantity=req.quantity,
        price=req.price or req.limit_price,
        stop_loss=req.stop_loss,
        target_price=req.target_price,
        idempotency_key=req.idempotency_key,
        user_confirmed=True
    )

    await log_audit_event(
        db,
        action="PAPER_ORDER_PLACED",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        resource_type="order",
        resource_id=str(order.id),
        details={"symbol": order.symbol, "side": order.side, "qty": order.quantity, "status": order.status}
    )
    return order


@router.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by status: OPEN, PENDING, FILLED, CANCELLED, REJECTED"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    side: Optional[str] = Query(None, description="Filter by side: BUY, SELL"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.events))
        .order_by(Order.created_at.desc())
    )
    if status:
        if status.upper() == "OPEN":
            stmt = stmt.where(Order.status.in_(["PENDING", "SUBMITTED"]))
        else:
            stmt = stmt.where(Order.status == status.upper())
    if symbol:
        stmt = stmt.where(Order.symbol == symbol.upper())
    if side:
        stmt = stmt.where(Order.side == side.upper())

    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/orders/{id}", response_model=OrderResponse)
async def get_order_by_id(
    id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Order)
        .where(and_(Order.id == id, Order.user_id == user.id))
        .options(selectinload(Order.events))
    )
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        raise ResourceNotFoundError("Order", id)
    return order


@router.post("/orders/{id}/cancel", response_model=OrderResponse)
async def cancel_order(
    id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await PaperTradingService.cancel_paper_order(db, user.id, id)


@router.post("/orders/{id}/modify", response_model=OrderResponse)
async def modify_order(
    id: uuid.UUID,
    req: OrderModifyRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await PaperTradingService.modify_paper_order(
        db=db,
        user_id=user.id,
        order_id=id,
        new_quantity=req.quantity,
        new_price=req.price,
        new_stop_loss=req.stop_loss,
        new_target=req.target_price
    )


@router.get("/orders/{id}/events", response_model=List[OrderEventResponse])
async def get_order_events(
    id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    order = await db.get(Order, id)
    if not order or order.user_id != user.id:
        raise ResourceNotFoundError("Order", id)

    res = await db.execute(
        select(OrderEvent)
        .where(OrderEvent.order_id == id)
        .order_by(OrderEvent.created_at.asc())
    )
    return list(res.scalars().all())


# 3. Paper Trading Demo Reset Endpoint (Section 17)
@router.post("/paper/reset")
async def reset_paper_trading(
    req: Optional[PaperResetRequest] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Dev/Demo reset: Cancels pending orders, resets positions, resets wallet to ₹10,00,000."""
    clear_history = req.clear_history if req else True
    return await PaperTradingService.reset_paper_account(db, user.id, clear_history=clear_history)


@router.get("/trading/environment")
async def get_trading_environment():
    """Return active trading environment mode and broker safety configurations."""
    from app.core.config import settings
    return {
        "trading_mode": settings.TRADING_MODE,
        "broker_provider": settings.BROKER_PROVIDER,
        "broker_env": settings.BROKER_ENV,
        "is_paper": settings.is_paper,
        "is_sandbox": settings.is_sandbox,
        "is_live": settings.is_live,
        "require_explicit_confirmation": settings.REQUIRE_EXPLICIT_TRADE_CONFIRMATION
    }
