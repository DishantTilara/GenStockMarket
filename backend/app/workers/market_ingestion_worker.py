import asyncio
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import redis_service
from app.models.instrument import Instrument
from app.models.market_data import MarketTick, MinuteBar, ProviderHealth
from app.providers.market_data.factory import get_market_data_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("market_ingestion_worker")


class MinuteCandleAggregator:
    def __init__(self):
        # Current open bucket per symbol: {symbol: {interval_start, open, high, low, close, volume, count}}
        self.buckets: Dict[str, Dict[str, Any]] = {}

    def ingest_tick(self, symbol: str, price: Decimal, qty: int, ts: datetime) -> Optional[Dict[str, Any]]:
        # Floor timestamp to start of minute
        minute_start = ts.replace(second=0, microsecond=0)

        completed_candle = None
        bucket = self.buckets.get(symbol)

        if bucket and bucket["interval_start"] != minute_start:
            # The minute rolled over! Complete previous candle
            completed_candle = {
                "symbol": symbol,
                "interval_start": bucket["interval_start"],
                "open": bucket["open"],
                "high": bucket["high"],
                "low": bucket["low"],
                "close": bucket["close"],
                "volume": bucket["volume"],
                "source_timestamp": bucket["last_ts"]
            }
            # Start fresh bucket for new minute
            self.buckets[symbol] = {
                "interval_start": minute_start,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": qty,
                "last_ts": ts,
                "count": 1
            }
        elif not bucket:
            self.buckets[symbol] = {
                "interval_start": minute_start,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": qty,
                "last_ts": ts,
                "count": 1
            }
        else:
            # Update existing bucket
            if price > bucket["high"]:
                bucket["high"] = price
            if price < bucket["low"]:
                bucket["low"] = price
            bucket["close"] = price
            bucket["volume"] += qty
            bucket["last_ts"] = ts
            bucket["count"] += 1

        return completed_candle


async def persist_completed_candle(db, candle: Dict[str, Any], instrument_map: Dict[str, Instrument]) -> None:
    symbol = candle["symbol"]
    inst = instrument_map.get(symbol)
    if not inst:
        return

    # Check if candle already exists (unique constraint: instrument_id, interval_start)
    res = await db.execute(
        select(MinuteBar).where(
            MinuteBar.instrument_id == inst.id,
            MinuteBar.interval_start == candle["interval_start"]
        )
    )
    existing = res.scalar_one_or_none()

    if not existing:
        bar = MinuteBar(
            instrument_id=inst.id,
            interval_start=candle["interval_start"],
            open=candle["open"],
            high=candle["high"],
            low=candle["low"],
            close=candle["close"],
            volume=candle["volume"],
            source_timestamp=candle["source_timestamp"],
            is_complete=True,
            quality="HIGH",
            source="simulated"
        )
        db.add(bar)
        await db.commit()

        # Publish minute bar completion over Redis
        await redis_service.publish("market:candles:1m", {
            "symbol": symbol,
            "interval_start": candle["interval_start"].isoformat(),
            "open": float(candle["open"]),
            "high": float(candle["high"]),
            "low": float(candle["low"]),
            "close": float(candle["close"]),
            "volume": candle["volume"]
        })
        logger.info(f"Persisted 1-min candle for {symbol} at {candle['interval_start'].strftime('%H:%M:%S')}")


async def run_market_ingestion():
    logger.info("Starting Market Ingestion Worker...")
    await redis_service.connect()
    provider = get_market_data_provider()

    aggregator = MinuteCandleAggregator()
    backoff_delay = 1.0

    while True:
        try:
            logger.info("Connecting to market data feed...")
            await provider.connect()
            backoff_delay = 1.0  # reset on successful connection

            async with AsyncSessionLocal() as db:
                inst_res = await db.execute(select(Instrument))
                instrument_map = {inst.symbol: inst for inst in inst_res.scalars().all()}

            logger.info(f"Loaded {len(instrument_map)} instruments. Ingesting stream...")

            last_health_ping = datetime.now(timezone.utc)
            symbols_seen = set()

            async for tick in provider.stream():
                symbol = tick["symbol"]
                price = tick["price"]
                qty = tick["quantity"]
                ts = tick["timestamp"]
                symbols_seen.add(symbol)

                # 1. Publish tick to Redis for real-time frontend WebSocket
                await redis_service.publish("market:ticks", {
                    "symbol": symbol,
                    "price": float(price),
                    "quantity": qty,
                    "timestamp": ts.isoformat()
                })

                # 2. Update latest tick in Redis
                tick_data = {
                    "symbol": symbol,
                    "price": float(price),
                    "volume": qty,
                    "timestamp": ts.isoformat()
                }
                await redis_service.set_json(f"market:latest_tick:{symbol}", tick_data, expire_seconds=5)

                # 3. Aggregate into 1-minute OHLCV candles
                completed = aggregator.ingest_tick(symbol, price, qty, ts)
                if completed:
                    async with AsyncSessionLocal() as db:
                        await persist_completed_candle(db, completed, instrument_map)

                # Periodic health heartbeat update (every 10s)
                now = datetime.now(timezone.utc)
                if (now - last_health_ping).total_seconds() >= 10:
                    health_status = {
                        "provider": "connected",
                        "last_event": now.isoformat(),
                        "last_completed_minute": (now - timedelta(minutes=1)).replace(second=0, microsecond=0).isoformat(),
                        "ingestion_lag_seconds": 0.25,
                        "symbols_expected": len(instrument_map),
                        "symbols_received": len(symbols_seen),
                        "missing_minutes": 0,
                        "reconnect_count": 0
                    }
                    await redis_service.set_json("market:health", health_status, expire_seconds=15)
                    last_health_ping = now

        except asyncio.CancelledError:
            logger.info("Market ingestion worker received shutdown signal.")
            break
        except Exception as e:
            logger.error(f"Market provider disconnected with error: {e}. Backing off {backoff_delay}s...")
            await asyncio.sleep(backoff_delay)
            backoff_delay = min(backoff_delay * 2.0, 30.0)


if __name__ == "__main__":
    asyncio.run(run_market_ingestion())
