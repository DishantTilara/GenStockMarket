import asyncio
import json
import logging
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.redis import redis_service

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
    queue = redis_service.fallback.subscribe_queue("market:ticks")

    try:
        # Send initial handshake
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Connected to Indian Stock Market Realtime Stream"
        })

        while True:
            # We await ticks from the pubsub queue or listen for client messages
            tick_task = asyncio.create_task(queue.get())
            recv_task = asyncio.create_task(websocket.receive_text())

            done, pending = await asyncio.wait(
                [tick_task, recv_task],
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
                elif completed_task == recv_task:
                    # Client incoming message (e.g. subscribe to specific symbol)
                    client_msg = completed_task.result()
                    # Acknowledge ping or custom subscription
                    await websocket.send_json({"type": "PONG", "received": client_msg})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        redis_service.fallback.unsubscribe_queue("market:ticks", queue)
    except Exception as e:
        logger.warning(f"WebSocket client connection closed: {e}")
        ws_manager.disconnect(websocket)
        redis_service.fallback.unsubscribe_queue("market:ticks", queue)
