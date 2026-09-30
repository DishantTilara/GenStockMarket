import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Numeric, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class TradeSetup(Base):
    __tablename__ = "trade_setups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    entry_zone = Column(JSON, nullable=False)  # {min: x, max: y}
    stop_loss = Column(Numeric(20, 4), nullable=False)
    target_price = Column(Numeric(20, 4), nullable=False)
    quantity = Column(Integer, nullable=False)
    risk_amount = Column(Numeric(20, 2), nullable=False)
    risk_reward = Column(Numeric(10, 2), nullable=False)
    reasons = Column(JSON, nullable=False)  # list of strings
    invalidation = Column(JSON, nullable=False)  # list of strings
    status = Column(String(30), default="PENDING_APPROVAL", nullable=False)  # PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED
    data_timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), default="LIMIT", nullable=False)  # MARKET, LIMIT, SL_LIMIT
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(20, 4), nullable=False)
    stop_loss = Column(Numeric(20, 4), nullable=True)
    target = Column(Numeric(20, 4), nullable=True)
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, SUBMITTED, FILLED, REJECTED, CANCELLED
    broker_order_id = Column(String(100), nullable=True)
    risk_approved = Column(Boolean, default=False, nullable=False)
    user_confirmed = Column(Boolean, default=False, nullable=False)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    events = relationship("OrderEvent", back_populates="order", cascade="all, delete-orphan")


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # CREATED, RISK_PASSED, RISK_FAILED, USER_CONFIRMED, BROKER_SUBMITTED, BROKER_FILLED, CANCELLED
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("Order", back_populates="events")
