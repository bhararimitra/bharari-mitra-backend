"""UPSC crawler — active central examinations from upsc.gov.in."""

from __future__ import annotations

import re
from urllib.parse import urljoin, unquote

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 40


class UpscCrawler(BaseCrawler):
    """
    Crawls UPSC active examinations.
    Source: https://www.upsc.gov.in/examinations/active-exams
    """

    name = "upsc_crawler"
    source_url = "https://www.upsc.gov.in/examinations/active-exams"
    base_url = "https://www.upsc.gov.in"
    apply_url = "https://upsconline.nic.in/"

    async def fetch(self) -> str:
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
        ) as client:
            response = await client.get(self.source_url)
            response.raise_for_status()
            return response.text

    async def parse(self, raw: str) -> list[RawJobData]:
        soup = BeautifulSoup(raw, "lxml")
        jobs: list[RawJobData] = []
        seen: set[str] = set()

        for a in soup.select("table a, .view-content a, .views-row a, td a"):
            title = a.get_text(" ", strip=True)
            href = (a.get("href") or "").strip()
            if len(title) < 12 or not href:
                continue
            if href.startswith("#") or "javascript:" in href.lower():
                continue

            notification_url = urljoin(self.base_url + "/", href)
            key = unquote(notification_url).lower()
            if key in seen:
                continue
            seen.add(key)

            jobs.append(
                RawJobData(
                    title=f"UPSC — {title}",
                    notification_url=notification_url,
                    apply_url=self.apply_url,
                    organization_slug="upsc",
                    organization_name="Union Public Service Commission (UPSC)",
                    organization_url=self.base_url,
                    department_slug=self._dept_slug(title),
                    department_name=self._dept_name(title),
                    district_slug="all-india",
                    district_name="All India",
                    qualification_slug="bachelors-degree",
                    qualification_name="Bachelor's Degree",
                )
            )
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("upsc_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match and not raw.published_at:
            raw.published_at = f"01/01/{year_match.group()}"
        return raw

    def _dept_slug(self, title: str) -> str:
        t = title.lower()
        if "civil services" in t:
            return "upsc-cse"
        if "engineering services" in t:
            return "upsc-ese"
        if "defence" in t or "nda" in t or "cds" in t:
            return "upsc-defence"
        if "capf" in t or "cisf" in t:
            return "upsc-capf"
        if "medical" in t:
            return "upsc-cms"
        if "forest" in t:
            return "upsc-ifs"
        return "upsc-examinations"

    def _dept_name(self, title: str) -> str:
        mapping = {
            "upsc-cse": "UPSC Civil Services",
            "upsc-ese": "UPSC Engineering Services",
            "upsc-defence": "UPSC Defence Examinations",
            "upsc-capf": "UPSC CAPF / CISF",
            "upsc-cms": "UPSC Medical Services",
            "upsc-ifs": "UPSC Forest Service",
        }
        return mapping.get(self._dept_slug(title), "UPSC Examinations")
