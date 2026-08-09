"""IBPS crawler — banking / central recruitment notifications from ibps.in."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 50
_DATE_RE = re.compile(r"(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{1,2}-\w{3}-\d{4}|\d{2}-\w{3}-\d{4})", re.I)
_RANGE_RE = re.compile(
    r"(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{2}-\w{3}-\d{4})\s*(?:to|-|–)\s*"
    r"(\d{1,2}[-/]\w{3}[-/]\d{4}|\d{2}-\w{3}-\d{4})",
    re.I,
)


class IbpsCrawler(BaseCrawler):
    """
    Crawls IBPS homepage + recruitment listing for open CRP / bank recruitments.
    Source: https://www.ibps.in/
    """

    name = "ibps_crawler"
    source_url = "https://www.ibps.in/"
    recruitment_url = "https://www.ibps.in/index.php/recruitment/"
    base_url = "https://www.ibps.in"
    apply_url = "https://www.ibps.in/"

    async def fetch(self) -> dict[str, str]:
        headers = {**DEFAULT_HEADERS, "Accept": "text/html,application/xhtml+xml"}
        async with httpx.AsyncClient(
            headers=headers,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            verify=False,
        ) as client:
            home = await client.get(self.source_url)
            home.raise_for_status()
            recruitment = await client.get(self.recruitment_url)
            recruitment.raise_for_status()
            return {"home": home.text, "recruitment": recruitment.text}

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()

        for html in (raw.get("home", ""), raw.get("recruitment", "")):
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                href = a["href"].strip()
                if len(title) < 18:
                    continue
                blob = f"{title} {href}".lower()
                if not any(
                    k in blob
                    for k in (
                        "recruit",
                        "crp",
                        "notification",
                        "clerk",
                        "po/mt",
                        "specialist",
                        "junior associate",
                        "bank officer",
                        "ibpsreg",
                    )
                ):
                    continue
                if any(k in blob for k in ("login", "contact us", "policies", "organisational")):
                    continue

                notification_url = urljoin(self.source_url, href)
                key = notification_url.lower()
                if key in seen:
                    continue
                seen.add(key)

                published_at, last_date = self._extract_dates(title)
                pdf_url = notification_url if notification_url.lower().endswith(".pdf") else None
                dept_slug, dept_name, qual_slug, qual_name = self._detect_stream(title)

                jobs.append(
                    RawJobData(
                        title=title if title.upper().startswith("IBPS") else f"IBPS — {title}",
                        notification_url=notification_url,
                        apply_url=notification_url if "ibpsreg" in notification_url else self.apply_url,
                        pdf_url=pdf_url,
                        published_at=published_at,
                        last_date=last_date,
                        organization_slug="ibps",
                        organization_name="Institute of Banking Personnel Selection (IBPS)",
                        organization_url=self.base_url,
                        department_slug=dept_slug,
                        department_name=dept_name,
                        district_slug="all-india",
                        district_name="All India",
                        qualification_slug=qual_slug,
                        qualification_name=qual_name,
                    )
                )
                if len(jobs) >= _MAX_JOBS:
                    break
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("ibps_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        raw.title = re.sub(r"\s+", " ", raw.title).strip()
        return raw

    def _extract_dates(self, title: str) -> tuple[str | None, str | None]:
        m = _RANGE_RE.search(title.replace("/", "-"))
        if m:
            return self._norm_date(m.group(1)), self._norm_date(m.group(2))
        dates = _DATE_RE.findall(title.replace("/", "-"))
        if len(dates) >= 2:
            return self._norm_date(dates[0]), self._norm_date(dates[1])
        if len(dates) == 1:
            return self._norm_date(dates[0]), None
        return None, None

    def _norm_date(self, value: str) -> str | None:
        value = value.strip().replace("/", "-")
        # dd-Mon-yyyy -> keep as-is for base parser (%d %b %Y after replace)
        parts = value.split("-")
        if len(parts) == 3 and parts[1].isalpha():
            return f"{parts[0].zfill(2)} {parts[1].title()} {parts[2]}"
        return value

    def _detect_stream(self, title: str) -> tuple[str, str, str | None, str | None]:
        t = title.lower()
        if "clerk" in t or "csa" in t or "junior associate" in t:
            return "ibps-clerk", "IBPS Clerk / CSA", "12th-pass-hsc", "12th Pass (HSC)"
        if "po" in t or "management trainee" in t or "mt" in t:
            return "ibps-po", "IBPS PO / MT", "bachelors-degree", "Bachelor's Degree"
        if "specialist" in t or "so" in t:
            return "ibps-so", "IBPS Specialist Officer", "bachelors-degree", "Bachelor's Degree"
        if "rrb" in t:
            return "ibps-rrb", "IBPS RRB", "bachelors-degree", "Bachelor's Degree"
        return "ibps-recruitment", "IBPS Recruitment", "bachelors-degree", "Bachelor's Degree"
