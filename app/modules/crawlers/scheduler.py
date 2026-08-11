"""APScheduler setup — background crawler jobs.

Use either:
  1. Dedicated worker: `python scripts/crawler_worker.py`
  2. In-API scheduler when ENABLE_API_SCHEDULER=true
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
_scheduler: AsyncIOScheduler | None = None

CRAWLER_PATHS: list[str] = [
    # Maharashtra — core
    "app.modules.crawlers.nhm.NhmCrawler",
    "app.modules.crawlers.police.PoliceCrawler",
    "app.modules.crawlers.msrtc.MsrtcCrawler",
    "app.modules.crawlers.mjp.MjpCrawler",
    "app.modules.crawlers.pavitra.PavitraCrawler",
    "app.modules.crawlers.dmer.DmerCrawler",
    "app.modules.crawlers.mo_recruitment.MoRecruitmentCrawler",
    "app.modules.crawlers.arogya.ArogyaCrawler",
    "app.modules.crawlers.wcd.WcdCrawler",
    "app.modules.crawlers.maharashtra_gov.MaharashtraGovCrawler",
    # Maharashtra — batch 2 departments / PSUs
    "app.modules.crawlers.mh_batch2.MsedclCrawler",
    "app.modules.crawlers.mh_batch2.MahagencoCrawler",
    "app.modules.crawlers.mh_batch2.MahatranscoCrawler",
    "app.modules.crawlers.mh_batch2.MahametroCrawler",
    "app.modules.crawlers.mh_batch2.MmrdaCrawler",
    "app.modules.crawlers.mh_batch2.MidcCrawler",
    "app.modules.crawlers.mh_batch2.PwdCrawler",
    "app.modules.crawlers.mh_batch2.WrdCrawler",
    "app.modules.crawlers.mh_batch2.AgricultureCrawler",
    "app.modules.crawlers.mh_batch2.TribalCrawler",
    "app.modules.crawlers.mh_batch2.SjsaCrawler",
    "app.modules.crawlers.mh_batch2.HomeDeptCrawler",
    "app.modules.crawlers.mh_batch2.PrisonsCrawler",
    "app.modules.crawlers.mh_batch2.CidcoCrawler",
    "app.modules.crawlers.mh_batch2.EducationDeptCrawler",
    "app.modules.crawlers.mh_batch2.MuhsCrawler",
    "app.modules.crawlers.mh_batch2.MumbaiUniversityCrawler",
    "app.modules.crawlers.mh_batch2.SppuCrawler",
    "app.modules.crawlers.mh_batch2.PcmcCrawler",
    "app.modules.crawlers.mh_batch2.PmcCrawler",
    # Maharashtra — batch 3 remaining
    "app.modules.crawlers.mh_batch3.MahaForestCrawler",
    "app.modules.crawlers.mh_batch3.AnimalHusbandryCrawler",
    "app.modules.crawlers.mh_batch3.HigherEducationCrawler",
    "app.modules.crawlers.mh_batch3.DmerOrgCrawler",
    "app.modules.crawlers.mh_batch3.MahaSwayamCrawler",
    "app.modules.crawlers.mh_batch3.MahaOnlineCrawler",
    "app.modules.crawlers.mh_batch3.SetMaharashtraCrawler",
    "app.modules.crawlers.mh_batch3.RtmnuCrawler",
    "app.modules.crawlers.mh_batch3.BamuCrawler",
    "app.modules.crawlers.mh_batch3.SgbauCrawler",
    "app.modules.crawlers.mh_batch3.ShivajiUniversityCrawler",
    "app.modules.crawlers.mh_batch3.NmcNagpurCrawler",
    "app.modules.crawlers.mh_batch3.BestUndertakingCrawler",
    "app.modules.crawlers.mh_batch3.MswcCrawler",
    "app.modules.crawlers.districts.DistrictCollectorsCrawler",
    "app.modules.crawlers.mpsc.MpscCrawler",
    # Central
    "app.modules.crawlers.ssc.SscCrawler",
    "app.modules.crawlers.upsc.UpscCrawler",
    "app.modules.crawlers.ibps.IbpsCrawler",
    "app.modules.crawlers.central_batch1.RrbNationalCrawler",
    "app.modules.crawlers.central_batch1.RrcCrCrawler",
    "app.modules.crawlers.central_batch1.RailwayBoardCrawler",
    "app.modules.crawlers.central_batch1.IndianArmyCrawler",
    "app.modules.crawlers.central_batch1.IndianNavyCrawler",
    "app.modules.crawlers.central_batch1.IndianAirForceCrawler",
    "app.modules.crawlers.central_batch1.IndiaPostCrawler",
    "app.modules.crawlers.central_batch1.SbiCrawler",
    "app.modules.crawlers.central_batch1.RbiCrawler",
]


async def run_crawler(crawler_class_path: str) -> None:
    """Import and run a crawler class with its own DB session."""
    import importlib
    from app.database.session import get_session_factory

    module_path, class_name = crawler_class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    CrawlerClass = getattr(module, class_name)

    factory = get_session_factory()
    async with factory() as db:
        try:
            crawler = CrawlerClass(db)
            await crawler.run()
            await db.commit()
            logger.info("scheduler_crawler_ok", crawler=crawler_class_path)
        except Exception as e:
            await db.rollback()
            logger.error(
                "scheduler_crawler_error",
                crawler=crawler_class_path,
                error=str(e),
            )


async def run_all_crawlers() -> None:
    """Run every registered crawler sequentially (one background job)."""
    logger.info("scheduler_batch_started", count=len(CRAWLER_PATHS))
    for path in CRAWLER_PATHS:
        await run_crawler(path)
    logger.info("scheduler_batch_finished")


# Backwards-compatible alias used by scripts/run_crawlers.py
_run_crawler = run_crawler


async def _run_expired_job_cleanup() -> None:
    from app.modules.jobs.cleanup import run_expired_job_cleanup

    await run_expired_job_cleanup()


def _register_jobs(scheduler: AsyncIOScheduler, *, run_immediately: bool) -> None:
    settings = get_settings()
    interval_hours = settings.CRAWLER_INTERVAL_HOURS

    scheduler.add_job(
        run_all_crawlers,
        trigger=IntervalTrigger(hours=interval_hours),
        id="crawl_all",
        name="Crawl all government sources",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    logger.info(
        "scheduler_job_registered",
        job="crawl_all",
        interval_hours=interval_hours,
    )

    if settings.JOB_CLEANUP_ENABLED:
        scheduler.add_job(
            _run_expired_job_cleanup,
            trigger=CronTrigger(day_of_week="sun", hour=2, minute=0, timezone="UTC"),
            id="cleanup_expired_jobs",
            name="Delete expired jobs (weekly)",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=86400,
        )
        logger.info(
            "scheduler_job_registered",
            job="cleanup_expired_jobs",
            when="Sunday 02:00 UTC",
            retention_days=settings.JOB_CLEANUP_RETENTION_DAYS,
        )

    if run_immediately:
        scheduler.add_job(
            run_all_crawlers,
            trigger="date",
            run_date=datetime.now(timezone.utc) + timedelta(seconds=5),
            id="crawl_all_startup",
            name="Initial crawl on startup",
            replace_existing=True,
            max_instances=1,
        )
        logger.info("scheduler_startup_crawl_queued", delay_seconds=5)


def start_scheduler(*, run_immediately: bool | None = None) -> AsyncIOScheduler:
    """Start the asyncio scheduler. Safe to call once."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    settings = get_settings()
    if run_immediately is None:
        run_immediately = settings.CRAWLER_RUN_ON_STARTUP

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _register_jobs(_scheduler, run_immediately=run_immediately)
    _scheduler.start()
    logger.info("scheduler_started", run_immediately=run_immediately)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
    _scheduler = None


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler
