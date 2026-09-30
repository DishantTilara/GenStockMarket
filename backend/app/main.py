import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import async_engine, Base, AsyncSessionLocal
from app.core.redis import redis_service
from app.core.errors import AppError, app_error_handler, http_error_handler, unhandled_exception_handler
from app.api.v1.api import api_router
from app.api.v1.health import router as health_router
from app.api.websocket import router as ws_router
from app.services.market_service import MarketService
from app.workers.market_ingestion_worker import run_market_ingestion

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Indian Stock Market GenAI Platform...")
    
    # 1. Connect Redis
    await redis_service.connect()

    # 2. Initialize Database tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema validated.")

    # 3. Auto seed instruments
    if settings.AUTO_SEED_INSTRUMENTS:
        async with AsyncSessionLocal() as db:
            seeded = await MarketService.ensure_instruments_seeded(db)
            logger.info(f"Initialized {len(seeded)} Indian equity & index instruments.")

    # 4. Launch continuous background market ingestion worker
    ingestion_task = asyncio.create_task(run_market_ingestion())

    yield

    logger.info("Shutting down platform services...")
    ingestion_task.cancel()
    await redis_service.disconnect()
    await async_engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Modular production-oriented Indian Stock Market GenAI Platform with real-time ingestion, deterministic indicators, double-entry ledger, and risk controls.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Routers
app.include_router(health_router)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router)

# Serve Frontend SPA
import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    index_file = os.path.join(frontend_dist, "index.html")

    @app.get("/")
    async def serve_root():
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "Indian Stock Market GenAI API active"}

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith(("api/", "ws", "health", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not found")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )
