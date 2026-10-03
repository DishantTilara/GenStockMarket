import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class TradeSetup(Base):
    __tablename__ = "trade_setups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    entry_zone: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # {min: x, max: y}
    stop_loss: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    target_price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    risk_reward: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reasons: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # list of strings
    invalidation: Mapped[List[str]] = mapped_column(JSON, nullable=False)  # list of strings
    status: Mapped[str] = mapped_column(String(30), default="PENDING_APPROVAL", nullable=False)  # PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED
    data_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=True)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # BUY, SELL
    order_type: Mapped[str] = mapped_column(String(20), default="LIMIT", nullable=False)  # MARKET, LIMIT, SL_LIMIT
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    stop_loss: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    target: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)  # PENDING, SUBMITTED, FILLED, REJECTED, CANCELLED, EXPIRED
    execution_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 4), nullable=True)
    charges: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.0"), nullable=False)
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(20, 2), default=Decimal("0.0"), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    source_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    risk_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    events = relationship("OrderEvent", back_populates="order", cascade="all, delete-orphan", order_by="asc(OrderEvent.created_at)")


class OrderEvent(Base):
    __tablename__ = "order_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATED, RISK_PASSED, RISK_FAILED, USER_CONFIRMED, BROKER_SUBMITTED, BROKER_FILLED, CANCELLED
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("Order", back_populates="events")
