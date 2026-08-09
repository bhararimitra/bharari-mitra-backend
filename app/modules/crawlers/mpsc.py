"""MPSC Crawler — mpsc.gov.in advertisements (React SPA via Playwright)."""

import re
from urllib.parse import quote
from app.modules.crawlers.base import BaseCrawler, RawJobData

_MAX_JOBS = 50


class MpscCrawler(BaseCrawler):
    """
    Crawls MPSC advertisements / notifications / corrigendums.

    mpsc.gov.in is a React SPA with CRC-protected APIs, so plain httpx
    cannot read listings. Playwright loads the app, lets it render, then
    we scrape the advertisements table.
    """

    name = "mpsc_crawler"
    source_url = "https://mpsc.gov.in/adv_notification/8"
    base_url = "https://mpsc.gov.in"
    apply_url = "https://mpsconline.gov.in"

    async def fetch(self) -> str:
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise RuntimeError(
                "Playwright is required for MPSC crawler. "
                "Install with: pip install playwright && playwright install chromium"
            ) from e

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (compatible; BharariMitraBot/1.0; "
                        "+https://bhararimitra.in/bot)"
                    )
                )
                await page.goto(self.source_url, wait_until="networkidle", timeout=90000)
                await page.wait_for_selector("table.dataTable tbody tr, table tbody tr", timeout=30000)
                # Ensure rows are painted
                await page.wait_for_timeout(1500)
                return await page.content()
            finally:
                await browser.close()

    async def parse(self, raw: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "lxml")
        jobs: list[RawJobData] = []
        seen: set[str] = set()

        table = soup.find("table")
        if not table:
            self._logger.warning("mpsc_table_not_found")
            return jobs

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            try:
                # Columns: Sr | Advt. No. | Subject | Date of Publication | File
                sr = cols[0].get_text(" ", strip=True)
                advt_no = cols[1].get_text(" ", strip=True) if len(cols) > 1 else ""
                title = cols[2].get_text(" ", strip=True) if len(cols) > 2 else ""
                if len(title) < 10:
                    continue

                published_at = None
                if len(cols) > 3:
                    published_at = self._extract_date(cols[3].get_text(" ", strip=True))

                # PDF downloads are JS-handled (href="#"); keep a stable canonical URL.
                notification_url = (
                    f"{self.source_url}?advt={quote(advt_no or 'unknown')}"
                    f"&sr={quote(sr or str(len(jobs) + 1))}"
                )

                key = f"{advt_no}|{title}"
                if key in seen:
                    continue
                seen.add(key)

                jobs.append(
                    RawJobData(
                        title=title if not advt_no else f"{advt_no} — {title}",
                        notification_url=notification_url,
                        apply_url=self.apply_url,
                        published_at=published_at,
                        organization_slug="mpsc",
                        organization_name="MPSC",
                        organization_url=self.base_url,
                        department_slug="mpsc-state-services",
                        department_name="MPSC State Services",
                        district_slug="all-maharashtra",
                        district_name="All Maharashtra",
                    )
                )
                if len(jobs) >= _MAX_JOBS:
                    break
            except Exception as e:
                self._logger.warning("mpsc_row_parse_error", error=str(e))
                continue

        self._logger.info("mpsc_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        if not raw.published_at:
            year_match = re.search(r"20\d{2}", raw.title)
            if year_match:
                raw.published_at = f"01/01/{year_match.group()}"
        age_match = re.search(r"(\d{2})\s*[-–]\s*(\d{2})\s*years?", raw.title, re.I)
        if age_match:
            raw.age_min = int(age_match.group(1))
            raw.age_max = int(age_match.group(2))
        return raw

    def _extract_date(self, text: str) -> str | None:
        # Site uses dd-mm-yyyy
        m = re.search(r"\d{2}[/\-]\d{2}[/\-]\d{4}", text or "")
        return m.group().replace("-", "/") if m else None
