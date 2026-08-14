"""Ping IndexNow when a new job URL is published."""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("indexnow")

INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
SITE_HOST = "bhararimitra.in"


async def ping_job_url(slug: str) -> None:
    settings = get_settings()
    key = (settings.INDEXNOW_KEY or "").strip()
    if not key:
        return
    url = f"https://{SITE_HOST}/jobs/{slug}"
    payload = {
        "host": SITE_HOST,
        "key": key,
        "keyLocation": f"https://{SITE_HOST}/{key}.txt",
        "urlList": [url],
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(INDEXNOW_ENDPOINT, json=payload)
            logger.info("indexnow_ping", slug=slug, status=res.status_code)
    except Exception as exc:
        logger.warning("indexnow_failed", slug=slug, error=str(exc))
