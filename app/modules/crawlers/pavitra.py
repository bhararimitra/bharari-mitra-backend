"""Pavitra / TAIT Teacher Recruitment crawler (School Education, Maharashtra)."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 60
_BASE = "https://tait2025.mahateacherrecruitment.org.in/"
_HOME = f"{_BASE}Public/Home.aspx"
_NEWS = f"{_BASE}Public/Notifications.aspx?NotificationCategoryID=18"
_BROCHURE = f"{_BASE}Public/Notifications.aspx?NotificationCategoryID=7"
_APPLICANT = f"{_BASE}Public/Notifications.aspx?NotificationCategoryID=4"


class PavitraCrawler(BaseCrawler):
    """
    Crawls PAVITRA Teacher Recruitment portal.
    Source: https://tait2025.mahateacherrecruitment.org.in/
    Linked from education.maharashtra.gov.in as पवित्र (शिक्षक पदभरती).
    """

    name = "pavitra_crawler"
    source_url = _HOME
    base_url = _BASE.rstrip("/")
    apply_url = _HOME

    async def fetch(self) -> dict[str, str]:
        pages = {
            "home": _HOME,
            "news": _NEWS,
            "brochure": _BROCHURE,
            "applicant": _APPLICANT,
        }
        out: dict[str, str] = {}
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=httpx.Timeout(60.0, connect=20.0),
            follow_redirects=True,
            verify=False,
        ) as client:
            for key, url in pages.items():
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    out[key] = response.text
                except Exception as e:
                    self._logger.warning("pavitra_page_fetch_failed", page=key, error=str(e))
                    out[key] = ""
        if not any(out.values()):
            raise RuntimeError("Pavitra: all listing pages failed to load")
        return out

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()

        # Home: notification zip packs + announcement text
        home = BeautifulSoup(raw.get("home", ""), "lxml")
        for a in home.find_all("a", href=True):
            title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
            href = a["href"].strip()
            if not title or len(title) < 8:
                continue
            if "NotificationFiles" not in href and not href.lower().endswith((".pdf", ".zip")):
                continue
            url = urljoin(self.base_url + "/", href)
            if url in seen:
                continue
            seen.add(url)
            jobs.append(
                self._job(
                    title=f"Pavitra — {title}",
                    notification_url=url,
                    pdf_url=url if url.lower().endswith(".pdf") else None,
                    summary="PAVITRA Teacher Recruitment notification pack",
                )
            )

        # Notification category tables
        for key in ("news", "brochure", "applicant"):
            soup = BeautifulSoup(raw.get(key, ""), "lxml")
            for a in soup.find_all("a", href=True):
                title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                href = a["href"].strip()
                if len(title) < 12:
                    continue
                href_l = href.lower()
                if not any(x in href_l for x in (".pdf", ".zip", "notificationfiles", "download", "file")):
                    # Some rows link via onclick / relative docs — keep PDF/ZIP only
                    continue
                url = urljoin(self.base_url + "/", href)
                if url in seen:
                    continue
                seen.add(url)
                jobs.append(
                    self._job(
                        title=f"Pavitra — {title}",
                        notification_url=url,
                        pdf_url=url if url.lower().endswith(".pdf") else None,
                    )
                )
                if len(jobs) >= _MAX_JOBS:
                    break
            if len(jobs) >= _MAX_JOBS:
                break

        # Always include a portal hub entry so Latest Jobs shows active cycle
        hub_key = self.source_url.lower()
        if hub_key not in seen and len(jobs) < _MAX_JOBS:
            seen.add(hub_key)
            ann = home.select_one(".announcement, .news, marquee, .alert")
            summary = None
            if ann:
                summary = re.sub(r"\s+", " ", ann.get_text(" ", strip=True))[:400]
            jobs.insert(
                0,
                self._job(
                    title="Pavitra — Teacher Recruitment 2025 (Portal)",
                    notification_url=self.source_url,
                    summary=summary or "Official PAVITRA / TAIT teacher recruitment portal",
                ),
            )

        self._logger.info("pavitra_parsed", total_found=len(jobs))
        return jobs[:_MAX_JOBS]

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        if not raw.published_at:
            raw.published_at = "01/01/2025"
        return raw

    def _job(
        self,
        *,
        title: str,
        notification_url: str,
        pdf_url: str | None = None,
        summary: str | None = None,
    ) -> RawJobData:
        return RawJobData(
            title=title,
            summary=summary,
            notification_url=notification_url,
            apply_url=self.apply_url,
            pdf_url=pdf_url,
            organization_slug="pavitra",
            organization_name="Pavitra — School Education Maharashtra",
            organization_url="https://education.maharashtra.gov.in",
            department_slug="pavitra-teacher",
            department_name="Teacher Recruitment (Pavitra / TAIT)",
            district_slug="all-maharashtra",
            district_name="All Maharashtra",
            qualification_slug="bachelors-degree",
            qualification_name="Bachelor's Degree / D.El.Ed / B.Ed",
        )
