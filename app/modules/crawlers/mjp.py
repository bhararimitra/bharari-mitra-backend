"""Maharashtra Jeevan Pradhikaran (MJP) recruitment crawler."""

from __future__ import annotations

import re
from urllib.parse import urljoin, unquote

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_MAX_JOBS = 40
_SKIP_TITLE = re.compile(
    r"^(advertisement|corrigendum|application link|recruitment|result notification)\s*$",
    re.I,
)


class MjpCrawler(BaseCrawler):
    """
    Crawls MJP recruitment notices / PDFs.
    Source: https://mjp.maharashtra.gov.in/employee/recruitment/
    """

    name = "mjp_crawler"
    source_url = "https://mjp.maharashtra.gov.in/employee/recruitment/"
    base_url = "https://mjp.maharashtra.gov.in"
    apply_url = "https://mjp.maharashtra.gov.in/employee/recruitment/"

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
            if not href or href.startswith("#"):
                continue

            href_l = href.lower()
            title_l = title.lower()
            is_recruitment = any(
                k in href_l or k in title_l
                for k in (
                    "recruit",
                    "advertisement",
                    "जाहिरात",
                    "जाहीरात",
                    "भरती",
                    "शुद्धिपत्र",
                    "result",
                    "निकाल",
                    "hall",
                    "प्रवेश",
                    "exam",
                    "ibpsonline",
                    "wp-content/uploads",
                )
            )
            if not is_recruitment:
                continue
            if _SKIP_TITLE.match(title) and not href_l.endswith(".pdf"):
                # Prefer meaningful PDF filenames / nearby context
                parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
                title = re.sub(r"\s+", " ", parent_text).strip()[:180] or title
            if len(title) < 8:
                continue
            if any(k in title_l for k in ("skip to", "government of maharashtra", "contact")):
                continue

            notification_url = urljoin(self.source_url, href)
            key = unquote(notification_url).lower()
            if key in seen:
                continue
            seen.add(key)

            # Prefer PDF / apply portal destinations
            if not (
                notification_url.lower().endswith(".pdf")
                or "ibps" in notification_url.lower()
                or "recruit" in title_l
                or "भरती" in title
                or "advertisement" in title_l
                or "जाहिरात" in title
                or "जाहीरात" in title
                or "result" in title_l
                or "निकाल" in title
                or "corrigendum" in title_l
                or "शुद्धिपत्र" in title
            ):
                continue

            display_title = title
            if display_title.lower() in {"advertisement", "corrigendum", "application link"}:
                # Fall back to decoded filename
                fname = unquote(notification_url.rstrip("/").split("/")[-1])
                display_title = re.sub(r"[-_]+", " ", fname.rsplit(".", 1)[0]).strip() or display_title

            jobs.append(
                RawJobData(
                    title=f"MJP — {display_title}",
                    notification_url=notification_url,
                    apply_url=self.apply_url,
                    pdf_url=notification_url if notification_url.lower().endswith(".pdf") else None,
                    organization_slug="mjp",
                    organization_name="Maharashtra Jeevan Pradhikaran (MJP)",
                    organization_url=self.base_url,
                    department_slug="mjp-recruitment",
                    department_name="MJP Recruitment",
                    district_slug="all-maharashtra",
                    district_name="All Maharashtra",
                    qualification_slug="bachelors-degree",
                    qualification_name="Bachelor's Degree",
                )
            )
            if len(jobs) >= _MAX_JOBS:
                break

        self._logger.info("mjp_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match and not raw.published_at:
            raw.published_at = f"01/01/{year_match.group()}"
        return raw
