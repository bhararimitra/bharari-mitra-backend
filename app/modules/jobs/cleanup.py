"""Weekly expired-job cleanup — drop closed applications to keep the DB small.

A job is expired when ``last_date`` is set and is older than the retention
window (default 7 days after the apply deadline). Rows with no last_date are
left alone so undated notices are not deleted by guesswork.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.modules.jobs.repository import JobRepository

logger = get_logger(__name__)


def expired_cutoff(today: date | None = None, retention_days: int | None = None) -> date:
    """Jobs with last_date strictly before this date are deleted."""
    settings = get_settings()
    days = settings.JOB_CLEANUP_RETENTION_DAYS if retention_days is None else retention_days
    days = max(0, int(days))
    return (today or date.today()) - timedelta(days=days)


async def cleanup_expired_jobs(
    db: AsyncSession,
    *,
    today: date | None = None,
    retention_days: int | None = None,
    dry_run: bool = False,
) -> dict[str, int | str | bool]:
    today = today or date.today()
    cutoff = expired_cutoff(today, retention_days)
    repo = JobRepository(db)

    if dry_run:
        to_delete = await repo.count_expired(cutoff)
        to_close = await repo.count_past_deadline(today)
        logger.info(
            "expired_jobs_cleanup_dry_run",
            cutoff=str(cutoff),
            would_delete=to_delete,
            would_close=to_close,
        )
        return {
            "dry_run": True,
            "cutoff": cutoff.isoformat(),
            "deleted": to_delete,
            "closed": to_close,
        }

    deleted = await repo.delete_expired(cutoff)
    closed = await repo.close_past_deadline(today)
    logger.info(
        "expired_jobs_cleanup_ok",
        cutoff=str(cutoff),
        deleted=deleted,
        closed=closed,
    )
    return {
        "dry_run": False,
        "cutoff": cutoff.isoformat(),
        "deleted": deleted,
        "closed": closed,
    }


async def run_expired_job_cleanup() -> None:
    """Scheduler entrypoint — own DB session, commit on success."""
    from app.database.session import get_session_factory

    factory = get_session_factory()
    async with factory() as db:
        try:
            await cleanup_expired_jobs(db)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error("expired_jobs_cleanup_error", error=str(e))
            raise
