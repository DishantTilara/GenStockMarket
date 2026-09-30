import asyncio
import json
import logging
from typing import Any, Optional, Dict
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Fallback cache & pubsub for local testing when Redis server is not running."""
    def __init__(self):
        self._store: Dict[str, str] = {}
        self._listeners: Dict[str, list] = {}

    async def get(self, key: str) -> Optional[str]:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._store[key] = value
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._store.pop(key, None) is not None else 0

    async def ping(self) -> bool:
        return True

    async def publish(self, channel: str, message: str) -> int:
        subscribers = self._listeners.get(channel, [])
        for queue in subscribers:
            await queue.put(message)
        return len(subscribers)

    def subscribe_queue(self, channel: str) -> asyncio.Queue:
        if channel not in self._listeners:
            self._listeners[channel] = []
        q = asyncio.Queue()
        self._listeners[channel].append(q)
        return q

    def unsubscribe_queue(self, channel: str, q: asyncio.Queue) -> None:
        if channel in self._listeners and q in self._listeners[channel]:
            self._listeners[channel].remove(q)


class RedisService:
    def __init__(self):
        self.client: Optional[aioredis.Redis] = None
        self.fallback = InMemoryCache()
        self._is_redis_available = False

    async def connect(self) -> None:
        if not settings.REDIS_ENABLED:
            logger.info("Redis disabled via configuration. Using in-memory fallback.")
            self._is_redis_available = False
            return

        try:
            self.client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
                socket_connect_timeout=2.0
            )
            await self.client.ping()
            self._is_redis_available = True
            logger.info("Connected to Redis successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis ({e}). Operating in resilient fallback mode.")
            self._is_redis_available = False

    async def disconnect(self) -> None:
        if self.client and self._is_redis_available:
            await self.client.close()

    async def ping(self) -> bool:
        if self._is_redis_available and self.client:
            try:
                return await self.client.ping()
            except Exception:
                return False
        return await self.fallback.ping()

    async def get_json(self, key: str) -> Optional[Any]:
        try:
            if self._is_redis_available and self.client:
                val = await self.client.get(key)
            else:
                val = await self.fallback.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error(f"Error getting JSON key {key}: {e}")
            return None

    async def set_json(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        try:
            serialized = json.dumps(value, default=str)
            if self._is_redis_available and self.client:
                return await self.client.set(key, serialized, ex=expire_seconds)
            else:
                return await self.fallback.set(key, serialized, ex=expire_seconds)
        except Exception as e:
            logger.error(f"Error setting JSON key {key}: {e}")
            return False

    async def publish(self, channel: str, message: Any) -> int:
        payload = json.dumps(message, default=str) if not isinstance(message, str) else message
        if self._is_redis_available and self.client:
            try:
                return await self.client.publish(channel, payload)
            except Exception as e:
                logger.error(f"Error publishing to Redis channel {channel}: {e}")
                return await self.fallback.publish(channel, payload)
        return await self.fallback.publish(channel, payload)


redis_service = RedisService()
