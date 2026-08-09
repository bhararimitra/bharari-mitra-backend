"""Maharashtra.gov.in official advertisements feed (state portal).

Filters PDFs to recruitment/appointment-like notices and skips tenders/quotations.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, unquote

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 50

_INCLUDE = re.compile(
    r"(भरती|जाहिरात|जाहीरात|नियुक्ती|नेमणूक|पद[ाे]?|recruit|advertisement|"
    r"vacancy|walk[\s-]*in|कुलसचिव|सल्लागार|consultant|officer|manager|"
    r"सेवानिवृत्त.{0,40}(पद|नेम|नियु))",
    re.I,
)
_EXCLUDE = re.compile(
    r"(दरपत्रक|निविदा|टेंडर|tender|quotation|खरेदी|लिलाव|auction|e[\s-]*tender|"
    r"procurement|जेएफओआरएम|jform|शिष्यवृत्ती|scholarship|योजनांसाठी प्रवेशिका)",
    re.I,
)


class MaharashtraGovCrawler(BaseCrawler):
    """
    Crawls maharashtra.gov.in homepage / notice PDFs for recruitment advertisements.
    Source: https://maharashtra.gov.in
    """

    name = "maharashtra_gov_crawler"
    source_url = "https://maharashtra.gov.in"
    base_url = "https://maharashtra.gov.in"
    apply_url = "https://maharashtra.gov.in"

    async def fetch(self) -> str:
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            verify=False,
        ) as client:
            response = await client.get(self.source_url)
            response.raise_for_status()
            return response.text

    async def parse(self, raw: str) -> list[RawJobData]:
        soup = BeautifulSoup(raw, "lxml")
        jobs: list[RawJobData] = []
        seen: set[str] = set()

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if "/Site/Upload/PDF/" not in href and not href.lower().endswith(".pdf"):
                continue

            parent = a.find_parent(["li", "div", "tr", "article", "p", "td"])
            title = ""
            if parent:
                title = re.sub(r"\s+", " ", parent.get_text(" ", strip=True)).strip()
            if not title or len(title) < 20:
                title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
            if not title or len(title) < 12:
                fname = unquote(href.rstrip("/").split("/")[-1])
                title = re.sub(r"[-_]+", " ", fname.rsplit(".", 1)[0]).strip()

            title = re.sub(r"\+?\s*अधिक\s*$", "", title).strip()
            if len(title) < 12:
                continue
            if _EXCLUDE.search(title) or _EXCLUDE.search(href):
                continue
            if not _INCLUDE.search(title) and not _INCLUDE.search(unquote(href)):
                continue

            url = urljoin(self.source_url + "/", href)
            if url in seen:
                continue
            seen.add(url)

            jobs.append(
                RawJobData(
                    title=f"Maharashtra Gov — {title[:220]}",
                    notification_url=url,
                    apply_url=self.apply_url,
                    pdf_url=url,
                    organization_slug="maharashtra-gov",
                    organization_name="Government of Maharashtra",
                    organization_url=self.base_url,
                    department_slug="maharashtra-gov-ads",
                    department_name="State Portal Advertisements",
                    district_slug="all-maharashtra",
                    district_name="All Maharashtra",
                )
            )
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("maharashtra_gov_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        # Dates often embedded in filename like 07-08-2026
        m = re.search(r"(20\d{2})[-_/]?(\d{2})[-_/]?(\d{2})", raw.notification_url)
        if m and not raw.published_at:
            # yyyy-mm-dd style in some names; also dd-mm-yyyy in titles
            pass
        m2 = re.search(r"(\d{2})[-_/](\d{2})[-_/](20\d{2})", raw.title + " " + raw.notification_url)
        if m2 and not raw.published_at:
            raw.published_at = f"{m2.group(1)}/{m2.group(2)}/{m2.group(3)}"
        elif not raw.published_at:
            year = re.search(r"20\d{2}", raw.title)
            if year:
                raw.published_at = f"01/01/{year.group()}"
        return raw
