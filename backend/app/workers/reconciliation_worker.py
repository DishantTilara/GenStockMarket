import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy import select, and_
from app.core.database import AsyncSessionLocal
from app.models.instrument import Instrument
from app.models.market_data import MinuteBar
from app.providers.market_data.factory import get_market_data_provider

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reconciliation_worker")


async def repair_symbol_gaps(db, inst: Instrument, provider) -> int:
    """Inspects minute candles in the last 4 hours and fills gaps."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    lookback = now - timedelta(hours=2)

    # Fetch existing minute bars in window
    res = await db.execute(
        select(MinuteBar.interval_start)
        .where(
            and_(
                MinuteBar.instrument_id == inst.id,
                MinuteBar.interval_start >= lookback,
                MinuteBar.interval_start < now
            )
        )
    )
    existing_timestamps = set(res.scalars().all())

    # Build expected minute set
    expected_timestamps = []
    curr = lookback
    while curr < now:
        expected_timestamps.append(curr)
        curr += timedelta(minutes=1)

    missing = [ts for ts in expected_timestamps if ts not in existing_timestamps]

    if not missing:
        return 0

    logger.info(f"Reconciliation: Detected {len(missing)} missing minute candles for {inst.symbol}. Backfilling...")

    # Fetch replacement bars from provider historical endpoint
    fetched_bars = await provider.get_minute_bars(inst.symbol, min(missing), max(missing) + timedelta(minutes=1))
    inserted_count = 0

    for bar_data in fetched_bars:
        bar_ts = bar_data["interval_start"]
        if bar_ts in missing:
            # Upsert
            new_bar = MinuteBar(
                instrument_id=inst.id,
                interval_start=bar_ts,
                open=bar_data["open"],
                high=bar_data["high"],
                low=bar_data["low"],
                close=bar_data["close"],
                volume=bar_data["volume"],
                source_timestamp=bar_data.get("source_timestamp", bar_ts),
                is_complete=True,
                quality="HIGH",
                source="reconciliation"
            )
            db.add(new_bar)
            inserted_count += 1

    if inserted_count > 0:
        await db.commit()
        logger.info(f"Reconciliation: Successfully backfilled {inserted_count} candles for {inst.symbol}")

    return inserted_count


async def run_reconciliation():
    logger.info("Starting Reconciliation Worker (Data Self-Healing Engine)...")
    provider = get_market_data_provider()

    while True:
        try:
            async with AsyncSessionLocal() as db:
                inst_res = await db.execute(select(Instrument).where(Instrument.is_active == True))
                instruments = inst_res.scalars().all()

                total_repaired = 0
                for inst in instruments:
                    repaired = await repair_symbol_gaps(db, inst, provider)
                    total_repaired += repaired

                if total_repaired > 0:
                    logger.info(f"Reconciliation run completed: {total_repaired} total missing bars recovered.")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in reconciliation worker: {e}")

        # Run reconciliation audit every 60 seconds
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(run_reconciliation())
