import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class BrokerAccount(Base):
    __tablename__ = "broker_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    broker_name = Column(String(50), nullable=False, default="sandbox")  # zerodha, upstox, angelone, sandbox, paper
    environment = Column(String(20), nullable=False, default="SANDBOX")  # SANDBOX, LIVE
    client_id = Column(String(100), nullable=True)
    api_key = Column(String(255), nullable=True)
    encrypted_secret = Column(String(500), nullable=True)
    encrypted_access_token = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    last_connected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", backref="broker_accounts")
    orders = relationship("BrokerOrder", back_populates="account", cascade="all, delete-orphan")
    positions = relationship("BrokerPosition", back_populates="account", cascade="all, delete-orphan")
    trades = relationship("BrokerTrade", back_populates="account", cascade="all, delete-orphan")


class BrokerOrder(Base):
    __tablename__ = "broker_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_account_id = Column(UUID(as_uuid=True), ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    broker_order_id = Column(String(100), nullable=False, index=True)
    internal_order_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), default="NSE", nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, SL
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(20, 2), nullable=True)
    status = Column(String(30), nullable=False, default="OPEN")  # OPEN, FILLED, REJECTED, CANCELLED
    filled_quantity = Column(Integer, default=0, nullable=False)
    average_price = Column(Numeric(20, 2), nullable=True)
    error_message = Column(String(500), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    account = relationship("BrokerAccount", back_populates="orders")


class BrokerTrade(Base):
    __tablename__ = "broker_trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_account_id = Column(UUID(as_uuid=True), ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    broker_trade_id = Column(String(100), nullable=False, index=True)
    broker_order_id = Column(String(100), nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(20, 2), nullable=False)
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    account = relationship("BrokerAccount", back_populates="trades")


class BrokerPosition(Base):
    __tablename__ = "broker_positions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_account_id = Column(UUID(as_uuid=True), ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    buy_price = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"))
    current_price = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"))
    pnl = Column(Numeric(20, 2), nullable=False, default=Decimal("0.00"))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    account = relationship("BrokerAccount", back_populates="positions")


class BrokerReconciliationEvent(Base):
    __tablename__ = "broker_reconciliation_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broker_account_id = Column(UUID(as_uuid=True), ForeignKey("broker_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    discrepancy_type = Column(String(100), nullable=False)  # UNKNOWN_BROKER_ORDER, MISSING_INTERNAL_ORDER, STATUS_MISMATCH, etc.
    details = Column(JSON, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolution_notes = Column(String(500), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
