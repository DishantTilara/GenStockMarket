import asyncio
import logging
from decimal import Decimal
from typing import Dict, Any
from app.core.redis import redis_service
from app.core.database import AsyncSessionLocal
from app.services.paper_trading_service import PaperTradingService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("paper_execution_worker")


async def run_paper_execution():
    """Worker that subscribes to incoming market ticks and evaluates pending LIMIT orders, Stop-Loss, and Targets."""
    logger.info("Starting Paper Trading Execution Worker...")
    await redis_service.connect()
    queue = redis_service.fallback.subscribe_queue("market:ticks")

    while True:
        try:
            msg = await queue.get()
            if isinstance(msg, dict):
                tick = msg
            else:
                import json
                tick = json.loads(msg)

            symbol = tick.get("symbol")
            price = Decimal(str(tick.get("price")))

            if symbol and price:
                async with AsyncSessionLocal() as db:
                    triggers = await PaperTradingService.evaluate_tick_triggers(db, symbol, price)
                    if triggers:
                        logger.info(f"Executed {len(triggers)} triggers for {symbol} @ ₹{price}: {triggers}")

        except asyncio.CancelledError:
            logger.info("Paper execution worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in paper execution worker: {e}")
            await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(run_paper_execution())
