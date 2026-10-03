import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.config import settings
from app.core.errors import AppError, ResourceNotFoundError
from app.models.payment import PaymentOrder
from app.models.wallet import Wallet, LedgerEntry
from app.models.user import User
from app.payments.razorpay_provider import RazorpayProvider
from app.services.wallet_service import WalletService
from app.core.redis import redis_service

logger = logging.getLogger("payments.service")


class PaymentService:
    """
    Authoritative service for managing Razorpay TEST payment orders,
    signature verification, idempotency protection, and wallet ledger credits.
    """

    def __init__(self, provider: Optional[RazorpayProvider] = None):
        self.provider = provider or RazorpayProvider()

    async def create_payment_order(
        self,
        db: AsyncSession,
        user: User,
        amount: Decimal,
        currency: str = "INR",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new payment order for wallet funding in Razorpay TEST mode.
        """
        if amount <= Decimal("0.00"):
            raise AppError(code="INVALID_AMOUNT", message="Deposit amount must be greater than zero", status_code=400)

        receipt = f"rcpt_{uuid.uuid4().hex[:12]}"
        order_notes = notes or {}
        order_notes["user_id"] = str(user.id)
        order_notes["email"] = user.email

        # 1. Call Razorpay provider
        rzp_order = self.provider.create_order(
            amount=amount,
            currency=currency,
            receipt=receipt,
            notes=order_notes,
        )

        rzp_order_id = rzp_order["id"]

        # 2. Persist in payment_orders
        payment_order = PaymentOrder(
            user_id=user.id,
            razorpay_order_id=rzp_order_id,
            amount=amount,
            currency=currency.upper(),
            status="CREATED",
            payment_type="WALLET_DEPOSIT",
            provider="razorpay",
            receipt=receipt,
            notes=order_notes,
        )
        db.add(payment_order)
        await db.commit()
        await db.refresh(payment_order)

        logger.info(f"[PAYMENT] Created PaymentOrder {payment_order.id} for user {user.id} (Razorpay: {rzp_order_id})")

        return {
            "id": payment_order.id,
            "razorpay_order_id": rzp_order_id,
            "amount": payment_order.amount,
            "currency": payment_order.currency,
            "status": payment_order.status,
            "razorpay_key_id": self.provider.key_id,
            "receipt": receipt,
            "payment_type": payment_order.payment_type,
            "created_at": payment_order.created_at,
        }

    async def verify_payment(
        self,
        db: AsyncSession,
        user: User,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Dict[str, Any]:
        """
        Verify Razorpay signature and credit the paper wallet exactly once.
        Ensures idempotent processing and atomic ledger creation.
        """
        stmt = select(PaymentOrder).where(PaymentOrder.razorpay_order_id == razorpay_order_id)
        res = await db.execute(stmt)
        payment_order = res.scalar_one_or_none()

        if not payment_order:
            raise ResourceNotFoundError("PaymentOrder", razorpay_order_id)

        if payment_order.user_id != user.id:
            raise AppError(code="UNAUTHORIZED", message="Payment order does not belong to the authenticated user", status_code=403)

        # Idempotency check: Already processed
        if payment_order.status == "PAID":
            logger.info(f"[PAYMENT] Payment order {razorpay_order_id} already marked PAID. Idempotently returning success.")
            wallet = await WalletService.get_or_create_wallet(db, user.id)
            return {
                "success": True,
                "status": "PAID",
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": payment_order.razorpay_payment_id,
                "credited_amount": payment_order.amount,
                "new_balance": Decimal(str(wallet.available_balance)),
                "message": "Payment was already verified and credited",
            }

        # Verify HMAC-SHA256 signature
        is_valid = self.provider.verify_payment_signature(
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            razorpay_signature=razorpay_signature,
        )

        if not is_valid:
            payment_order.status = "FAILED"
            await db.commit()
            logger.warning(f"[PAYMENT] Signature verification failed for order {razorpay_order_id}")
            raise AppError(code="INVALID_PAYMENT_SIGNATURE", message="Payment signature verification failed", status_code=400)

        # Check for duplicate payment ID
        dup_check = await db.execute(
            select(PaymentOrder).where(
                and_(
                    PaymentOrder.razorpay_payment_id == razorpay_payment_id,
                    PaymentOrder.id != payment_order.id,
                )
            )
        )
        if dup_check.scalar_one_or_none():
            logger.error(f"[PAYMENT] Duplicate payment ID {razorpay_payment_id} detected!")
            raise AppError(code="DUPLICATE_PAYMENT", message="Payment ID has already been credited", status_code=400)

        # Mark PAID & update completed_at
        now = datetime.now(timezone.utc)
        payment_order.status = "PAID"
        payment_order.razorpay_payment_id = razorpay_payment_id
        payment_order.completed_at = now

        # Credit wallet and record immutable ledger entry
        wallet = await WalletService.get_or_create_wallet(db, user.id)
        current_bal = Decimal(str(wallet.available_balance))
        new_balance = current_bal + payment_order.amount
        wallet.available_balance = new_balance

        ledger_entry = LedgerEntry(
            wallet_id=wallet.id,
            reference=f"RZP-{razorpay_payment_id}",
            entry_type="DEPOSIT",
            direction="CREDIT",
            amount=payment_order.amount,
            balance_after=new_balance,
            status="POSTED",
            description=f"Razorpay TEST Deposit (Order: {razorpay_order_id}, Payment: {razorpay_payment_id})",
            metadata_json={
                "provider": "razorpay",
                "mode": "test",
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "receipt": payment_order.receipt,
            },
            created_at=now,
        )
        db.add(ledger_entry)

        await db.commit()
        await db.refresh(wallet)
        await db.refresh(payment_order)

        logger.info(f"[PAYMENT SUCCESS] Credited ₹{payment_order.amount} to user {user.id}. New Balance: ₹{new_balance}")

        # Real-time event publishing
        await redis_service.publish(
            "wallet:events",
            {
                "type": "WALLET_DEPOSIT",
                "user_id": str(user.id),
                "amount": float(payment_order.amount),
                "new_balance": float(new_balance),
                "reference": f"RZP-{razorpay_payment_id}",
            },
        )

        return {
            "success": True,
            "status": "PAID",
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "credited_amount": payment_order.amount,
            "new_balance": new_balance,
            "message": "Payment verified and wallet credited successfully",
        }

    async def process_webhook(
        self,
        db: AsyncSession,
        body_bytes: bytes,
        signature: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle asynchronous webhook events from Razorpay securely and idempotently.
        """
        if not self.provider.verify_webhook_signature(body_bytes, signature):
            logger.warning("[RAZORPAY WEBHOOK] Invalid webhook signature")
            raise AppError(code="INVALID_WEBHOOK_SIGNATURE", message="Invalid webhook signature", status_code=400)

        event = payload.get("event")
        logger.info(f"[RAZORPAY WEBHOOK] Received event: {event}")

        if event in ["payment.captured", "order.paid"]:
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            payment_id = payment_entity.get("id")

            if order_id and payment_id:
                stmt = select(PaymentOrder).where(PaymentOrder.razorpay_order_id == order_id)
                res = await db.execute(stmt)
                payment_order = res.scalar_one_or_none()

                if payment_order and payment_order.status != "PAID":
                    user = await db.get(User, payment_order.user_id)
                    if user:
                        return await self.verify_payment(
                            db=db,
                            user=user,
                            razorpay_order_id=order_id,
                            razorpay_payment_id=payment_id,
                            razorpay_signature="webhook_verified",
                        )

        return {"status": "ignored_or_already_processed"}

    async def get_payment_history(self, db: AsyncSession, user_id: uuid.UUID) -> List[PaymentOrder]:
        """Retrieve historical payment orders for a user."""
        stmt = (
            select(PaymentOrder)
            .where(PaymentOrder.user_id == user_id)
            .order_by(PaymentOrder.created_at.desc())
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_payment_by_id(self, db: AsyncSession, user_id: uuid.UUID, payment_id: uuid.UUID) -> Optional[PaymentOrder]:
        """Retrieve a single payment order by UUID."""
        stmt = select(PaymentOrder).where(
            and_(PaymentOrder.id == payment_id, PaymentOrder.user_id == user_id)
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
