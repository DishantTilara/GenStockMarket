import uuid
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.core.redis import redis_service
from app.models.instrument import Instrument
from app.models.market_data import MinuteBar, DailyBar, ProviderHealth
from app.providers.market_data.factory import get_market_data_provider
from app.providers.market_data.symbol_mapper import IndianSymbolMapper
from app.providers.market_data.validation import validate_candle

logger = logging.getLogger("market_service")


class MarketService:
    @staticmethod
    async def ensure_instruments_seeded(db: AsyncSession) -> List[Instrument]:
        """Ensure core Indian equities and benchmark indices are seeded with provider symbols."""
        provider = get_market_data_provider()
        catalog = await provider.get_instruments()

        existing_res = await db.execute(select(Instrument))
        existing = {inst.symbol: inst for inst in existing_res.scalars().all()}

        created = []
        for item in catalog:
            sym = item["symbol"]
            ex = item.get("exchange", "NSE")
            prov_sym = item.get("provider_symbol") or IndianSymbolMapper.to_provider_symbol(sym, ex)
            
            if sym not in existing:
                new_inst = Instrument(
                    symbol=sym,
                    name=item["name"],
                    exchange=ex,
                    segment=item.get("segment", "EQUITY"),
                    lot_size=item.get("lot_size", 1),
                    tick_size=Decimal(str(item.get("tick_size", 0.05))),
                    sector=item.get("sector", "General"),
                    provider_symbol=prov_sym,
                    is_active=True
                )
                db.add(new_inst)
                created.append(new_inst)
            else:
                # Update provider_symbol if missing
                inst_obj = existing[sym]
                if not inst_obj.provider_symbol:
                    inst_obj.provider_symbol = prov_sym

        if created or any(not inst.provider_symbol for inst in existing.values()):
            await db.commit()

        final_res = await db.execute(select(Instrument).where(Instrument.is_active == True))
        return list(final_res.scalars().all())

    @staticmethod
    async def search_instruments(db: AsyncSession, query: str) -> List[Dict[str, Any]]:
        """Search instruments by symbol or company name."""
        q = (query or "").strip().lower()
        if not q:
            # Return top active instruments
            stmt = select(Instrument).where(Instrument.is_active == True).limit(20)
            res = await db.execute(stmt)
            insts = res.scalars().all()
        else:
            stmt = select(Instrument).where(
                and_(
                    Instrument.is_active == True,
                    or_(
                        Instrument.symbol.ilike(f"%{q}%"),
                        Instrument.name.ilike(f"%{q}%"),
                        Instrument.sector.ilike(f"%{q}%")
                    )
                )
            ).limit(25)
            res = await db.execute(stmt)
            insts = res.scalars().all()

        results = []
        for inst in insts:
            results.append({
                "symbol": inst.symbol,
                "exchange": inst.exchange,
                "name": inst.name,
                "provider_symbol": inst.provider_symbol or IndianSymbolMapper.to_provider_symbol(inst.symbol, inst.exchange),
                "sector": inst.sector
            })
        return results

    @staticmethod
    async def get_quote(symbol: str) -> Dict[str, Any]:
        """Fetch validated quote with Redis cache."""
        canonical_sym, exchange = IndianSymbolMapper.to_canonical_symbol(symbol)
        cache_key = f"market:quote:{canonical_sym.upper()}"
        cached = await redis_service.get_json(cache_key)
        if cached:
            # Ensure Decimal fields are restored for domain consumers
            for k in ["price", "change", "change_pct", "open", "high", "low", "close", "prev_close"]:
                if k in cached and cached[k] is not None:
                    cached[k] = Decimal(str(cached[k]))
            if "timestamp" in cached and isinstance(cached["timestamp"], str):
                try:
                    cached["timestamp"] = datetime.fromisoformat(cached["timestamp"])
                except Exception:
                    pass
            return cached

        provider = get_market_data_provider()
        quote = await provider.get_quote(canonical_sym)
        
        # Prepare serializable dict for Redis cache with 3s TTL
        ts = quote["timestamp"]
        ts_iso = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
        serializable = {
            "symbol": quote["symbol"],
            "exchange": quote.get("exchange", exchange),
            "provider_symbol": quote.get("provider_symbol") or IndianSymbolMapper.to_provider_symbol(canonical_sym, exchange),
            "price": float(quote["price"]),
            "change": float(quote.get("change", 0.0)),
            "change_pct": float(quote.get("change_pct", 0.0)),
            "open": float(quote.get("open", quote["price"])),
            "high": float(quote.get("high", quote["price"])),
            "low": float(quote.get("low", quote["price"])),
            "close": float(quote.get("close", quote["price"])),
            "prev_close": float(quote.get("prev_close", quote["price"])),
            "volume": int(quote.get("volume", 0)),
            "timestamp": ts_iso,
            "freshness": quote.get("freshness", "FRESH"),
            "market_session": quote.get("market_session", "OPEN"),
            "quality": quote.get("quality", "HIGH")
        }
        await redis_service.set_json(cache_key, serializable, expire_seconds=3)
        return quote

    @staticmethod
    async def get_minute_bars(
        db: AsyncSession,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 200
    ) -> List[Dict[str, Any]]:
        """Retrieve 1-minute historical candlestick bars."""
        sym, _ = IndianSymbolMapper.to_canonical_symbol(symbol)
        inst_res = await db.execute(select(Instrument).where(Instrument.symbol == sym))
        inst = inst_res.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if not end_time:
            end_time = now
        if not start_time:
            start_time = end_time - timedelta(hours=4)

        if inst:
            bars_res = await db.execute(
                select(MinuteBar)
                .where(
                    and_(
                        MinuteBar.instrument_id == inst.id,
                        MinuteBar.interval_start >= start_time,
                        MinuteBar.interval_start <= end_time
                    )
                )
                .order_by(MinuteBar.interval_start.asc())
                .limit(limit)
            )
            db_bars = bars_res.scalars().all()
            if len(db_bars) >= 10:
                return [
                    {
                        "interval_start": b.interval_start,
                        "open": b.open,
                        "high": b.high,
                        "low": b.low,
                        "close": b.close,
                        "volume": b.volume,
                        "is_complete": b.is_complete,
                        "quality": b.quality
                    }
                    for b in db_bars
                ]

        # Fallback to provider if database has insufficient bars yet
        provider = get_market_data_provider()
        bars = await provider.get_minute_bars(sym, start_time, end_time)
        return bars[-limit:] if limit else bars

    @staticmethod
    async def get_candles(
        db: AsyncSession,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical candles for any supported timeframe (1m, 5m, 15m, 30m, 1h, 1D).
        Queries PostgreSQL AggregatedCandle/MinuteBar before falling back to provider.
        """
        sym, exchange = IndianSymbolMapper.to_canonical_symbol(symbol)
        tf = timeframe.lower().strip()
        
        # 1. If 1m, check database minute bars first
        if tf in ["1m", "1min"]:
            now = datetime.now(timezone.utc)
            start = now - timedelta(minutes=limit * 2)
            db_bars = await MarketService.get_minute_bars(db, sym, start_time=start, end_time=now, limit=limit)
            if len(db_bars) >= min(limit, 20):
                return db_bars

        # 2. Check AggregatedCandle table
        try:
            from app.models.market_data import AggregatedCandle
            candle_stmt = (
                select(AggregatedCandle)
                .where(
                    and_(
                        AggregatedCandle.symbol == sym,
                        AggregatedCandle.timeframe == tf
                    )
                )
                .order_by(AggregatedCandle.interval_start.desc())
                .limit(limit)
            )
            res = await db.execute(candle_stmt)
            cached_candles = res.scalars().all()
            if len(cached_candles) >= min(limit, 20):
                cached_candles.reverse()
                return [
                    {
                        "symbol": c.symbol,
                        "exchange": c.exchange,
                        "interval_start": c.interval_start,
                        "timestamp": c.interval_start,
                        "open": c.open,
                        "high": c.high,
                        "low": c.low,
                        "close": c.close,
                        "volume": c.volume,
                        "source": c.source,
                        "quality": c.quality,
                        "is_complete": c.is_complete
                    }
                    for c in cached_candles
                ]
        except Exception as e:
            logger.debug(f"AggregatedCandle cache check skipped: {e}")

        # 3. Query provider
        provider = get_market_data_provider()
        if hasattr(provider, "get_candles"):
            return await provider.get_candles(sym, timeframe=timeframe, limit=limit)
        
        # Fallback for simulated provider
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=min(limit, 90))
        return await provider.get_minute_bars(sym, start, now)

    @staticmethod
    async def reconcile_missing_candles(db: AsyncSession, instrument: Instrument) -> int:
        """
        Detect gaps in 1-minute historical data and reconcile missing candles from provider.
        Upserts missing bars to prevent duplicates.
        """
        now = datetime.now(timezone.utc)
        latest_res = await db.execute(
            select(MinuteBar)
            .where(MinuteBar.instrument_id == instrument.id)
            .order_by(MinuteBar.interval_start.desc())
            .limit(1)
        )
        latest_bar = latest_res.scalar_one_or_none()

        if not latest_bar:
            # First-time seed: fetch last 60 minutes
            start_recon = now - timedelta(hours=2)
        else:
            bar_time = latest_bar.interval_start
            if bar_time.tzinfo is None:
                bar_time = bar_time.replace(tzinfo=timezone.utc)
            gap_minutes = int((now - bar_time).total_seconds() / 60)
            if gap_minutes <= 1:
                return 0  # Up to date
            start_recon = bar_time + timedelta(minutes=1)

        provider = get_market_data_provider()
        try:
            fetched_bars = await provider.get_minute_bars(instrument.symbol, start_recon, now)
        except Exception as e:
            logger.warning(f"Reconciliation fetch failed for {instrument.symbol}: {e}")
            return 0

        reconciled_count = 0
        for b in fetched_bars:
            if isinstance(b, dict) and "symbol" not in b:
                b["symbol"] = instrument.symbol
            is_valid, _ = validate_candle(b)
            if not is_valid:
                continue

            interval_start = b["interval_start"]
            # Check existing to prevent duplicate constraint violation
            existing_check = await db.execute(
                select(MinuteBar).where(
                    and_(
                        MinuteBar.instrument_id == instrument.id,
                        MinuteBar.interval_start == interval_start
                    )
                )
            )
            if not existing_check.scalar_one_or_none():
                new_bar = MinuteBar(
                    instrument_id=instrument.id,
                    interval_start=interval_start,
                    open=Decimal(str(b["open"])),
                    high=Decimal(str(b["high"])),
                    low=Decimal(str(b["low"])),
                    close=Decimal(str(b["close"])),
                    volume=int(b["volume"]),
                    source_timestamp=interval_start + timedelta(seconds=59),
                    is_complete=True,
                    quality="HIGH",
                    source="reconciliation"
                )
                db.add(new_bar)
                reconciled_count += 1

        if reconciled_count > 0:
            await db.commit()
            logger.info(f"Reconciled {reconciled_count} missing minute bars for {instrument.symbol}")

        return reconciled_count

    @staticmethod
    async def get_market_health(db: AsyncSession) -> Dict[str, Any]:
        """Aggregate health metrics across market worker, Redis, and data provider."""
        health_cache = await redis_service.get_json("market:health")
        provider = get_market_data_provider()
        provider_metrics = provider.get_health() if hasattr(provider, "get_health") else {}

        if health_cache:
            if provider_metrics:
                health_cache.update(provider_metrics)
            return health_cache

        # Check DB ProviderHealth table
        res = await db.execute(select(ProviderHealth).order_by(ProviderHealth.updated_at.desc()).limit(1))
        record = res.scalar_one_or_none()

        now_iso = datetime.now(timezone.utc).isoformat()
        if record:
            health = {
                "provider": getattr(provider, "name", "yfinance" if "YFinance" in type(provider).__name__ else "simulated"),
                "status": "HEALTHY" if record.is_connected else "DOWN",
                "last_event": record.last_event_at.isoformat() if record.last_event_at else now_iso,
                "last_completed_minute": record.last_completed_minute.isoformat() if record.last_completed_minute else now_iso,
                "ingestion_lag_seconds": float(record.ingestion_lag_seconds),
                "symbols_expected": record.symbols_expected,
                "symbols_received": record.symbols_received,
                "missing_minutes": record.missing_minutes,
                "reconnect_count": record.reconnect_count,
            }
        else:
            health = {
                "provider": "yfinance" if "YFinance" in type(provider).__name__ else "simulated",
                "status": "HEALTHY",
                "last_event": now_iso,
                "last_completed_minute": now_iso,
                "ingestion_lag_seconds": 0.25,
                "symbols_expected": 16,
                "symbols_received": 16,
                "missing_minutes": 0,
                "reconnect_count": 0,
            }

        if provider_metrics:
            health.update(provider_metrics)

        await redis_service.set_json("market:health", health, expire_seconds=3)
        return health
