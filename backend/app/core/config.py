import json
from typing import List, Optional
from pydantic import Field, model_validator
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
    MARKET_DATA_PROVIDER: str = "yfinance"
    MARKET_DATA_API_KEY: Optional[str] = None
    MARKET_DATA_API_SECRET: Optional[str] = None
    MARKET_INGESTION_INTERVAL_SECONDS: float = 1.0
    MARKET_POLL_INTERVAL_SECONDS: float = 30.0
    MARKET_DATA_MAX_AGE_SECONDS: int = 120
    AUTO_SEED_INSTRUMENTS: bool = True

    # AI Provider
    LLM_PROVIDER: str = "groq"
    AI_PROVIDER: Optional[str] = None
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4o-mini"
    LOCAL_LLM_URL: str = "http://localhost:11434/v1"

    # Groq Provider
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_TIMEOUT_SECONDS: float = 30.0

    # News Provider
    NEWS_PROVIDER: str = "simulated"
    NEWS_API_KEY: Optional[str] = None

    # Broker Provider
    BROKER_PROVIDER: str = "paper"
    BROKER_ENV: str = "paper"  # paper, sandbox, live
    BROKER_API_KEY: Optional[str] = None
    BROKER_API_SECRET: Optional[str] = None
    BROKER_ACCESS_TOKEN: Optional[str] = None

    # Paper Trading Configuration
    TRADING_MODE: str = "PAPER"  # PAPER, SANDBOX, LIVE
    PAPER_BROKERAGE_ENABLED: bool = True
    PAPER_SLIPPAGE_BPS: int = 5
    PAPER_CHARGES_ENABLED: bool = True

    # Risk Management
    MAX_ORDER_VALUE_INR: float = 500000.00
    MAX_PORTFOLIO_EXPOSURE_PCT: float = 0.25
    MAX_DAILY_LOSS_PCT: float = 0.05
    REQUIRE_EXPLICIT_TRADE_CONFIRMATION: bool = True

    # Razorpay Payment Gateway (TEST Mode)
    RAZORPAY_MODE: str = "test"
    RAZORPAY_KEY_ID: Optional[str] = None
    RAZORPAY_KEY_SECRET: Optional[str] = None
    RAZORPAY_WEBHOOK_SECRET: Optional[str] = None
    PAPER_INITIAL_BALANCE: float = 1000000.00

    # News Provider
    NEWS_PROVIDER: str = "simulated"
    NEWS_API_KEY: Optional[str] = None

    @model_validator(mode="after")
    def validate_trading_environment(self) -> "Settings":
        mode = self.TRADING_MODE.upper()
        broker = self.BROKER_PROVIDER.lower()

        valid_modes = {"PAPER", "SANDBOX", "LIVE"}
        if mode not in valid_modes:
            raise ValueError(f"Invalid TRADING_MODE '{self.TRADING_MODE}'. Must be one of {valid_modes}")

        # Enforce compatibility rules:
        # PAPER + live broker = reject
        # SANDBOX + live broker = reject
        # LIVE + paper broker = reject
        if mode == "PAPER" and broker in {"zerodha", "angelone", "upstox", "fyers", "live_broker"}:
            raise ValueError(f"Incompatible configuration: TRADING_MODE=PAPER cannot run with live broker provider '{broker}'")
        if mode == "SANDBOX" and broker in {"zerodha", "angelone", "upstox", "fyers", "live_broker"}:
            raise ValueError(f"Incompatible configuration: TRADING_MODE=SANDBOX cannot run with live broker provider '{broker}'")
        if mode == "LIVE" and broker in {"paper", "simulated", "sandbox"}:
            raise ValueError(f"Incompatible configuration: TRADING_MODE=LIVE cannot run with simulated/paper broker provider '{broker}'")

        return self

    @property
    def is_paper(self) -> bool:
        return self.TRADING_MODE.upper() == "PAPER"

    @property
    def is_sandbox(self) -> bool:
        return self.TRADING_MODE.upper() == "SANDBOX"

    @property
    def is_live(self) -> bool:
        return self.TRADING_MODE.upper() == "LIVE"


settings = Settings()


