import asyncio
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.redis import redis_service
from app.providers.market_data.validation import get_indian_market_status

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket Stream"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead_connections = set()
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead_connections.add(conn)
        for dead in dead_connections:
            self.active_connections.discard(dead)


ws_manager = ConnectionManager()


@router.websocket("/ws/market")
async def websocket_market_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    tick_queue = redis_service.fallback.subscribe_queue("market:ticks")
    candle_queue = redis_service.fallback.subscribe_queue("market:candles:1m")
    order_queue = redis_service.fallback.subscribe_queue("order:events")

    try:
        status_info = get_indian_market_status()
        # Send initial handshake with session status and mode
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to Indian Stock Market Realtime Stream (Paper Trading Mode)",
            "mode": "PAPER",
            "market_status": status_info.status,
            "exchange": "NSE"
        })

        while True:
            tick_task = asyncio.create_task(tick_queue.get())
            candle_task = asyncio.create_task(candle_queue.get())
            order_task = asyncio.create_task(order_queue.get())
            recv_task = asyncio.create_task(websocket.receive_text())

            done, pending = await asyncio.wait(
                [tick_task, candle_task, order_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            for completed_task in done:
                if completed_task == tick_task:
                    msg = completed_task.result()
                    parsed = json.loads(msg) if isinstance(msg, str) else msg
                    await websocket.send_json({
                        "type": "TICK",
                        "data": parsed
                    })
                elif completed_task == candle_task:
                    msg = completed_task.result()
                    parsed = json.loads(msg) if isinstance(msg, str) else msg
                    await websocket.send_json({
                        "type": "CANDLE_UPDATE",
                        "data": parsed
                    })
                elif completed_task == order_task:
                    msg = completed_task.result()
                    parsed = json.loads(msg) if isinstance(msg, str) else msg
                    await websocket.send_json({
                        "type": "ORDER_EVENT",
                        "data": parsed
                    })
                elif completed_task == recv_task:
                    client_msg = completed_task.result()
                    await websocket.send_json({"type": "PONG", "received": client_msg})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket client connection closed: {e}")
    finally:
        ws_manager.disconnect(websocket)
        redis_service.fallback.unsubscribe_queue("market:ticks", tick_queue)
        redis_service.fallback.unsubscribe_queue("market:candles:1m", candle_queue)
        redis_service.fallback.unsubscribe_queue("order:events", order_queue)
