"""Run all MVP crawlers once and commit into the local database.

Usage (from backend/):
    python scripts/run_crawlers.py
    python scripts/run_crawlers.py nhm police
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select, text

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import get_engine, get_session_factory
from app.modules.crawlers.scheduler import _run_crawler
from app.modules.jobs.models import Job

logger = get_logger(__name__)

CRAWLERS = {
    "mpsc": "app.modules.crawlers.mpsc.MpscCrawler",
    "police": "app.modules.crawlers.police.PoliceCrawler",
    "nhm": "app.modules.crawlers.nhm.NhmCrawler",
    "msrtc": "app.modules.crawlers.msrtc.MsrtcCrawler",
    "mjp": "app.modules.crawlers.mjp.MjpCrawler",
    "pavitra": "app.modules.crawlers.pavitra.PavitraCrawler",
    "dmer": "app.modules.crawlers.dmer.DmerCrawler",
    "mo": "app.modules.crawlers.mo_recruitment.MoRecruitmentCrawler",
    "wcd": "app.modules.crawlers.wcd.WcdCrawler",
    "mahagov": "app.modules.crawlers.maharashtra_gov.MaharashtraGovCrawler",
    "msedcl": "app.modules.crawlers.mh_batch2.MsedclCrawler",
    "mahagenco": "app.modules.crawlers.mh_batch2.MahagencoCrawler",
    "mahatransco": "app.modules.crawlers.mh_batch2.MahatranscoCrawler",
    "mahametro": "app.modules.crawlers.mh_batch2.MahametroCrawler",
    "mmrda": "app.modules.crawlers.mh_batch2.MmrdaCrawler",
    "midc": "app.modules.crawlers.mh_batch2.MidcCrawler",
    "pwd": "app.modules.crawlers.mh_batch2.PwdCrawler",
    "wrd": "app.modules.crawlers.mh_batch2.WrdCrawler",
    "agriculture": "app.modules.crawlers.mh_batch2.AgricultureCrawler",
    "tribal": "app.modules.crawlers.mh_batch2.TribalCrawler",
    "sjsa": "app.modules.crawlers.mh_batch2.SjsaCrawler",
    "home": "app.modules.crawlers.mh_batch2.HomeDeptCrawler",
    "prisons": "app.modules.crawlers.mh_batch2.PrisonsCrawler",
    "cidco": "app.modules.crawlers.mh_batch2.CidcoCrawler",
    "education": "app.modules.crawlers.mh_batch2.EducationDeptCrawler",
    "muhs": "app.modules.crawlers.mh_batch2.MuhsCrawler",
    "mu": "app.modules.crawlers.mh_batch2.MumbaiUniversityCrawler",
    "sppu": "app.modules.crawlers.mh_batch2.SppuCrawler",
    "pcmc": "app.modules.crawlers.mh_batch2.PcmcCrawler",
    "pmc": "app.modules.crawlers.mh_batch2.PmcCrawler",
    "mahaforest": "app.modules.crawlers.mh_batch3.MahaForestCrawler",
    "ahdf": "app.modules.crawlers.mh_batch3.AnimalHusbandryCrawler",
    "htedu": "app.modules.crawlers.mh_batch3.HigherEducationCrawler",
    "dmerorg": "app.modules.crawlers.mh_batch3.DmerOrgCrawler",
    "mahaswayam": "app.modules.crawlers.mh_batch3.MahaSwayamCrawler",
    "mahaonline": "app.modules.crawlers.mh_batch3.MahaOnlineCrawler",
    "set": "app.modules.crawlers.mh_batch3.SetMaharashtraCrawler",
    "rtmnu": "app.modules.crawlers.mh_batch3.RtmnuCrawler",
    "bamu": "app.modules.crawlers.mh_batch3.BamuCrawler",
    "sgbau": "app.modules.crawlers.mh_batch3.SgbauCrawler",
    "shivaji": "app.modules.crawlers.mh_batch3.ShivajiUniversityCrawler",
    "nmc": "app.modules.crawlers.mh_batch3.NmcNagpurCrawler",
    "best": "app.modules.crawlers.mh_batch3.BestUndertakingCrawler",
    "mswc": "app.modules.crawlers.mh_batch3.MswcCrawler",
    "districts": "app.modules.crawlers.districts.DistrictCollectorsCrawler",
    "ssc": "app.modules.crawlers.ssc.SscCrawler",
    "upsc": "app.modules.crawlers.upsc.UpscCrawler",
    "ibps": "app.modules.crawlers.ibps.IbpsCrawler",
}


async def count_jobs() -> int:
    factory = get_session_factory()
    async with factory() as db:
        result = await db.execute(select(func.count()).select_from(Job))
        return int(result.scalar_one())


async def sample_jobs(limit: int = 8) -> list[tuple[str, str]]:
    factory = get_session_factory()
    async with factory() as db:
        result = await db.execute(
            select(Job.title, Job.slug).order_by(Job.created_at.desc()).limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()]


async def main(selected: list[str]) -> None:
    configure_logging()
    settings = get_settings()
    print(f"Database: {settings.DATABASE_URL.split('@')[-1]}")

    # Quick connectivity check
    engine = get_engine()
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    print("DB connection OK")

    before = await count_jobs()
    print(f"Jobs before: {before}")

    for key in selected:
        path = CRAWLERS[key]
        print(f"\n=== Running {key} ===")
        try:
            await _run_crawler(path)
            print(f"{key}: finished")
        except Exception as e:
            print(f"{key}: FAILED {type(e).__name__}: {e}")

    after = await count_jobs()
    print(f"\nJobs after: {after} (added ~{after - before})")
    print("Latest jobs:")
    for title, slug in await sample_jobs():
        safe = title[:90].encode("ascii", "replace").decode()
        print(f"  - {safe}")
        print(f"    slug={slug}")

    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run BharariMitra crawlers into DB")
    parser.add_argument(
        "names",
        nargs="*",
        choices=[*CRAWLERS.keys()],
        help="Optional subset of crawler keys (default: all)",
    )
    args = parser.parse_args()
    selected = args.names or list(CRAWLERS.keys())
    order = list(CRAWLERS.keys())
    # Keep MPSC (Playwright) last when running everything
    if "mpsc" in order:
        order = [k for k in order if k != "mpsc"] + ["mpsc"]
    selected = [name for name in order if name in selected]
    asyncio.run(main(selected))
