import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.audit import log_audit_event
from app.core.errors import AppError
from app.models.user import User
from app.api.deps import get_current_user
from app.payments.service import PaymentService
from app.payments.schemas import (
    CreatePaymentOrderRequest,
    PaymentOrderResponse,
    VerifyPaymentRequest,
    PaymentVerificationResponse,
    PaymentHistoryItemResponse,
)

router = APIRouter(prefix="/payments", tags=["Payments (Razorpay TEST)"])
payment_service = PaymentService()


@router.post("/create-order", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_order(
    req: CreatePaymentOrderRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a Razorpay order in TEST mode for paper wallet funding.
    Returns checkout details including razorpay_order_id and public key_id.
    """
    order_dict = await payment_service.create_payment_order(
        db=db,
        user=user,
        amount=req.amount,
        currency=req.currency,
        notes=req.notes,
    )

    await log_audit_event(
        db,
        action="PAYMENT_ORDER_CREATED",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        resource_type="payment_order",
        resource_id=str(order_dict["id"]),
        details={
            "amount": float(req.amount),
            "currency": req.currency,
            "razorpay_order_id": order_dict["razorpay_order_id"],
        },
    )

    return order_dict


@router.post("/verify", response_model=PaymentVerificationResponse)
async def verify_payment(
    req: VerifyPaymentRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify the client-side Razorpay checkout signature and credit the user's paper wallet.
    Idempotent: Duplicate submissions will not double-credit.
    """
    res = await payment_service.verify_payment(
        db=db,
        user=user,
        razorpay_order_id=req.razorpay_order_id,
        razorpay_payment_id=req.razorpay_payment_id,
        razorpay_signature=req.razorpay_signature,
    )

    await log_audit_event(
        db,
        action="PAYMENT_VERIFIED",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        resource_type="payment_order",
        resource_id=req.razorpay_order_id,
        details={
            "razorpay_payment_id": req.razorpay_payment_id,
            "credited_amount": float(res["credited_amount"]),
            "new_balance": float(res["new_balance"]),
        },
    )

    return res


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Asynchronous server-to-server webhook endpoint from Razorpay.
    Verifies signature using RAZORPAY_WEBHOOK_SECRET and idempotently credits wallet.
    """
    body_bytes = await request.body()
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    res = await payment_service.process_webhook(
        db=db,
        body_bytes=body_bytes,
        signature=x_razorpay_signature or "",
        payload=payload,
    )
    return res


@router.get("", response_model=List[PaymentHistoryItemResponse])
async def get_payment_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full history of Razorpay deposit orders for the current user."""
    orders = await payment_service.get_payment_history(db, user.id)
    return orders


@router.get("/{payment_id}", response_model=PaymentHistoryItemResponse)
async def get_payment_by_id(
    payment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve details for a specific payment order."""
    order = await payment_service.get_payment_by_id(db, user.id, payment_id)
    if not order:
        raise HTTPException(status_code=404, detail="Payment order not found")
    return order
