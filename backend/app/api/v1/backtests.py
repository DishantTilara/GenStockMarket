import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.strategy import Backtest, BacktestTrade
from app.schemas.strategy import BacktestRequest, BacktestResponse, BacktestTradeResponse
from app.services.backtest_service import BacktestService
from app.api.deps import get_current_user

router = APIRouter(prefix="/backtests", tags=["Backtesting Engine"])


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    req: BacktestRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await BacktestService.run_backtest(db, user.id, req)


@router.get("", response_model=List[dict])
async def list_user_backtests(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Backtest)
        .where(Backtest.user_id == user.id)
        .order_by(Backtest.created_at.desc())
        .limit(20)
    )
    backtests = res.scalars().all()
    return [
        {
            "id": b.id,
            "symbol": b.instrument_symbol,
            "timeframe": b.timeframe,
            "total_return": b.total_return,
            "win_rate": b.win_rate,
            "profit_factor": b.profit_factor,
            "max_drawdown": b.max_drawdown,
            "trade_count": b.trade_count,
            "created_at": b.created_at
        }
        for b in backtests
    ]


@router.get("/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_by_id(
    backtest_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    b = await db.get(Backtest, backtest_id)
    if not b or b.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backtest not found")

    trades_res = await db.execute(select(BacktestTrade).where(BacktestTrade.backtest_id == b.id))
    trades = trades_res.scalars().all()

    return BacktestResponse(
        id=b.id,
        symbol=b.instrument_symbol,
        timeframe=b.timeframe,
        initial_capital=b.initial_capital,
        total_return=b.total_return,
        cagr=b.cagr,
        win_rate=b.win_rate,
        loss_rate=b.loss_rate,
        profit_factor=b.profit_factor,
        max_drawdown=b.max_drawdown,
        sharpe_ratio=b.sharpe_ratio,
        trade_count=b.trade_count,
        trades=[BacktestTradeResponse(
            entry_time=t.entry_time,
            exit_time=t.exit_time,
            side=t.side,
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            quantity=t.quantity,
            pnl=t.pnl,
            pnl_pct=t.pnl_pct,
            exit_reason=t.exit_reason
        ) for t in trades],
        equity_curve=b.equity_curve or [],
        status=b.status,
        created_at=b.created_at
    )
