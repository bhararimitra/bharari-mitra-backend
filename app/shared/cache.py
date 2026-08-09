"""Redis cache helper — optional; degrades to no-op when Redis is down."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_redis: aioredis.Redis | None = None
_redis_disabled: bool = False
_warned_once: bool = False


def _cache_enabled() -> bool:
    settings = get_settings()
    if not getattr(settings, "REDIS_ENABLED", True):
        return False
    return not _redis_disabled


def get_redis() -> aioredis.Redis | None:
    global _redis
    if not _cache_enabled():
        return None
    if _redis is None:
        settings = get_settings()
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
    return _redis


def _mark_unavailable(error: Exception) -> None:
    global _redis_disabled, _warned_once, _redis
    _redis_disabled = True
    _redis = None
    if not _warned_once:
        _warned_once = True
        logger.warning(
            "redis_unavailable",
            error=str(error),
            hint="Set REDIS_ENABLED=false or start Redis; cache disabled for this process",
        )


async def cache_get(key: str) -> Any | None:
    if not _cache_enabled():
        return None
    try:
        r = get_redis()
        if r is None:
            return None
        value = await r.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        _mark_unavailable(e)
    return None


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    if not _cache_enabled():
        return
    try:
        settings = get_settings()
        r = get_redis()
        if r is None:
            return
        await r.set(
            key,
            json.dumps(value, default=str),
            ex=ttl or settings.CACHE_TTL_SECONDS,
        )
    except Exception as e:
        _mark_unavailable(e)


async def cache_delete(key: str) -> None:
    if not _cache_enabled():
        return
    try:
        r = get_redis()
        if r is None:
            return
        await r.delete(key)
    except Exception as e:
        _mark_unavailable(e)


async def cache_clear_pattern(pattern: str) -> None:
    if not _cache_enabled():
        return
    try:
        r = get_redis()
        if r is None:
            return
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception as e:
        _mark_unavailable(e)
