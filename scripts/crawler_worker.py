"""Long-running background worker for BharariMitra crawlers.

Runs all crawlers on a schedule (default every 6 hours) and optionally
once at startup. Keep this process running separately from the API.

Usage:
    python scripts/crawler_worker.py
    python scripts/crawler_worker.py --once          # run batch once and exit
    python scripts/crawler_worker.py --no-startup    # skip immediate first run

Windows (background):
    .\\scripts\\start_crawler_worker.ps1
"""

from __future__ import annotations

import argparse
import os
import signal
import sys
from pathlib import Path

# Unbuffered logs when stdout is redirected to a file
os.environ.setdefault("PYTHONUNBUFFERED", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import asyncio

from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import get_engine
from app.modules.crawlers.scheduler import (
    run_all_crawlers,
    start_scheduler,
    stop_scheduler,
)

logger = get_logger(__name__)


async def _check_db() -> None:
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("crawler_worker_db_ok")


async def run_once() -> None:
    configure_logging()
    settings = get_settings()
    logger.info(
        "crawler_worker_once",
        database=settings.DATABASE_URL.split("@")[-1],
    )
    await _check_db()
    await run_all_crawlers()
    await get_engine().dispose()


async def run_forever(*, run_immediately: bool) -> None:
    configure_logging()
    settings = get_settings()
    logger.info(
        "crawler_worker_starting",
        database=settings.DATABASE_URL.split("@")[-1],
        interval_hours=settings.CRAWLER_INTERVAL_HOURS,
        run_on_startup=run_immediately,
    )
    await _check_db()

    start_scheduler(run_immediately=run_immediately)
    stop_event = asyncio.Event()

    def _handle_stop(*_args) -> None:
        logger.info("crawler_worker_stop_signal")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_stop)
        except NotImplementedError:
            # Windows: signal handlers limited; KeyboardInterrupt still works
            pass

    logger.info("crawler_worker_ready")
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        stop_scheduler()
        await get_engine().dispose()
        logger.info("crawler_worker_stopped")


def main() -> None:
    parser = argparse.ArgumentParser(description="BharariMitra crawler background worker")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run all crawlers once and exit (no long-lived scheduler)",
    )
    parser.add_argument(
        "--no-startup",
        action="store_true",
        help="Do not queue an immediate crawl on worker start",
    )
    args = parser.parse_args()

    if args.once:
        asyncio.run(run_once())
        return

    try:
        asyncio.run(run_forever(run_immediately=not args.no_startup))
    except KeyboardInterrupt:
        # Windows Ctrl+C
        stop_scheduler()


if __name__ == "__main__":
    main()
