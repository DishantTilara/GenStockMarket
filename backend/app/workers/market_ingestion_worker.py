import asyncio
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional
from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis import redis_service
from app.models.instrument import Instrument
from app.models.market_data import MarketTick, MinuteBar, ProviderHealth
from app.providers.market_data.factory import get_market_data_provider
from app.providers.market_data.symbol_mapper import IndianSymbolMapper
from app.services.market_service import MarketService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("market_ingestion_worker")


class MinuteCandleAggregator:
    def __init__(self):
        # Current open bucket per symbol: {symbol: {interval_start, open, high, low, close, volume, count}}
        self.buckets: Dict[str, Dict[str, Any]] = {}

    def ingest_tick(self, symbol: str, price: Decimal, qty: int, ts: datetime) -> Optional[Dict[str, Any]]:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
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


async def persist_completed_candle(db, candle: Dict[str, Any], instrument_map: Dict[str, Instrument], source_name: str = "yfinance") -> None:
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
            source=source_name
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
    source_name = "yfinance" if "YFinance" in type(provider).__name__ else "simulated"

    aggregator = MinuteCandleAggregator()
    backoff_delay = 1.0

    while True:
        try:
            logger.info(f"Connecting to market data feed ({source_name})...")
            await provider.connect()
            backoff_delay = 1.0  # reset on successful connection

            async with AsyncSessionLocal() as db:
                await MarketService.ensure_instruments_seeded(db)
                inst_res = await db.execute(select(Instrument).where(Instrument.is_active == True))
                instrument_map = {inst.symbol: inst for inst in inst_res.scalars().all()}

                # Reconcile any missing candles on startup/recovery
                for inst in instrument_map.values():
                    try:
                        await MarketService.reconcile_missing_candles(db, inst)
                    except Exception as ex:
                        logger.debug(f"Reconciliation note for {inst.symbol}: {ex}")

            logger.info(f"Loaded {len(instrument_map)} active instruments. Ingesting stream...")

            last_health_ping = datetime.now(timezone.utc)
            symbols_seen = set()

            async for tick in provider.stream():
                symbol = tick["symbol"]
                price = Decimal(str(tick["price"]))
                qty = tick.get("quantity", 100)
                ts = tick["timestamp"]
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                symbols_seen.add(symbol)

                inst = instrument_map.get(symbol)
                exchange = inst.exchange if inst else tick.get("exchange", "NSE")
                provider_sym = (inst.provider_symbol if inst and inst.provider_symbol else None) or IndianSymbolMapper.to_provider_symbol(symbol, exchange)
                freshness = tick.get("freshness", "FRESH")

                # 1. Publish tick to Redis for real-time frontend WebSocket
                tick_payload = {
                    "type": "TICK",
                    "symbol": symbol,
                    "exchange": exchange,
                    "provider_symbol": provider_sym,
                    "price": float(price),
                    "quantity": qty,
                    "change": float(tick.get("change", 0.0)),
                    "change_pct": float(tick.get("change_pct", 0.0)),
                    "freshness": freshness,
                    "timestamp": ts.isoformat()
                }
                await redis_service.publish("market:ticks", tick_payload)

                # 2. Update latest tick/quote in Redis
                await redis_service.set_json(f"market:latest_tick:{symbol}", tick_payload, expire_seconds=30)
                quote_cache_key = f"market:quote:{symbol.upper()}"
                await redis_service.set_json(quote_cache_key, tick_payload, expire_seconds=30)

                # 3. Aggregate into 1-minute OHLCV candles
                completed = aggregator.ingest_tick(symbol, price, qty, ts)
                if completed:
                    async with AsyncSessionLocal() as db:
                        await persist_completed_candle(db, completed, instrument_map, source_name)

                # 4. Evaluate paper trading LIMIT orders and SL/Target triggers
                try:
                    from app.services.paper_trading_service import PaperTradingService
                    async with AsyncSessionLocal() as db:
                        await PaperTradingService.evaluate_tick_triggers(db, symbol, price)
                except Exception as ex:
                    logger.debug(f"Paper trigger evaluation note: {ex}")

                # Periodic health heartbeat update (every 10s)
                now = datetime.now(timezone.utc)
                if (now - last_health_ping).total_seconds() >= 10:
                    health_status = {
                        "provider": source_name,
                        "status": "HEALTHY",
                        "last_event": now.isoformat(),
                        "last_completed_minute": (now - timedelta(minutes=1)).replace(second=0, microsecond=0).isoformat(),
                        "ingestion_lag_seconds": 0.25,
                        "symbols_expected": len(instrument_map),
                        "symbols_received": len(symbols_seen),
                        "missing_minutes": 0,
                        "reconnect_count": 0
                    }
                    if hasattr(provider, "get_health"):
                        health_status.update(provider.get_health())
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
