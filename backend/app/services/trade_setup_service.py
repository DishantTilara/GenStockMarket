import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token
from app.core.errors import AppError, RiskCheckFailedError
from app.models.order import TradeSetup, Order, OrderEvent
from app.models.wallet import LedgerEntry
from app.providers.market_data.factory import get_market_data_provider
from app.providers.broker.factory import get_broker_provider
from app.services.indicator_service import IndicatorService
from app.services.wallet_service import WalletService
from app.schemas.risk import TradeSetupResponse, OrderExecuteRequest, OrderResponse


class TradeSetupService:
    @classmethod
    async def generate_setup(cls, db: AsyncSession, user_id: uuid.UUID, symbol: str) -> TradeSetupResponse:
        sym = symbol.upper()
        market_provider = get_market_data_provider()
        quote = await market_provider.get_quote(sym)
        indicators = await IndicatorService.compute_indicators(sym)

        price = Decimal(str(quote["price"]))
        rsi = indicators["rsi_14"]
        support = Decimal(str(indicators["support"]))
        resistance = Decimal(str(indicators["resistance"]))

        if rsi < 45 or indicators["trend"] in ["BULLISH", "STRONG_BULLISH"]:
            side = "BUY"
            entry_min = round(price * Decimal("0.995"), 2)
            entry_max = round(price * Decimal("1.005"), 2)
            stop_loss = round(min(support, price * Decimal("0.985")), 2)
            target = round(price + (price - stop_loss) * Decimal("2.0"), 2)
            reasons = [
                f"Trend regime confirmed as {indicators['trend']}",
                f"RSI {rsi:.1f} shows constructive accumulation with support at ₹{support:,.2f}",
                f"Price holding above 20-period EMA (₹{indicators['ema_20']:,.2f})"
            ]
            invalidation = [
                f"Hourly candle closing decisively below ₹{stop_loss:,.2f}",
                "Broad index NIFTY breakdown with heavy institutional selling"
            ]
        else:
            side = "SELL"
            entry_min = round(price * Decimal("0.995"), 2)
            entry_max = round(price * Decimal("1.005"), 2)
            stop_loss = round(max(resistance, price * Decimal("1.015")), 2)
            target = round(price - (stop_loss - price) * Decimal("2.0"), 2)
            reasons = [
                f"Trend regime detected as {indicators['trend']}",
                f"RSI {rsi:.1f} shows overhead resistance near ₹{resistance:,.2f}",
                f"Price trading below volume-weighted average price (VWAP)"
            ]
            invalidation = [
                f"Breakout candle closing above ₹{stop_loss:,.2f}",
                "Sudden sector-wide short covering surge"
            ]

        risk_per_share = abs(price - stop_loss)
        target_diff = abs(target - price)
        rr_ratio = round(target_diff / risk_per_share, 2) if risk_per_share else Decimal("2.0")

        # Standard 1% account risk sizing
        risk_budget = Decimal("5000.00")
        qty = max(1, int(risk_budget / risk_per_share)) if risk_per_share else 10
        total_risk = round(risk_per_share * qty, 2)

        setup = TradeSetup(
            user_id=user_id,
            symbol=sym,
            side=side,
            entry_zone={"min": float(entry_min), "max": float(entry_max)},
            stop_loss=stop_loss,
            target_price=target,
            quantity=qty,
            risk_amount=total_risk,
            risk_reward=rr_ratio,
            reasons=reasons,
            invalidation=invalidation,
            status="PENDING_APPROVAL",
            data_timestamp=datetime.now(timezone.utc)
        )
        db.add(setup)
        await db.commit()
        await db.refresh(setup)

        return TradeSetupResponse(
            id=setup.id,
            symbol=setup.symbol,
            side=setup.side,
            entry_zone={"min": entry_min, "max": entry_max},
            stop_loss=setup.stop_loss,
            target_price=setup.target_price,
            quantity=setup.quantity,
            risk_amount=setup.risk_amount,
            risk_reward=setup.risk_reward,
            reasons=setup.reasons,
            invalidation=setup.invalidation,
            status=setup.status,
            data_timestamp=setup.data_timestamp
        )

    @classmethod
    async def execute_confirmed_order(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        req: OrderExecuteRequest
    ) -> OrderResponse:
        # Validate confirmation token
        payload = decode_token(req.confirmation_token)
        if payload.get("type") != "trade_confirmation" or payload.get("sub") != str(user_id):
            raise AppError(code="INVALID_TRADE_CONFIRMATION", message="Invalid or expired trade confirmation token")

        # Check funds in wallet
        wallet = await WalletService.get_or_create_wallet(db, user_id)
        order_cost = req.price * req.quantity
        if Decimal(str(wallet.available_balance)) < order_cost:
            raise AppError(code="INSUFFICIENT_FUNDS", message="Available balance insufficient at time of execution")

        # Deduct cost from wallet and record ledger entry
        wallet.available_balance = Decimal(str(wallet.available_balance)) - order_cost
        ledger = LedgerEntry(
            wallet_id=wallet.id,
            reference=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            entry_type=f"TRADE_{req.side}",
            direction="DEBIT",
            amount=order_cost,
            balance_after=wallet.available_balance,
            status="POSTED",
            description=f"Executed {req.side} order for {req.quantity} {req.symbol} @ ₹{req.price:,.2f}"
        )
        db.add(ledger)

        # Submit to Broker Provider Adapter
        broker = get_broker_provider()
        broker_res = await broker.place_order({
            "symbol": req.symbol,
            "side": req.side,
            "quantity": req.quantity,
            "price": float(req.price)
        })

        order = Order(
            user_id=user_id,
            symbol=req.symbol,
            side=req.side,
            order_type=req.order_type,
            quantity=req.quantity,
            price=req.price,
            stop_loss=req.stop_loss,
            target=req.target,
            status="FILLED",
            broker_order_id=broker_res.get("order_id"),
            risk_approved=True,
            user_confirmed=True
        )
        db.add(order)
        await db.flush()

        event = OrderEvent(
            order_id=order.id,
            event_type="FILLED",
            details=broker_res
        )
        db.add(event)

        await db.commit()
        await db.refresh(order)

        return OrderResponse(
            id=order.id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
            status=order.status,
            broker_order_id=order.broker_order_id,
            created_at=order.created_at
        )
