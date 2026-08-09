"""Public Health Department — Medical Officer (Group-A) recruitment portal crawler."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 40


class MoRecruitmentCrawler(BaseCrawler):
    """
    Crawls MO Recruitment portal (selection lists / notices for Medical Officer Group-A).
    Source: https://www.morecruitment.maha-arogya.com/
    """

    name = "mo_recruitment_crawler"
    source_url = "https://www.morecruitment.maha-arogya.com/"
    base_url = "https://www.morecruitment.maha-arogya.com"
    apply_url = "https://www.morecruitment.maha-arogya.com/"

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
            if len(title) < 10:
                continue
            if not (href.lower().endswith(".pdf") or "imp_docs" in href.lower()):
                continue
            url = urljoin(self.source_url, href)
            if url in seen:
                continue
            seen.add(url)

            jobs.append(
                RawJobData(
                    title=f"MO Bharti — {title}",
                    notification_url=url,
                    apply_url=self.apply_url,
                    pdf_url=url if url.lower().endswith(".pdf") else None,
                    organization_slug="mo-recruitment",
                    organization_name="Public Health Department — MO Recruitment",
                    organization_url=self.base_url,
                    department_slug="phd-medical-officer",
                    department_name="Medical Officer Group-A",
                    district_slug="all-maharashtra",
                    district_name="All Maharashtra",
                    qualification_slug="mbbs",
                    qualification_name="MBBS",
                )
            )
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("mo_recruitment_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match and not raw.published_at:
            raw.published_at = f"01/01/{year_match.group()}"
        return raw
