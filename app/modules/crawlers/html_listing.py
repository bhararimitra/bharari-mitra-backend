"""Shared helpers for Maharashtra HTML notice-board crawlers."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_FILE_HINT = re.compile(r"\.(pdf|zip|docx?|xlsx?)(?:$|\?)", re.I)
_KEEP = re.compile(
    r"(भरती|जाहिरात|जाहीरात|नियुक्ती|नेमणूक|पद|recruit|advert|vacanc|corrigendum|"
    r"notification|result|merit|hall\s*ticket|निवड|निकाल|शुद्धिपत्र|apprentice|walk)",
    re.I,
)


class HtmlListingCrawler(BaseCrawler):
    """Configurable HTML listing crawler for department notice pages."""

    name: str = "html_listing_crawler"
    source_url: str = ""
    base_url: str = ""
    apply_url: str | None = None
    organization_slug: str = ""
    organization_name: str = ""
    department_slug: str = ""
    department_name: str = ""
    qualification_slug: str | None = None
    qualification_name: str | None = None
    title_prefix: str = ""
    max_jobs: int = 40
    extra_pages: tuple[str, ...] = ()

    async def fetch(self) -> dict[str, str]:
        pages = [self.source_url, *self.extra_pages]
        out: dict[str, str] = {}
        async with httpx.AsyncClient(
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            verify=False,
        ) as client:
            for url in pages:
                if not url:
                    continue
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    out[url] = response.text
                except Exception as e:
                    self._logger.warning(
                        "listing_page_failed", crawler=self.name, url=url, error=str(e)
                    )
        if not out:
            raise RuntimeError(f"{self.name}: no pages loaded")
        return out

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        for page_url, html in raw.items():
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                title = re.sub(r"\s+", " ", a.get_text(" ", strip=True)).strip()
                href = a["href"].strip()
                if not href or href.startswith("#") or href.lower().startswith("javascript:"):
                    continue
                blob = f"{title} {href}"
                is_file = bool(_FILE_HINT.search(href))
                is_notice_path = bool(
                    re.search(r"/(notice|recruitment|career|advert|upload|vacanc)", href, re.I)
                )
                if not (is_file or is_notice_path or _KEEP.search(blob)):
                    continue
                if re.search(r"facebook|twitter|linkedin|whatsapp|sharer", href, re.I):
                    continue

                # Recover title from parent / filename when link text is weak
                if len(title) < 12 or re.fullmatch(r"\(?\d+(\.\d+)?\s*(KB|MB|GB)\)?", title, re.I):
                    parent = a.find_parent(["li", "div", "tr", "article", "td", "p", "h2", "h3", "h4"])
                    if parent:
                        richer = re.sub(r"\s+", " ", parent.get_text(" ", strip=True)).strip()
                        if len(richer) > 12:
                            title = richer[:220]
                    if len(title) < 12 and is_file:
                        from urllib.parse import unquote

                        fname = unquote(href.rstrip("/").split("/")[-1])
                        title = re.sub(r"[-_]+", " ", fname.rsplit(".", 1)[0]).strip()
                if len(title) < 12:
                    continue
                if title.lower() in {
                    "home",
                    "careers",
                    "recruitment",
                    "भरती",
                    "जाहिरात",
                    "जाहीरात",
                    "पदभरती",
                }:
                    continue

                url = urljoin(page_url, href)
                if url in seen:
                    continue
                seen.add(url)
                prefix = self.title_prefix or self.organization_name
                jobs.append(
                    RawJobData(
                        title=f"{prefix} — {title}" if prefix else title,
                        notification_url=url,
                        apply_url=self.apply_url or self.source_url,
                        pdf_url=url if is_file else None,
                        organization_slug=self.organization_slug,
                        organization_name=self.organization_name,
                        organization_url=self.base_url,
                        department_slug=self.department_slug,
                        department_name=self.department_name,
                        district_slug="all-maharashtra",
                        district_name="All Maharashtra",
                        qualification_slug=self.qualification_slug,
                        qualification_name=self.qualification_name,
                    )
                )
                if len(jobs) >= self.max_jobs:
                    break
            if len(jobs) >= self.max_jobs:
                break
        self._logger.info(f"{self.name}_parsed", total_found=len(jobs))
        return jobs

    def normalize(self, raw: RawJobData) -> RawJobData:
        raw = super().normalize(raw)
        m = re.search(r"(\d{2})[-./](\d{2})[-./](20\d{2})", raw.title)
        if m and not raw.published_at:
            raw.published_at = f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
        elif not raw.published_at:
            y = re.search(r"20\d{2}", raw.title)
            if y:
                raw.published_at = f"01/01/{y.group()}"
        return raw
