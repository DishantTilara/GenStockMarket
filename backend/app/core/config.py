import json
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = "development"
    APP_NAME: str = "Indian Stock Market GenAI Platform"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "change-this-ultra-secure-secret-key-in-production-min-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000"
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/stockmarket"
    SYNC_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/stockmarket"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    # Market Data
    MARKET_DATA_PROVIDER: str = "simulated"
    MARKET_DATA_API_KEY: Optional[str] = None
    MARKET_DATA_API_SECRET: Optional[str] = None
    MARKET_INGESTION_INTERVAL_SECONDS: float = 1.0
    AUTO_SEED_INSTRUMENTS: bool = True

    # AI Provider
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LOCAL_LLM_URL: str = "http://localhost:11434/v1"

    # News Provider
    NEWS_PROVIDER: str = "simulated"
    NEWS_API_KEY: Optional[str] = None

    # Broker Provider
    BROKER_PROVIDER: str = "paper"
    BROKER_API_KEY: Optional[str] = None
    BROKER_API_SECRET: Optional[str] = None

    # Risk Management
    MAX_ORDER_VALUE_INR: float = 500000.00
    MAX_PORTFOLIO_EXPOSURE_PCT: float = 0.25
    MAX_DAILY_LOSS_PCT: float = 0.05
    REQUIRE_EXPLICIT_TRADE_CONFIRMATION: bool = True


settings = Settings()
