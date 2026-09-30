from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.redis import redis_service
from app.services.market_service import MarketService
from app.schemas.market import MarketHealthResponse

router = APIRouter(tags=["Health & Observability"])


@router.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "service": "Indian Stock Market GenAI Platform",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/database")
async def database_health(db: AsyncSession = Depends(get_db)):
    try:
        t_start = datetime.now(timezone.utc)
        await db.execute(text("SELECT 1"))
        latency = (datetime.now(timezone.utc) - t_start).total_seconds() * 1000
        return {
            "status": "UP",
            "latency_ms": round(latency, 2),
            "database": "PostgreSQL / SQLite"
        }
    except Exception as e:
        return {"status": "DOWN", "error": str(e)}


@router.get("/health/redis")
async def redis_health():
    is_ping_ok = await redis_service.ping()
    return {
        "status": "UP" if is_ping_ok else "DOWN",
        "provider": "Redis / Resilient InMemory Fallback"
    }


@router.get("/health/market", response_model=MarketHealthResponse)
async def market_health(db: AsyncSession = Depends(get_db)):
    health_data = await MarketService.get_market_health(db)
    return MarketHealthResponse(**health_data)
