import hmac
import hashlib
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
import razorpay
from app.core.config import settings
from app.payments.provider import PaymentProvider

logger = logging.getLogger("payments.razorpay")


class RazorpayProvider(PaymentProvider):
    """
    Razorpay payment gateway provider operating strictly in TEST mode.
    Handles order creation, signature verification, and webhook authenticity checks.
    """

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID or "rzp_test_placeholder"
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET or "mock_secret_placeholder"
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET or ""
        self.mode = settings.RAZORPAY_MODE

        try:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
        except Exception as e:
            logger.warning(f"[RAZORPAY] Initialized with placeholder client: {e}")
            self.client = None

    def create_order(
        self,
        amount: Decimal,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Razorpay order. Amount in INR is converted to paise (integer).
        """
        amount_paise = int(amount * Decimal("100"))
        order_receipt = receipt or f"rcpt_{uuid.uuid4().hex[:12]}"
        order_data = {
            "amount": amount_paise,
            "currency": currency.upper(),
            "receipt": order_receipt,
            "notes": notes or {},
            "payment_capture": 1,
        }

        # Real call if valid key is configured, otherwise fallback to deterministic test mock
        if self.client and not self.key_id.startswith("rzp_test_placeholder"):
            try:
                res = self.client.order.create(data=order_data)
                logger.info(f"[RAZORPAY] Created order {res.get('id')} for amount ₹{amount}")
                return res
            except Exception as exc:
                logger.error(f"[RAZORPAY] Order creation failed: {exc}")
                raise exc
        else:
            # Deterministic test order for automated environments and offline testing
            test_order_id = f"order_{uuid.uuid4().hex[:14]}"
            logger.info(f"[RAZORPAY TEST MODE] Generated test order {test_order_id} for ₹{amount}")
            return {
                "id": test_order_id,
                "entity": "order",
                "amount": amount_paise,
                "amount_paid": 0,
                "amount_due": amount_paise,
                "currency": currency.upper(),
                "receipt": order_receipt,
                "status": "created",
                "attempts": 0,
                "notes": notes or {},
                "created_at": 1700000000,
            }

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verify Razorpay HMAC SHA256 payment signature.
        Formula: HMAC-SHA256(order_id + "|" + payment_id, key_secret)
        """
        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return False

        # In test simulation mode without key_secret, allow mock verification string
        if self.key_secret == "mock_secret_placeholder" and razorpay_signature.startswith("test_sig_"):
            return True

        try:
            msg = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
            generated_sig = hmac.new(
                self.key_secret.encode("utf-8"),
                msg,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(generated_sig, razorpay_signature)
        except Exception as exc:
            logger.error(f"[RAZORPAY] Signature verification error: {exc}")
            return False

    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature: str,
    ) -> bool:
        """
        Verify Razorpay Webhook HMAC SHA256 signature using RAZORPAY_WEBHOOK_SECRET.
        """
        if not self.webhook_secret or not signature:
            logger.warning("[RAZORPAY] Webhook verification skipped: secret or signature missing")
            return False

        try:
            generated_sig = hmac.new(
                self.webhook_secret.encode("utf-8"),
                body_bytes,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(generated_sig, signature)
        except Exception as exc:
            logger.error(f"[RAZORPAY] Webhook signature verification error: {exc}")
            return False
