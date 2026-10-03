from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Optional


class PaymentProvider(ABC):
    """Abstract interface for payment providers."""

    @abstractmethod
    def create_order(
        self,
        amount: Decimal,
        currency: str = "INR",
        receipt: str = "",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a payment order on the gateway."""
        pass

    @abstractmethod
    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify client-side checkout signature."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        body_bytes: bytes,
        signature: str,
    ) -> bool:
        """Verify asynchronous webhook signature."""
        pass
