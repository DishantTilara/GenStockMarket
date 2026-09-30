import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.redis import redis_service
from app.models.alert import Alert, AlertEvent
from app.providers.market_data.factory import get_market_data_provider
from app.services.indicator_service import IndicatorService


class AlertService:
    @staticmethod
    async def evaluate_alerts(db: AsyncSession) -> List[AlertEvent]:
        """Iterates through active alerts and triggers events when conditions are met."""
        active_alerts_res = await db.execute(select(Alert).where(Alert.is_active == True, Alert.is_triggered == False))
        alerts = active_alerts_res.scalars().all()
        triggered_events = []

        market_provider = get_market_data_provider()

        for alert in alerts:
            sym = alert.symbol.upper()
            quote = await market_provider.get_quote(sym)
            current_price = Decimal(str(quote["price"]))
            target = Decimal(str(alert.target_value))

            is_condition_met = False
            msg = ""

            if alert.condition_type == "PRICE_ABOVE" and current_price >= target:
                is_condition_met = True
                msg = f"{sym} crossed ABOVE target price ₹{target:,.2f} (Current: ₹{current_price:,.2f})"

            elif alert.condition_type == "PRICE_BELOW" and current_price <= target:
                is_condition_met = True
                msg = f"{sym} crossed BELOW target price ₹{target:,.2f} (Current: ₹{current_price:,.2f})"

            elif "RSI" in alert.condition_type:
                indicators = await IndicatorService.compute_indicators(sym)
                rsi = Decimal(str(indicators["rsi_14"]))
                if alert.condition_type == "RSI_OVERBOUGHT" and rsi >= target:
                    is_condition_met = True
                    msg = f"{sym} RSI reached {rsi:.1f} (Overbought threshold: {target})"
                elif alert.condition_type == "RSI_OVERSOLD" and rsi <= target:
                    is_condition_met = True
                    msg = f"{sym} RSI dipped to {rsi:.1f} (Oversold threshold: {target})"

            elif alert.condition_type == "VOLUME_SPIKE":
                indicators = await IndicatorService.compute_indicators(sym)
                if indicators["volume_spike"]:
                    is_condition_met = True
                    msg = f"{sym} volume surge detected (Volume: {quote['volume']:,})"

            if is_condition_met:
                alert.is_triggered = True
                event = AlertEvent(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    symbol=sym,
                    triggered_price=current_price,
                    message=msg,
                    triggered_at=datetime.now(timezone.utc)
                )
                db.add(event)
                triggered_events.append(event)

                # Broadcast alert event through Redis PubSub
                await redis_service.publish(f"user:{alert.user_id}:alerts", {
                    "alert_id": str(alert.id),
                    "symbol": sym,
                    "price": float(current_price),
                    "message": msg,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        if triggered_events:
            await db.commit()

        return triggered_events
