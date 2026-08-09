"""MSRTC Crawler — msrtc.maharashtra.gov.in recruitment advertisements."""

import re
from urllib.parse import urljoin
import httpx
from bs4 import BeautifulSoup
from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_POST_MAP = {
    "driver": (
        "msrtc-driver", "MSRTC Driver",
        "10th-pass", "10th Pass (SSC)",
        19900, 63200, 21, 40,
    ),
    "conductor": (
        "msrtc-conductor", "MSRTC Conductor",
        "12th-pass-hsc", "12th Pass (HSC)",
        17400, 53500, 18, 35,
    ),
    "mechanic": (
        "msrtc-mechanic", "MSRTC Mechanic",
        "iti", "ITI",
        19900, 63200, 18, 35,
    ),
    "traffic supervisor": (
        "msrtc-traffic-supervisor", "MSRTC Traffic Supervisor",
        "bachelors-degree", "Bachelor's Degree",
        25500, 81100, 21, 40,
    ),
    "junior engineer": (
        "msrtc-junior-engineer", "MSRTC Junior Engineer",
        "diploma-engineering", "Diploma in Engineering",
        29200, 92300, 21, 38,
    ),
    "apprentice": (
        "msrtc-apprentice", "MSRTC Apprentice",
        "iti", "ITI",
        7000, 9000, 18, 28,
    ),
    "supervisor": (
        "msrtc-supervisor", "MSRTC Supervisor",
        "bachelors-degree", "Bachelor's Degree",
        25500, 81100, 21, 40,
    ),
}


class MsrtcCrawler(BaseCrawler):
    """
    Crawls MSRTC recruitment advertisements.
    Source: https://msrtc.maharashtra.gov.in/GeneralPages/Recruitment.aspx
    """

    name = "msrtc_crawler"
    source_url = "https://msrtc.maharashtra.gov.in/GeneralPages/Recruitment.aspx"
    base_url = "https://msrtc.maharashtra.gov.in"
    apply_url = "https://msrtc.maharashtra.gov.in/GeneralPages/Recruitment.aspx"

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

        table = soup.find("table")
        if not table:
            self._logger.warning("msrtc_table_not_found")
            return jobs

        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 1:
                continue
            try:
                title = cols[0].get_text(" ", strip=True)
                title = re.sub(r"\s+", " ", title).strip()
                if not title or len(title) < 8:
                    continue
                # Skip pure press notes if they have no ad link
                link = row.find("a", href=True)
                if not link:
                    continue

                href = link["href"].strip()
                notification_url = urljoin(self.source_url, href)

                dept_slug, dept_name, qual_slug, qual_name, \
                    sal_min, sal_max, age_min, age_max = self._detect_post(title)

                jobs.append(
                    RawJobData(
                        title=title,
                        notification_url=notification_url,
                        apply_url=self.apply_url,
                        pdf_url=notification_url if ".pdf" in notification_url.lower() else None,
                        salary_min=sal_min,
                        salary_max=sal_max,
                        age_min=age_min,
                        age_max=age_max,
                        organization_slug="msrtc",
                        organization_name="MSRTC",
                        organization_url=self.base_url,
                        department_slug=dept_slug,
                        department_name=dept_name,
                        district_slug="all-maharashtra",
                        district_name="All Maharashtra",
                        qualification_slug=qual_slug,
                        qualification_name=qual_name,
                    )
                )
            except Exception as e:
                self._logger.warning("msrtc_row_parse_error", error=str(e))
                continue

        self._logger.info("msrtc_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        year_match = re.search(r"20\d{2}", raw.title)
        if year_match:
            raw.published_at = f"01/01/{year_match.group()}"
        raw.title = re.sub(r"\bMSRTC\b\s*[-–:]\s*", "", raw.title, flags=re.I).strip()
        if not raw.title:
            raw.title = "MSRTC Recruitment"
        return raw

    def _detect_post(
        self, title: str
    ) -> tuple[str, str, str | None, str | None, int | None, int | None, int | None, int | None]:
        t = title.lower()
        for keyword, info in _POST_MAP.items():
            if keyword in t:
                return info
        # Marathi / common post hints
        if "चालक" in title or "ड्रायव्हर" in title:
            return _POST_MAP["driver"]
        if "परिचालक" in title:
            return _POST_MAP["conductor"]
        return (
            "msrtc-general", "MSRTC General Recruitment",
            None, None, None, None, None, None,
        )
