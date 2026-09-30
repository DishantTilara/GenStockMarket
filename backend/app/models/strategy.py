import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Index, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    timeframe = Column(String(10), default="5m", nullable=False)
    entry_rules = Column(JSON, nullable=False)  # list of rule conditions
    exit_rules = Column(JSON, nullable=False)
    stop_loss = Column(JSON, nullable=False)
    target = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="strategies")
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_symbol = Column(String(50), nullable=False)
    timeframe = Column(String(10), default="5m", nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    initial_capital = Column(Numeric(20, 2), default=100000.00, nullable=False)
    
    # Results
    total_return = Column(Numeric(10, 4), default=0.0, nullable=False)
    cagr = Column(Numeric(10, 4), default=0.0, nullable=False)
    win_rate = Column(Numeric(10, 4), default=0.0, nullable=False)
    loss_rate = Column(Numeric(10, 4), default=0.0, nullable=False)
    profit_factor = Column(Numeric(10, 4), default=0.0, nullable=False)
    max_drawdown = Column(Numeric(10, 4), default=0.0, nullable=False)
    sharpe_ratio = Column(Numeric(10, 4), default=0.0, nullable=False)
    trade_count = Column(Integer, default=0, nullable=False)
    equity_curve = Column(JSON, nullable=True)  # List of {time, equity}
    status = Column(String(30), default="COMPLETED", nullable=False)  # RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    strategy = relationship("Strategy", back_populates="backtests")
    trades = relationship("BacktestTrade", back_populates="backtest", cascade="all, delete-orphan")


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    entry_price = Column(Numeric(20, 4), nullable=False)
    exit_price = Column(Numeric(20, 4), nullable=False)
    quantity = Column(Integer, nullable=False)
    pnl = Column(Numeric(20, 2), nullable=False)
    pnl_pct = Column(Numeric(10, 4), nullable=False)
    exit_reason = Column(String(50), nullable=False)  # TARGET, STOP_LOSS, TIME_EXIT

    backtest = relationship("Backtest", back_populates="trades")
