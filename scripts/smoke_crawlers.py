"""Live smoke test: fetch+parse only (no DB). Run: python scripts/smoke_crawlers.py"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Allow `python scripts/smoke_crawlers.py` from backend/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def run_one(name: str, crawler_cls) -> None:
    crawler = object.__new__(crawler_cls)
    # Attach a tiny logger-compatible object for parse warnings
    from app.core.logging import configure_logging, get_logger

    configure_logging()
    crawler._logger = get_logger(name)
    print(f"\n=== {name} ===")
    try:
        raw = await crawler_cls.fetch(crawler)
        size = len(raw) if hasattr(raw, "__len__") else "?"
        print(f"fetch ok payload={type(raw).__name__} size={size}")
        jobs = await crawler_cls.parse(crawler, raw)
        print(f"parsed jobs={len(jobs)}")
        for j in jobs[:5]:
            title = j.title[:80].encode("ascii", "replace").decode()
            print(f"  - {title}")
            print(f"    {j.notification_url[:100]}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")


async def main() -> None:
    from app.modules.crawlers.nhm import NhmCrawler
    from app.modules.crawlers.police import PoliceCrawler
    from app.modules.crawlers.msrtc import MsrtcCrawler
    from app.modules.crawlers.mjp import MjpCrawler
    from app.modules.crawlers.ssc import SscCrawler
    from app.modules.crawlers.upsc import UpscCrawler
    from app.modules.crawlers.ibps import IbpsCrawler
    from app.modules.crawlers.mpsc import MpscCrawler

    # HTML/API crawlers first (reliable), then Playwright MPSC
    await run_one("NHM", NhmCrawler)
    await run_one("Police", PoliceCrawler)
    await run_one("MSRTC", MsrtcCrawler)
    await run_one("MJP", MjpCrawler)
    await run_one("SSC", SscCrawler)
    await run_one("UPSC", UpscCrawler)
    await run_one("IBPS", IbpsCrawler)
    await run_one("MPSC", MpscCrawler)


if __name__ == "__main__":
    asyncio.run(main())
