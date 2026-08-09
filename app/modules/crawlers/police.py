"""Maharashtra Police Crawler — mahapolice.gov.in/police-recruitment."""

import re
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_DEPT_MAP = {
    "constable": ("police-constable", "Police Constable", "12th-pass-hsc", 18, 28),
    "शिपाई": ("police-constable", "Police Constable", "12th-pass-hsc", 18, 28),
    "sub-inspector": ("police-sub-inspector", "Police Sub-Inspector", "bachelors-degree", 19, 25),
    "head-constable": ("police-head-constable", "Police Head Constable", "12th-pass-hsc", 18, 28),
    "driver": ("police-driver", "Police Driver", "10th-pass", 21, 30),
    "srpf": ("police-srpf", "SRPF", "12th-pass-hsc", 18, 28),
    "सशस्त्र": ("police-srpf", "SRPF", "12th-pass-hsc", 18, 28),
}

# Cap how many notices we ingest per run (page is newest-first).
_MAX_JOBS = 40


class PoliceCrawler(BaseCrawler):
    """
    Crawls Maharashtra Police recruitment notices.
    Source: https://www.mahapolice.gov.in/police-recruitment
    """

    name = "police_crawler"
    source_url = "https://www.mahapolice.gov.in/police-recruitment"
    base_url = "https://www.mahapolice.gov.in"
    apply_base = "https://www.mahapolice.gov.in/police-recruitment"

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
        seen_urls: set[str] = set()

        # Primary: heading text paired with nearest PDF under /uploads/police_recruitment/
        for tag in soup.find_all(["h2", "h3", "h4", "h5", "strong"]):
            title = tag.get_text(" ", strip=True)
            if len(title) < 20:
                continue
            pdf_url = self._nearest_recruitment_pdf(tag)
            if not pdf_url or pdf_url in seen_urls:
                continue
            seen_urls.add(pdf_url)
            jobs.append(self._build_job(title, pdf_url))
            if len(jobs) >= _MAX_JOBS:
                break

        # Fallback: anchors whose href is a recruitment PDF and text is the title
        if len(jobs) < 5:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                title = a.get_text(" ", strip=True)
                if "/uploads/police_recruitment/" not in href.lower():
                    continue
                if not href.lower().endswith(".pdf") or len(title) < 20:
                    continue
                pdf_url = urljoin(self.base_url + "/", href)
                if pdf_url in seen_urls:
                    continue
                seen_urls.add(pdf_url)
                jobs.append(self._build_job(title, pdf_url))
                if len(jobs) >= _MAX_JOBS:
                    break

        self._logger.info("police_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match:
            raw.published_at = f"01/01/{year_match.group()}"
        return raw

    def _nearest_recruitment_pdf(self, tag) -> str | None:
        # Walk forward until the next heading; take the first recruitment PDF.
        for el in tag.next_elements:
            name = getattr(el, "name", None)
            if name in {"h2", "h3", "h4", "h5"}:
                break
            if name == "a" and el.get("href"):
                href = el["href"]
                if (
                    "/uploads/police_recruitment/" in href.lower()
                    and href.lower().endswith(".pdf")
                ):
                    return urljoin(self.base_url + "/", href)

        parent = tag.parent
        if parent and parent.name not in {"body", "html", "main"}:
            for a in parent.find_all("a", href=True):
                href = a["href"]
                if (
                    "/uploads/police_recruitment/" in href.lower()
                    and href.lower().endswith(".pdf")
                ):
                    return urljoin(self.base_url + "/", href)
        return None

    def _build_job(self, title: str, pdf_url: str) -> RawJobData:
        dept_slug, dept_name, qual_slug, age_min, age_max = self._detect_dept(title)
        return RawJobData(
            title=title,
            notification_url=pdf_url,
            apply_url=self.apply_base,
            pdf_url=pdf_url,
            age_min=age_min,
            age_max=age_max,
            organization_slug="maharashtra-police",
            organization_name="Maharashtra Police",
            organization_url=self.base_url,
            department_slug=dept_slug,
            department_name=dept_name,
            district_slug="all-maharashtra",
            district_name="All Maharashtra",
            qualification_slug=qual_slug,
            qualification_name=self._qual_name(qual_slug),
        )

    def _detect_dept(
        self, title: str
    ) -> tuple[str, str, str | None, int | None, int | None]:
        t = title.lower()
        for keyword, info in _DEPT_MAP.items():
            if keyword.lower() in t or keyword in title:
                return info
        return ("police-recruitment", "Police Recruitment", None, None, None)

    def _qual_name(self, slug: str | None) -> str | None:
        mapping = {
            "12th-pass-hsc": "12th Pass (HSC)",
            "bachelors-degree": "Bachelor's Degree",
            "10th-pass": "10th Pass (SSC)",
        }
        return mapping.get(slug or "", None)
