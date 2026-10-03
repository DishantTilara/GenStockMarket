import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    available_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"), nullable=False)
    locked_balance: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=Decimal("0.00"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="wallet")
    ledger_entries = relationship("LedgerEntry", back_populates="wallet", cascade="all, delete-orphan", order_by="desc(LedgerEntry.created_at)")
    deposits = relationship("DepositRequest", back_populates="wallet", cascade="all, delete-orphan")
    withdrawals = relationship("WithdrawalRequest", back_populates="wallet", cascade="all, delete-orphan")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    reference: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DEPOSIT, WITHDRAWAL_LOCK, WITHDRAWAL_FINAL, WITHDRAWAL_REVERT, TRADE_BUY, TRADE_SELL, FEE
    direction: Mapped[str] = mapped_column(String(10), nullable=False)   # CREDIT, DEBIT
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="POSTED", nullable=False)  # POSTED, PENDING, REVERSED
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    wallet = relationship("Wallet", back_populates="ledger_entries")


class DepositRequest(Base):
    __tablename__ = "deposit_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR", nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    payment_provider: Mapped[str] = mapped_column(String(50), default="simulated_upi", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)  # PENDING, COMPLETED, FAILED
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    wallet = relationship("Wallet", back_populates="deposits")


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    bank_account_info: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING", nullable=False)  # PENDING, APPROVED, PROCESSED, REJECTED
    reference_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    wallet = relationship("Wallet", back_populates="withdrawals")
