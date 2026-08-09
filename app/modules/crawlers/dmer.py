"""DMER Maharashtra recruitment crawler — medical education / bond service vacancies."""

from __future__ import annotations

import re
from urllib.parse import urljoin, unquote

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 50
_DATE_RE = re.compile(
    r"(?:Date\s*:?\s*)?(\d{1,2}[-./]\d{1,2}[-./]\d{2,4})",
    re.I,
)


class DmerCrawler(BaseCrawler):
    """
    Crawls DMER Recruitment Portal notices / vacancy PDFs.
    Source: https://dmerrecruitment.maha-arogya.com/
    """

    name = "dmer_crawler"
    source_url = "https://dmerrecruitment.maha-arogya.com/"
    base_url = "https://dmerrecruitment.maha-arogya.com"
    apply_url = "https://dmerrecruitment.maha-arogya.com/"

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
            title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
            href = a["href"].strip()
            if len(title) < 12:
                continue
            href_l = href.lower()
            title_l = title.lower()
            if not (
                href_l.endswith(".pdf")
                or "imp_docs" in href_l
                or any(
                    k in title_l or k in title
                    for k in (
                        "vacancy",
                        "notification",
                        "recruit",
                        "allotment",
                        "भरती",
                        "रिक्",
                        "जाहिरात",
                        "जाहीरात",
                        "notice",
                    )
                )
            ):
                continue

            url = urljoin(self.source_url, href)
            if url in seen:
                continue
            seen.add(url)

            published = None
            m = _DATE_RE.search(title)
            if m:
                published = m.group(1).replace(".", "/").replace("-", "/")

            jobs.append(
                RawJobData(
                    title=f"DMER — {title}",
                    notification_url=url,
                    apply_url=self.apply_url,
                    pdf_url=url if url.lower().endswith(".pdf") else None,
                    published_at=published,
                    organization_slug="dmer",
                    organization_name="DMER Maharashtra",
                    organization_url=self.base_url,
                    department_slug="dmer-medical-education",
                    department_name="Medical Education & Research",
                    district_slug="all-maharashtra",
                    district_name="All Maharashtra",
                    qualification_slug="mbbs",
                    qualification_name="MBBS / MD / MS / MDS",
                )
            )
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("dmer_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match and not raw.published_at:
            raw.published_at = f"01/01/{year_match.group()}"
        return raw
