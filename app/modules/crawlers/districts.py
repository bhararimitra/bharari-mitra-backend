"""District collector / ZP template crawler for Maharashtra districts."""

from __future__ import annotations

import json
from pathlib import Path

from app.modules.crawlers.html_listing import HtmlListingCrawler

_SOURCES = Path(__file__).resolve().parent / "sources" / "maharashtra.json"


def _district_urls() -> list[tuple[str, str, str]]:
    """Return (slug, name, collector_url) for districts with a hint URL."""
    data = json.loads(_SOURCES.read_text(encoding="utf-8"))
    rows: list[tuple[str, str, str]] = []
    for d in data.get("districts", []):
        url = d.get("collector_hint") or d.get("zp_hint")
        if url:
            rows.append((d["slug"], d["name"], url))
    return rows


class DistrictCollectorsCrawler(HtmlListingCrawler):
    """
    Crawls all district collector (and known ZP) homepages for recruitment-like links.
    One crawler run covers every district listed in maharashtra.json.
    """

    name = "district_collectors_crawler"
    source_url = "https://pune.gov.in"
    base_url = "https://maharashtra.gov.in"
    apply_url = "https://maharashtra.gov.in"
    organization_slug = "district-collectors"
    organization_name = "Maharashtra District Collectors"
    department_slug = "district-recruitment"
    department_name = "District Recruitment Notices"
    title_prefix = "District"
    max_jobs = 120

    async def fetch(self) -> dict[str, str]:
        # Override pages dynamically from inventory
        self.extra_pages = tuple(url for _, _, url in _district_urls())
        # Keep a primary page so Base expectations hold
        if self.extra_pages:
            self.source_url = self.extra_pages[0]
        return await super().fetch()

    async def parse(self, raw: dict[str, str]):
        jobs = await super().parse(raw)
        # Retitle with district name when URL matches
        url_to_name = {url: name for _, name, url in _district_urls()}
        for job in jobs:
            for url, name in url_to_name.items():
                if url.rstrip("/") in job.notification_url or url.rstrip("/") in (job.apply_url or ""):
                    if not job.title.startswith(f"District ({name})"):
                        job.title = job.title.replace("District —", f"District ({name}) —", 1)
                    break
        return jobs
