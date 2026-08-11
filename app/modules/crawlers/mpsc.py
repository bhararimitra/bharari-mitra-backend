"""MPSC Crawler — mpsc.gov.in advertisements (React SPA via Playwright)."""

from __future__ import annotations

import asyncio
import re
from typing import Any
from urllib.parse import quote

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.dates import dates_in_text

_MAX_JOBS = 50
_DATE_KEY_HINTS = (
    "lastdate",
    "last_date",
    "closingdate",
    "closing_date",
    "enddate",
    "end_date",
    "todate",
    "to_date",
    "applicationend",
    "applyend",
    "applyto",
    "onlineend",
)
_ADVT_KEY_HINTS = (
    "advtno",
    "advt_no",
    "advertisementno",
    "advertisement_no",
    "advertisementnumber",
    "adno",
    "advt",
)


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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._json_payloads: list[Any] = []

    async def fetch(self) -> str:
        try:
            from playwright.async_api import async_playwright
        except ImportError as e:
            raise RuntimeError(
                "Playwright is required for MPSC crawler. "
                "Install with: pip install playwright && playwright install chromium"
            ) from e

        self._json_payloads = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (compatible; BharariMitraBot/1.0; "
                        "+https://bhararimitra.in/bot)"
                    )
                )

                async def on_response(response: Any) -> None:
                    ctype = (response.headers.get("content-type") or "").lower()
                    url = (response.url or "").lower()
                    if "json" not in ctype and "api" not in url:
                        return
                    try:
                        payload = await response.json()
                    except Exception:
                        return
                    if payload is not None:
                        self._json_payloads.append(payload)

                page.on("response", lambda response: asyncio.create_task(on_response(response)))
                await page.goto(self.source_url, wait_until="networkidle", timeout=90000)
                await page.wait_for_selector("table.dataTable tbody tr, table tbody tr", timeout=30000)
                await page.wait_for_timeout(1500)
                return await page.content()
            finally:
                await browser.close()

    async def parse(self, raw: str) -> list[RawJobData]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(raw, "lxml")
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        last_by_advt = self._last_dates_from_payloads()
        if not hasattr(self, "_json_payloads"):
            self._json_payloads = []

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

                last_date = last_by_advt.get(self._advt_key(advt_no))
                if not last_date:
                    row_text = " ".join(c.get_text(" ", strip=True) for c in cols)
                    last_date = self._last_date_from_row(row_text, published_at)

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
                        last_date=last_date,
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

        self._logger.info(
            "mpsc_parsed",
            total_found=len(jobs),
            json_payloads=len(self._json_payloads),
            last_dates=sum(1 for j in jobs if j.last_date),
        )
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
        m = re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{4}", text or "")
        return m.group().replace("-", "/") if m else None

    def _advt_key(self, advt_no: str) -> str:
        return re.sub(r"\s+", "", advt_no or "").lower()

    def _last_date_from_row(self, row_text: str, published_at: str | None) -> str | None:
        found = dates_in_text(row_text)
        if not found:
            return None
        extra = [d for d in found if d != published_at]
        return extra[-1] if extra else None

    def _last_dates_from_payloads(self) -> dict[str, str]:
        found: dict[str, str] = {}
        payloads = getattr(self, "_json_payloads", []) or []

        def walk(obj: Any) -> None:
            if isinstance(obj, list):
                for item in obj:
                    walk(item)
                return
            if not isinstance(obj, dict):
                return
            keys = {re.sub(r"[^a-z0-9]", "", str(k).lower()): v for k, v in obj.items()}
            advt = None
            for hint in _ADVT_KEY_HINTS:
                if hint in keys and keys[hint]:
                    advt = str(keys[hint])
                    break
            date_val = None
            for key, val in keys.items():
                if val and any(h in key for h in _DATE_KEY_HINTS):
                    date_val = str(val)
                    break
            if advt and date_val:
                parsed = self._extract_date(date_val)
                if parsed:
                    found[self._advt_key(advt)] = parsed
            for val in obj.values():
                walk(val)

        for payload in payloads:
            walk(payload)
        return found
