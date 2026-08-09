"""NHM Maharashtra Crawler — nhm.maharashtra.gov.in recruitments notices."""

import re
import httpx
from bs4 import BeautifulSoup
from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_POST_MAP = {
    "staff nurse": (
        "nhm-nursing", "NHM Nursing",
        "gnm-bsc-nursing", "GNM / B.Sc Nursing",
        18000, 35000, 18, 38,
    ),
    "community health officer": (
        "nhm-cho", "Community Health Officer",
        "bsc-nursing", "B.Sc Nursing",
        25000, 35000, 21, 30,
    ),
    "cho": (
        "nhm-cho", "Community Health Officer",
        "bsc-nursing", "B.Sc Nursing",
        25000, 35000, 21, 30,
    ),
    "medical officer": (
        "nhm-medical-officer", "Medical Officer",
        "mbbs", "MBBS",
        41000, 56000, 21, 45,
    ),
    "pharmacist": (
        "nhm-pharmacy", "Pharmacy",
        "d-pharm-b-pharm", "D.Pharm / B.Pharm",
        15000, 25000, 18, 38,
    ),
    "lab technician": (
        "nhm-lab", "Laboratory",
        "dmlt-bmlt", "DMLT / BMLT",
        12000, 20000, 18, 38,
    ),
    "anm": (
        "nhm-anm", "NHM ANM",
        "anm-course", "ANM Course",
        10000, 15000, 18, 35,
    ),
}


class NhmCrawler(BaseCrawler):
    """
    Crawls NHM Maharashtra recruitment notices.
    Source: https://nhm.maharashtra.gov.in/en/notice-category/recruitments/
    """

    name = "nhm_crawler"
    source_url = "https://nhm.maharashtra.gov.in/en/notice-category/recruitments/"
    base_url = "https://nhm.maharashtra.gov.in"

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
            self._logger.warning("nhm_table_not_found")
            return jobs

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            try:
                # Columns: Sr | Title | Description | Start Date | End Date | File
                title = cols[1].get_text(" ", strip=True)
                if not title or len(title) < 5:
                    continue

                published_at = None
                last_date = None
                if len(cols) >= 5:
                    published_at = self._extract_date(cols[3].get_text(" ", strip=True))
                    last_date = self._extract_date(cols[4].get_text(" ", strip=True))
                elif len(cols) >= 4:
                    last_date = self._extract_date(cols[-2].get_text(" ", strip=True))

                link = row.find("a", href=True)
                notification_url = self.source_url
                if link:
                    href = link["href"].strip()
                    notification_url = (
                        href if href.startswith("http")
                        else f"{self.base_url}/{href.lstrip('/')}"
                    )

                dept_slug, dept_name, qual_slug, qual_name, \
                    sal_min, sal_max, age_min, age_max = self._detect_post(title)

                jobs.append(
                    RawJobData(
                        title=title,
                        notification_url=notification_url,
                        apply_url=self.source_url,
                        pdf_url=notification_url if ".pdf" in notification_url.lower() else None,
                        last_date=last_date,
                        published_at=published_at,
                        salary_min=sal_min,
                        salary_max=sal_max,
                        age_min=age_min,
                        age_max=age_max,
                        organization_slug="nhm-maharashtra",
                        organization_name="NHM Maharashtra",
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
                self._logger.warning("nhm_row_parse_error", error=str(e))
                continue

        self._logger.info("nhm_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        if not raw.published_at:
            year_match = re.search(r"20\d{2}", raw.title)
            if year_match:
                raw.published_at = f"01/01/{year_match.group()}"
        return raw

    def _extract_date(self, text: str) -> str | None:
        m = re.search(r"\d{2}[/\-]\d{2}[/\-]\d{4}", text or "")
        return m.group().replace("-", "/") if m else None

    def _detect_post(
        self, title: str
    ) -> tuple[str, str, str | None, str | None, int | None, int | None, int | None, int | None]:
        t = title.lower()
        for keyword, info in _POST_MAP.items():
            if keyword in t:
                return info
        return (
            "nhm-general", "NHM Maharashtra",
            None, None, None, None, None, None,
        )
