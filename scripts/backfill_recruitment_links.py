"""Backfill recruitment_event_id for all jobs."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import app.database.models  # noqa: F401
from sqlalchemy import select

from app.database.session import get_session_factory
from app.modules.jobs.models import Job
from app.modules.recruitments.linking import link_job_to_recruitment


async def main() -> None:
    factory = get_session_factory()
    async with factory() as db:
        rows = (await db.execute(select(Job))).scalars().all()
        linked = 0
        for job in rows:
            event = await link_job_to_recruitment(db, job)
            if event:
                linked += 1
        await db.commit()
        print(f"Linked {linked}/{len(rows)} jobs to recruitment_events.")


if __name__ == "__main__":
    asyncio.run(main())
