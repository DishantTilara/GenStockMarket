import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Numeric, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), default="Main Portfolio", nullable=False)
    initial_cash: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("1000000.00"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="portfolios")
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="CASCADE"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0.0"), nullable=False)
    current_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), default=Decimal("0.0"), nullable=False)
    unrealized_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.0"), nullable=False)
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.0"), nullable=False)
    stop_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    target_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    portfolio = relationship("Portfolio", back_populates="positions")


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="SET NULL"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    charges: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.0"), nullable=False)
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), default=Decimal("0.0"), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    portfolio = relationship("Portfolio", back_populates="transactions")
