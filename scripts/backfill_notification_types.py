"""Backfill jobs.notification_type from title/summary using the classifier."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from sqlalchemy import select

from app.database.session import get_session_factory
from app.modules.crawlers.classify import classify_notification
from app.modules.jobs.models import Job


async def main() -> None:
    factory = get_session_factory()
    async with factory() as db:
        rows = (await db.execute(select(Job))).scalars().all()
        updated = 0
        for job in rows:
            ntype = classify_notification(job.title, job.summary)
            if job.notification_type != ntype:
                job.notification_type = ntype
                updated += 1
        await db.commit()
        print(f"Scanned {len(rows)} jobs; updated notification_type on {updated}.")


if __name__ == "__main__":
    asyncio.run(main())
