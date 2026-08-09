"""Smoke-test MPSC Playwright crawler only."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def main() -> None:
    from app.core.logging import configure_logging, get_logger
    from app.modules.crawlers.mpsc import MpscCrawler

    configure_logging()
    crawler = object.__new__(MpscCrawler)
    crawler._logger = get_logger("MPSC")
    print("Fetching MPSC via Playwright...")
    raw = await MpscCrawler.fetch(crawler)
    print(f"fetch ok bytes={len(raw)}")
    # Save for inspection
    out = Path(__file__).resolve().parent / "_probe_out" / "mpsc_playwright.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(raw, encoding="utf-8", errors="replace")
    jobs = await MpscCrawler.parse(crawler, raw)
    print(f"parsed jobs={len(jobs)}")
    for j in jobs[:10]:
        title = j.title[:100].encode("ascii", "replace").decode()
        print(f"  - {title}")
        print(f"    {j.notification_url[:120]}")


if __name__ == "__main__":
    asyncio.run(main())
