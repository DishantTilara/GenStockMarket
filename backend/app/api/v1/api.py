from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.market import router as market_router
from app.api.v1.technical import router as technical_router
from app.api.v1.scanner import router as scanner_router
from app.api.v1.watchlists import router as watchlists_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.news import router as news_router
from app.api.v1.ai import router as ai_router
from app.api.v1.strategies import router as strategies_router
from app.api.v1.backtests import router as backtests_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.orders import router as orders_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(wallet_router)
api_router.include_router(market_router)
api_router.include_router(technical_router)
api_router.include_router(scanner_router)
api_router.include_router(watchlists_router)
api_router.include_router(alerts_router)
api_router.include_router(news_router)
api_router.include_router(ai_router)
api_router.include_router(strategies_router)
api_router.include_router(backtests_router)
api_router.include_router(portfolio_router)
api_router.include_router(orders_router)
