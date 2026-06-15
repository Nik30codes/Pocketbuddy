"""Redis client configuration and caching utilities."""

import json
from typing import Optional, Any

from app.core.config import settings

redis_client = None

try:
    from redis.asyncio import Redis
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    pass


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache."""
    if not redis_client:
        return None
    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        pass
    return None


async def cache_set(key: str, value: Any, ttl: int = 3600) -> None:
    """Set a value in cache with TTL (default 1 hour)."""
    if not redis_client:
        return
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
    except Exception:
        pass


async def cache_delete(key: str) -> None:
    """Delete a key from cache."""
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception:
        pass


async def cache_invalidate_pattern(pattern: str) -> None:
    """Invalidate all keys matching a pattern."""
    if not redis_client:
        return
    try:
        async for key in redis_client.scan_iter(match=pattern):
            await redis_client.delete(key)
    except Exception:
        pass
