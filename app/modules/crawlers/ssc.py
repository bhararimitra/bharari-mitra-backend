"""SSC (Staff Selection Commission) crawler — central government exams via official API."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_EXAMS_API = "https://ssc.gov.in/api/admin/5.1/allExams"
_MAX_JOBS = 40

_QUAL_HINTS = (
    (re.compile(r"\b(CHSL|10\+2|higher secondary)\b", re.I), "12th-pass-hsc", "12th Pass (HSC)"),
    (re.compile(r"\b(MTS|multitasking)\b", re.I), "10th-pass", "10th Pass (SSC)"),
    (re.compile(r"\b(JE|junior engineer)\b", re.I), "diploma-engineering", "Diploma in Engineering"),
    (re.compile(r"\b(CGL|graduate|stenographer|SI|CAPF|CPO)\b", re.I), "bachelors-degree", "Bachelor's Degree"),
    (re.compile(r"\b(GD|constable|rifleman)\b", re.I), "10th-pass", "10th Pass (SSC)"),
)


class SscCrawler(BaseCrawler):
    """
    Crawls SSC exam catalogue from the official API.
    Source: https://ssc.gov.in (API: /api/admin/5.1/allExams)
    """

    name = "ssc_crawler"
    source_url = "https://ssc.gov.in/"
    base_url = "https://ssc.gov.in"
    apply_url = "https://ssc.gov.in/"

    async def fetch(self) -> dict:
        headers = {
            **DEFAULT_HEADERS,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://ssc.gov.in/",
        }
        async with httpx.AsyncClient(
            headers=headers,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
        ) as client:
            response = await client.get(_EXAMS_API)
            response.raise_for_status()
            return response.json()

    async def parse(self, raw: dict) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        rows = raw.get("data") if isinstance(raw, dict) else None
        if not isinstance(rows, list):
            self._logger.warning("ssc_unexpected_payload")
            return jobs

        for row in rows:
            if not isinstance(row, dict):
                continue
            exam_name = (row.get("examName") or row.get("description") or "").strip()
            exam_code = (row.get("examCode") or "").strip()
            if len(exam_name) < 8:
                continue

            title = f"SSC {exam_code} — {exam_name}" if exam_code else f"SSC — {exam_name}"
            key = f"{exam_code}|{exam_name}".lower()
            if key in seen:
                continue
            seen.add(key)

            nav = (row.get("navigationUrl") or "").strip()
            notification_url = urljoin(self.base_url + "/", nav.lstrip("/")) if nav else self.source_url
            qual_slug, qual_name = self._detect_qual(f"{exam_code} {exam_name}")

            jobs.append(
                RawJobData(
                    title=title,
                    summary=(row.get("description") or exam_name)[:500],
                    notification_url=notification_url,
                    apply_url=notification_url if nav else self.apply_url,
                    organization_slug="ssc",
                    organization_name="Staff Selection Commission (SSC)",
                    organization_url=self.base_url,
                    department_slug=f"ssc-{(exam_code or 'general').lower()}",
                    department_name=f"SSC {exam_code}" if exam_code else "SSC Examinations",
                    district_slug="all-india",
                    district_name="All India",
                    qualification_slug=qual_slug,
                    qualification_name=qual_name,
                )
            )
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("ssc_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match and not raw.published_at:
            raw.published_at = f"01/01/{year_match.group()}"
        return raw

    def _detect_qual(self, text: str) -> tuple[str | None, str | None]:
        for pattern, slug, name in _QUAL_HINTS:
            if pattern.search(text):
                return slug, name
        return None, None
