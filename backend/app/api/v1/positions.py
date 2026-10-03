import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.core.errors import AppError, ResourceNotFoundError
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioPosition
from app.providers.market_data.factory import get_market_data_provider
from app.services.portfolio_service import PortfolioService
from app.services.paper_trading_service import PaperTradingService
from app.schemas.portfolio import PortfolioPositionResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/positions", tags=["Positions"])


class ModifySlTargetRequest(BaseModel):
    stop_loss: Optional[Decimal] = None
    target_price: Optional[Decimal] = None


class PositionsListResponse(BaseModel):
    open_positions: List[PortfolioPositionResponse]
    closed_positions: List[PortfolioPositionResponse]
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    total_current_value: Decimal


@router.get("", response_model=PositionsListResponse)
async def list_positions(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    portfolio = await PortfolioService.get_or_create_portfolio(db, user.id)
    market_provider = get_market_data_provider()

    res = await db.execute(
        select(PortfolioPosition).where(PortfolioPosition.portfolio_id == portfolio.id)
    )
    all_positions = res.scalars().all()

    open_pos: List[PortfolioPositionResponse] = []
    closed_pos: List[PortfolioPositionResponse] = []
    tot_unrealized = Decimal("0.00")
    tot_realized = Decimal("0.00")
    tot_val = Decimal("0.00")

    for p in all_positions:
        quote = await market_provider.get_quote(p.symbol)
        cur_price = Decimal(str(quote["price"])) if quote and "price" in quote else p.average_price

        invested = p.average_price * Decimal(str(p.quantity))
        val = cur_price * Decimal(str(p.quantity))
        unrealized = val - invested if p.quantity > 0 else Decimal("0.00")
        unrealized_pct = ((cur_price - p.average_price) / p.average_price * Decimal("100")) if (p.quantity > 0 and p.average_price) else Decimal("0.00")
        realized = Decimal(str(p.realized_pnl or 0))

        tot_realized += realized

        pos_resp = PortfolioPositionResponse(
            id=p.id,
            symbol=p.symbol,
            sector=p.sector,
            quantity=p.quantity,
            average_price=p.average_price,
            current_price=cur_price,
            invested_amount=round(invested, 2),
            current_value=round(val, 2),
            unrealized_pnl=round(unrealized, 2),
            unrealized_pnl_pct=round(unrealized_pct, 2),
            realized_pnl=round(realized, 2),
            stop_loss=p.stop_loss,
            target_price=p.target_price
        )

        if p.quantity > 0 and p.is_active:
            open_pos.append(pos_resp)
            tot_unrealized += unrealized
            tot_val += val
        else:
            closed_pos.append(pos_resp)

    return PositionsListResponse(
        open_positions=open_pos,
        closed_positions=closed_pos,
        total_unrealized_pnl=round(tot_unrealized, 2),
        total_realized_pnl=round(tot_realized, 2),
        total_current_value=round(tot_val, 2)
    )


@router.post("/{symbol}/close")
async def close_position(
    symbol: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Closes an open position immediately via paper MARKET SELL."""
    sym = symbol.upper()
    portfolio = await PortfolioService.get_or_create_portfolio(db, user.id)

    res = await db.execute(
        select(PortfolioPosition)
        .where(PortfolioPosition.portfolio_id == portfolio.id)
        .where(PortfolioPosition.symbol == sym)
        .where(PortfolioPosition.quantity > 0)
    )
    position = res.scalar_one_or_none()
    if not position or position.quantity <= 0:
        raise AppError(code="NO_OPEN_POSITION", message=f"No open holding found for {sym}")

    qty_to_close = position.quantity
    order = await PaperTradingService.create_paper_order(
        db=db,
        user_id=user.id,
        symbol=sym,
        side="SELL",
        order_type="MARKET",
        quantity=qty_to_close,
        user_confirmed=True
    )
    return {
        "status": "CLOSED",
        "symbol": sym,
        "quantity_closed": qty_to_close,
        "execution_price": float(order.execution_price or order.price),
        "realized_pnl": float(order.realized_pnl or 0)
    }


@router.post("/{symbol}/modify-sl-target")
async def modify_position_sl_target(
    symbol: str,
    req: ModifySlTargetRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates stop loss and target price for an open position."""
    sym = symbol.upper()
    portfolio = await PortfolioService.get_or_create_portfolio(db, user.id)

    res = await db.execute(
        select(PortfolioPosition)
        .where(PortfolioPosition.portfolio_id == portfolio.id)
        .where(PortfolioPosition.symbol == sym)
        .where(PortfolioPosition.quantity > 0)
    )
    position = res.scalar_one_or_none()
    if not position or position.quantity <= 0:
        raise AppError(code="NO_OPEN_POSITION", message=f"No open holding found for {sym}")

    if req.stop_loss is not None:
        position.stop_loss = req.stop_loss
    if req.target_price is not None:
        position.target_price = req.target_price

    await db.commit()
    await db.refresh(position)

    return {
        "status": "UPDATED",
        "symbol": sym,
        "stop_loss": float(position.stop_loss) if position.stop_loss else None,
        "target_price": float(position.target_price) if position.target_price else None
    }
