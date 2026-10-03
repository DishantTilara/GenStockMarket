import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    razorpay_order_id = Column(String(100), unique=True, nullable=False, index=True)
    razorpay_payment_id = Column(String(100), unique=True, nullable=True, index=True)
    amount = Column(Numeric(20, 2), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    status = Column(String(30), default="CREATED", nullable=False, index=True)  # CREATED, PENDING, PAID, FAILED, CANCELLED, REFUNDED
    payment_type = Column(String(50), default="WALLET_DEPOSIT", nullable=False)
    provider = Column(String(50), default="razorpay", nullable=False)
    receipt = Column(String(100), nullable=False, index=True)
    notes = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="payment_orders")
