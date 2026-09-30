import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_access_token
from app.models.wallet import Wallet
from app.providers.market_data.factory import get_market_data_provider
from app.providers.broker.factory import get_broker_provider
from app.services.wallet_service import WalletService
from app.schemas.risk import RiskValidationRequest, RiskValidationResponse, RiskCheckItem


class RiskService:
    @classmethod
    async def validate_pre_flight(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        req: RiskValidationRequest
    ) -> RiskValidationResponse:
        checks: List[RiskCheckItem] = []
        market_provider = get_market_data_provider()
        broker_provider = get_broker_provider()

        # 1. Market Status Check
        status_info = await market_provider.market_status()
        # Allow SIMULATED environment or regular open
        market_ok = status_info["status"] in ["OPEN", "PRE_OPEN"] or settings.APP_ENV == "development"
        checks.append(RiskCheckItem(
            check_name="MARKET_SESSION_STATUS",
            passed=market_ok,
            message=f"Session is {status_info['status']} ({status_info['message']})"
        ))

        # 2. Quote Freshness Check
        quote = await market_provider.get_quote(req.symbol)
        quote_ts = quote["timestamp"]
        now = datetime.now(timezone.utc)
        age_seconds = (now - quote_ts).total_seconds() if quote_ts else 0
        freshness_ok = age_seconds <= 15.0  # reasonable threshold
        checks.append(RiskCheckItem(
            check_name="QUOTE_FRESHNESS",
            passed=freshness_ok,
            message=f"Quote age is {age_seconds:.1f}s (Threshold: <= 15s)"
        ))

        # 3. Available Funds Check
        wallet = await WalletService.get_or_create_wallet(db, user_id)
        order_value = req.price * req.quantity
        available = Decimal(str(wallet.available_balance))
        funds_ok = available >= order_value
        checks.append(RiskCheckItem(
            check_name="SUFFICIENT_AVAILABLE_FUNDS",
            passed=funds_ok,
            message=f"Order value ₹{order_value:,.2f} vs Available balance ₹{available:,.2f}"
        ))

        # 4. Maximum Order Value Cap
        max_order_val = Decimal(str(settings.MAX_ORDER_VALUE_INR))
        cap_ok = order_value <= max_order_val
        checks.append(RiskCheckItem(
            check_name="MAX_ORDER_VALUE_LIMIT",
            passed=cap_ok,
            message=f"Order value ₹{order_value:,.2f} <= Max allowed ₹{max_order_val:,.2f}"
        ))

        # 5. Stop Loss Validation
        sl_ok = True
        sl_msg = "Stop loss verified"
        if req.stop_loss is not None:
            if req.side == "BUY" and req.stop_loss >= req.price:
                sl_ok = False
                sl_msg = f"BUY stop loss ₹{req.stop_loss} must be below entry price ₹{req.price}"
            elif req.side == "SELL" and req.stop_loss <= req.price:
                sl_ok = False
                sl_msg = f"SELL stop loss ₹{req.stop_loss} must be above entry price ₹{req.price}"
        else:
            sl_ok = False
            sl_msg = "Stop loss is strictly mandatory under platform risk guidelines"
        checks.append(RiskCheckItem(
            check_name="STOP_LOSS_INTEGRITY",
            passed=sl_ok,
            message=sl_msg
        ))

        # 6. Broker Connection Health
        broker_conn = await broker_provider.connect()
        checks.append(RiskCheckItem(
            check_name="BROKER_GATEWAY_HEALTH",
            passed=broker_conn,
            message="Broker gateway adapter is healthy and accepting orders"
        ))

        all_passed = all(c.passed for c in checks)
        confirmation_token = None
        rejection_code = None
        rejection_reason = None

        if all_passed:
            # Generate short-lived user confirmation token (5 minutes validity)
            confirmation_token = create_access_token(
                subject=user_id,
                expires_delta=timedelta(minutes=5),
                claims={
                    "type": "trade_confirmation",
                    "symbol": req.symbol,
                    "side": req.side,
                    "quantity": req.quantity,
                    "price": str(req.price),
                    "stop_loss": str(req.stop_loss) if req.stop_loss else None
                }
            )
        else:
            failed_check = next(c for c in checks if not c.passed)
            rejection_code = failed_check.check_name
            rejection_reason = failed_check.message

        return RiskValidationResponse(
            approved=all_passed,
            rejection_code=rejection_code,
            rejection_reason=rejection_reason,
            checks=checks,
            confirmation_token=confirmation_token
        )
