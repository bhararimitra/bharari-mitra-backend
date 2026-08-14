"""Reclassify jobs.notification_type from title/summary using the crawler classifier.

Does NOT delete rows or change slugs. Default is dry-run (no writes).

Usage (from backend/):
    python scripts/backfill_notification_types.py
    python scripts/backfill_notification_types.py --apply
    python scripts/backfill_notification_types.py --limit 50
    python scripts/backfill_notification_types.py --apply --limit 50

Logic (per row, not raw SQL — classification is regex in Python):

    SELECT id, slug, title, summary, notification_type FROM jobs;
    new_type = classify_notification(title, summary)
    if new_type != notification_type:
        UPDATE jobs SET notification_type = new_type WHERE id = ...
        -- slug unchanged

Public /api/v1/jobs still returns job + advertisement only (recruitment_only).
Rows moved to notice/hall_ticket/result/etc. leave the Jobs listing and appear
on the matching feed.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from sqlalchemy import func, select

from app.database.session import get_session_factory
from app.modules.crawlers.classify import classify_notification
from app.modules.jobs.models import Job, NotificationType


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit notification_type updates. Without this flag, only print a dry-run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max rows to UPDATE (0 = all mismatches). Dry-run still scans all rows.",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=25,
        help="How many mismatch examples to print.",
    )
    return parser.parse_args()


async def _counts(db) -> dict[str, int]:
    rows = (
        await db.execute(
            select(Job.notification_type, func.count(Job.id)).group_by(Job.notification_type)
        )
    ).all()
    return {str(ntype.value if hasattr(ntype, "value") else ntype): int(n) for ntype, n in rows}


async def main() -> None:
    args = _parse_args()
    factory = get_session_factory()
    async with factory() as db:
        before = await _counts(db)
        print("BEFORE counts:", dict(sorted(before.items())))

        jobs = (await db.execute(select(Job))).scalars().all()
        mismatches: list[tuple[Job, NotificationType]] = []
        for job in jobs:
            ntype = classify_notification(job.title, job.summary)
            if job.notification_type != ntype:
                mismatches.append((job, ntype))

        by_transition = Counter(
            f"{job.notification_type.value}->{ntype.value}" for job, ntype in mismatches
        )
        print(f"Scanned {len(jobs)} rows; {len(mismatches)} would change notification_type.")
        print("Transitions:", dict(sorted(by_transition.items())))
        print("Sample (slug | from -> to | title):")
        for job, ntype in mismatches[: max(args.sample, 0)]:
            title = (job.title or "").replace("\n", " ")[:90]
            print(f"  {job.slug} | {job.notification_type.value}->{ntype.value} | {title}")

        if not args.apply:
            print("DRY-RUN: no database writes. Re-run with --apply to commit.")
            return

        to_update = mismatches if args.limit <= 0 else mismatches[: args.limit]
        for job, ntype in to_update:
            job.notification_type = ntype
        await db.commit()
        after = await _counts(db)
        print(f"APPLIED: updated {len(to_update)} rows (slugs unchanged).")
        print("AFTER counts:", dict(sorted(after.items())))


if __name__ == "__main__":
    asyncio.run(main())
