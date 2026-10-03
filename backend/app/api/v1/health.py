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
@router.get("/health/market-data", response_model=MarketHealthResponse)
async def market_health(db: AsyncSession = Depends(get_db)):
    health_data = await MarketService.get_market_health(db)
    return MarketHealthResponse(**health_data)


@router.get("/health/paper-trading")
async def paper_trading_health(db: AsyncSession = Depends(get_db)):
    from app.services.paper_reconciliation_service import PaperReconciliationService
    return await PaperReconciliationService.reconcile_paper_trading(db)


@router.get("/health/broker")
async def broker_health():
    from app.providers.broker.factory import get_broker_provider
    from app.core.config import settings
    provider = get_broker_provider()
    account_info = await provider.get_account()
    return {
        "status": "UP" if account_info.get("is_connected") else "DISCONNECTED",
        "trading_mode": settings.TRADING_MODE,
        "broker_provider": settings.BROKER_PROVIDER,
        "account_info": account_info
    }


@router.get("/health/reconciliation")
async def reconciliation_health(db: AsyncSession = Depends(get_db)):
    from app.models.broker import BrokerReconciliationEvent
    from sqlalchemy import select, func
    res = await db.execute(
        select(func.count(BrokerReconciliationEvent.id))
        .where(BrokerReconciliationEvent.resolved == False)
    )
    unresolved_count = res.scalar() or 0
    return {
        "status": "HEALTHY" if unresolved_count == 0 else "ATTENTION_REQUIRED",
        "unresolved_discrepancies": unresolved_count,
        "last_check_timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health/ai")
async def ai_health():
    from app.core.config import settings
    has_key = bool(settings.GROQ_API_KEY and settings.GROQ_API_KEY != "mock_key")
    return {
        "status": "UP" if has_key else "DEGRADED",
        "provider": "Groq",
        "model": "llama-3.3-70b-versatile",
        "fail_closed_enabled": True
    }


