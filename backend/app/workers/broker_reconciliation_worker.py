import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.core.database import async_session_factory
from app.models.user import User
from app.services.broker_reconciliation_service import BrokerReconciliationService
from app.core.config import settings

logger = logging.getLogger("broker_reconciliation_worker")


class BrokerReconciliationWorker:
    """
    Background worker performing periodic reconciliation between broker gateway and PostgreSQL.
    """

    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self._running = False
        self._task: asyncio.Task = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"[RECONCILIATION WORKER] Started with interval {self.interval_seconds}s")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[RECONCILIATION WORKER] Stopped")

    async def _run_loop(self):
        while self._running:
            try:
                await self.reconcile_all_active_users()
            except Exception as e:
                logger.error(f"[RECONCILIATION WORKER] Error during reconciliation cycle: {e}")
            await asyncio.sleep(self.interval_seconds)

    async def reconcile_all_active_users(self):
        async with async_session_factory() as db:
            users_res = await db.execute(select(User).where(User.is_active == True))
            users = users_res.scalars().all()
            for user in users:
                try:
                    res = await BrokerReconciliationService.reconcile_account(db, user.id, auto_correct=True)
                    if res["discrepancies_detected"] > 0:
                        logger.warning(
                            f"[RECONCILIATION WORKER] User {user.id} has {res['discrepancies_detected']} discrepancies "
                            f"({res['corrections_applied']} corrected)"
                        )
                except Exception as ex:
                    logger.error(f"[RECONCILIATION WORKER] Failed for user {user.id}: {ex}")


reconciliation_worker = BrokerReconciliationWorker(interval_seconds=60)
