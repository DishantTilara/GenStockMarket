import uuid
import logging
from typing import Dict, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderEvent
from app.core.audit import log_audit_event

logger = logging.getLogger("order_state_machine")


class OrderStateMachine:
    """
    Deterministic Order State Machine.
    Enforces strict lifecycle transitions and logs every state event in order_events.
    """

    # Complete 16 deterministic order states
    CREATED = "CREATED"
    RISK_PENDING = "RISK_PENDING"
    RISK_APPROVED = "RISK_APPROVED"
    USER_PENDING = "USER_PENDING"
    USER_APPROVED = "USER_APPROVED"
    SUBMITTED = "SUBMITTED"
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    MODIFY_PENDING = "MODIFY_PENDING"
    CANCEL_PENDING = "CANCEL_PENDING"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"

    # Strict transition graph
    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        CREATED: {RISK_PENDING, REJECTED, CANCELLED},
        RISK_PENDING: {RISK_APPROVED, REJECTED},
        RISK_APPROVED: {USER_PENDING, USER_APPROVED, SUBMITTED, CANCELLED},
        USER_PENDING: {USER_APPROVED, CANCELLED, EXPIRED},
        USER_APPROVED: {SUBMITTED, CANCELLED},
        SUBMITTED: {OPEN, FILLED, PARTIALLY_FILLED, REJECTED, RECONCILIATION_REQUIRED},
        OPEN: {PARTIALLY_FILLED, FILLED, MODIFY_PENDING, CANCEL_PENDING, CANCELLED, EXPIRED, RECONCILIATION_REQUIRED},
        PARTIALLY_FILLED: {PARTIALLY_FILLED, FILLED, MODIFY_PENDING, CANCEL_PENDING, CANCELLED, RECONCILIATION_REQUIRED},
        MODIFY_PENDING: {OPEN, PARTIALLY_FILLED, RECONCILIATION_REQUIRED},
        CANCEL_PENDING: {CANCELLED, FILLED, RECONCILIATION_REQUIRED},
        FILLED: {RECONCILIATION_REQUIRED},
        CANCELLED: {RECONCILIATION_REQUIRED},
        REJECTED: {RECONCILIATION_REQUIRED},
        EXPIRED: {RECONCILIATION_REQUIRED},
        UNKNOWN: {OPEN, FILLED, CANCELLED, REJECTED, RECONCILIATION_REQUIRED},
        RECONCILIATION_REQUIRED: {OPEN, PARTIALLY_FILLED, FILLED, CANCELLED, REJECTED}
    }

    @classmethod
    def is_transition_valid(cls, current_status: str, target_status: str) -> bool:
        cur = current_status.upper()
        tgt = target_status.upper()
        if cur == tgt:
            return True
        allowed = cls.ALLOWED_TRANSITIONS.get(cur, set())
        return tgt in allowed

    @classmethod
    async def transition(
        cls,
        db: AsyncSession,
        order: Order,
        target_status: str,
        details: Dict[str, Any] = None,
        is_reconciliation: bool = False
    ) -> Order:
        """
        Atomically transition order state and record OrderEvent.
        Raises ValueError if transition is invalid and not an explicit reconciliation correction.
        """
        current_status = order.status.upper()
        target = target_status.upper()

        if not is_reconciliation and not cls.is_transition_valid(current_status, target):
            err_msg = f"Illegal order state transition from '{current_status}' to '{target}'"
            logger.error(f"[ORDER STATE MACHINE] {err_msg} for order {order.id}")
            raise ValueError(err_msg)

        order.status = target
        order.updated_at = order.updated_at  # will be handled on commit

        # Record OrderEvent
        event_details = details or {}
        if is_reconciliation:
            event_details["is_reconciliation"] = True
            event_details["prior_state"] = current_status

        evt = OrderEvent(
            order_id=order.id,
            event_type=target,
            details=event_details
        )
        db.add(evt)
        await db.commit()
        await db.refresh(order)

        logger.info(f"[ORDER STATE MACHINE] Order {order.id} transitioned from {current_status} -> {target}")
        return order
