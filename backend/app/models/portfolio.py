import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), default="Main Portfolio", nullable=False)
    initial_cash = Column(Numeric(20, 2), default=1000000.00, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="portfolios")
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)
    sector = Column(String(100), nullable=True)
    quantity = Column(Integer, default=0, nullable=False)
    average_price = Column(Numeric(20, 4), default=0.0, nullable=False)
    current_price = Column(Numeric(20, 4), default=0.0, nullable=False)
    unrealized_pnl = Column(Numeric(20, 2), default=0.0, nullable=False)
    realized_pnl = Column(Numeric(20, 2), default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    portfolio = relationship("Portfolio", back_populates="positions")


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id = Column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="SET NULL"), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(20, 4), nullable=False)
    charges = Column(Numeric(20, 2), default=0.0, nullable=False)
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    portfolio = relationship("Portfolio", back_populates="transactions")
