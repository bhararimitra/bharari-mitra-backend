"""Fill jobs.last_date from title/summary when crawlers left it empty."""

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
from app.modules.crawlers.base import BaseCrawler
from app.modules.crawlers.dates import infer_last_date
from app.modules.jobs.models import Job


class _DateParser(BaseCrawler):
    name = "last_date_backfill"
    source_url = "https://bhararimitra.in"

    async def fetch(self):
        return ""

    async def parse(self, raw):
        return []


async def main() -> None:
    factory = get_session_factory()
    async with factory() as db:
        parser = _DateParser(db)
        rows = (await db.execute(select(Job).where(Job.last_date.is_(None)))).scalars().all()
        updated = 0
        for job in rows:
            inferred = infer_last_date(f"{job.title} {job.summary or ''}")
            if not inferred:
                continue
            parsed = await parser._parse_date(inferred)
            if parsed is None:
                continue
            job.last_date = parsed
            updated += 1
        await db.commit()
        print(f"Scanned {len(rows)} jobs without last_date; filled {updated}.")


if __name__ == "__main__":
    asyncio.run(main())
