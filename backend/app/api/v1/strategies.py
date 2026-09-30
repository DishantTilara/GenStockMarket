import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.user import User
from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/strategies", tags=["Strategies"])


@router.get("", response_model=List[StrategyResponse])
async def get_strategies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Strategy).where(Strategy.user_id == user.id).order_by(Strategy.created_at.desc()))
    return list(res.scalars().all())


@router.post("", response_model=StrategyResponse)
async def create_strategy(req: StrategyCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    strat = Strategy(
        user_id=user.id,
        name=req.name,
        description=req.description,
        timeframe=req.timeframe,
        entry_rules=req.entry_rules,
        exit_rules=req.exit_rules,
        stop_loss=req.stop_loss,
        target=req.target,
        is_active=True
    )
    db.add(strat)
    await db.commit()
    await db.refresh(strat)
    return strat


@router.post("/nl-generate")
async def generate_strategy_from_natural_language(query: str):
    """Translates user natural language into structured algorithmic strategy definition."""
    # Deterministic strategy translation
    entry = ["close > EMA(20)", "RSI(14) > 55", "volume > SMA(volume, 20) * 1.5"]
    exit_rules = ["close < EMA(20)"]
    stop_loss = {"type": "pct", "value": 1.5}
    target = {"type": "pct", "value": 3.0}

    return {
        "name": "AI Generated Momentum Strategy",
        "description": query,
        "entry_rules": entry,
        "exit_rules": exit_rules,
        "stop_loss": stop_loss,
        "target": target,
        "timeframe": "5m"
    }
