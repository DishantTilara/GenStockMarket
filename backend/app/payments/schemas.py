import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class CreatePaymentOrderRequest(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"), le=Decimal("1000000.00"), description="Deposit amount in INR (min ₹1, max ₹10,00,000)")
    currency: str = Field("INR", max_length=10)
    notes: Optional[Dict[str, Any]] = None


class PaymentOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    razorpay_order_id: str
    amount: Decimal
    currency: str
    status: str
    razorpay_key_id: str
    receipt: str
    payment_type: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentVerificationResponse(BaseModel):
    success: bool
    status: str
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    credited_amount: Decimal
    new_balance: Decimal
    message: str


class PaymentHistoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    razorpay_order_id: str
    razorpay_payment_id: Optional[str] = None
    amount: Decimal
    currency: str
    status: str
    payment_type: str
    provider: str
    receipt: str
    created_at: datetime
    completed_at: Optional[datetime] = None
