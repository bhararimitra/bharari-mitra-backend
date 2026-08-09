"""Women & Child Development Maharashtra — news / appointment advertisements."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 40
_PAGES = (
    "https://womenchild.maharashtra.gov.in/mr/news",
    "https://womenchild.maharashtra.gov.in/",
)


class WcdCrawler(BaseCrawler):
    """
    Crawls WCD Maharashtra news / advertisements (appointments, Anganwadi-related notices).
    Source: https://womenchild.maharashtra.gov.in
    """

    name = "wcd_crawler"
    source_url = "https://womenchild.maharashtra.gov.in/mr/news"
    base_url = "https://womenchild.maharashtra.gov.in"
    apply_url = "https://womenchild.maharashtra.gov.in/"

    async def fetch(self) -> dict[str, str]:
        out: dict[str, str] = {}
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            verify=False,
        ) as client:
            for url in _PAGES:
                response = await client.get(url)
                response.raise_for_status()
                out[url] = response.text
        return out

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()

        for html in raw.values():
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                href = a["href"].strip()
                if len(title) < 20:
                    continue
                blob = f"{title} {href}".lower()
                if not any(
                    k in title or k in blob
                    for k in (
                        "जाहिरात",
                        "जाहीरात",
                        "भरती",
                        "नियुक्ती",
                        "recruit",
                        "advertisement",
                        "vacancy",
                        "anganwadi",
                        "अंगणवाडी",
                        "पद",
                    )
                ):
                    continue
                if any(k in blob for k in ("login", "facebook", "twitter", "youtube", "instagram")):
                    continue

                url = urljoin(self.base_url + "/", href)
                if url in seen:
                    continue
                seen.add(url)

                jobs.append(
                    RawJobData(
                        title=f"WCD — {title}",
                        notification_url=url,
                        apply_url=url,
                        pdf_url=url if url.lower().endswith(".pdf") else None,
                        organization_slug="wcd-maharashtra",
                        organization_name="Women & Child Development Maharashtra",
                        organization_url=self.base_url,
                        department_slug="wcd-general",
                        department_name="WCD Recruitment / Appointments",
                        district_slug="all-maharashtra",
                        district_name="All Maharashtra",
                    )
                )
                if len(jobs) >= _MAX_JOBS:
                    break
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("wcd_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match and not raw.published_at:
            raw.published_at = f"01/01/{year_match.group()}"
        return raw
