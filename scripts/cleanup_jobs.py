"""Delete expired jobs (last_date older than the retention window).

Usage (from backend/):
    python scripts/cleanup_jobs.py --dry-run
    python scripts/cleanup_jobs.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import get_engine, get_session_factory
from app.modules.jobs.cleanup import cleanup_expired_jobs

logger = get_logger(__name__)


async def main(*, dry_run: bool) -> None:
    configure_logging()
    settings = get_settings()
    print(f"Database: {settings.DATABASE_URL.split('@')[-1]}")
    print(f"Retention: {settings.JOB_CLEANUP_RETENTION_DAYS} days after last_date")

    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    factory = get_session_factory()
    async with factory() as db:
        stats = await cleanup_expired_jobs(db, dry_run=dry_run)
        if not dry_run:
            await db.commit()

    verb = "would delete" if dry_run else "deleted"
    print(f"Cutoff last_date < {stats['cutoff']}")
    print(f"{verb}: {stats['deleted']}")
    print(f"{'would close' if dry_run else 'closed'}: {stats['closed']}")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up expired BharariMitra jobs")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count rows only; do not delete or close",
    )
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))
