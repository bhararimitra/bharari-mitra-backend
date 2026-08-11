"""Public Health Department (Arogya) crawler — phd.maharashtra.gov.in.

arogya.maharashtra.gov.in no longer resolves. The live official site is the
S3WaaS portal phd.maharashtra.gov.in (advertisements + Marathi जाहिरात).
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.modules.crawlers.base import BaseCrawler, RawJobData
from app.modules.crawlers.http_headers import DEFAULT_HEADERS, HTTP_TIMEOUT

_BROWSER_HEADERS = {
    **DEFAULT_HEADERS,
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

_FILE_HINT = re.compile(r"\.(pdf|zip|docx?)(?:$|\?)", re.I)
_KEEP = re.compile(
    r"(recruit|advert|vacanc|appoint|director|officer|nurse|anm|corrigendum|"
    r"walk.?in|contract|bharti|भरती|जाहिरात|जाहीरात|निवड|शुद्धिपत्र|नियुक्ती|"
    r"वैद्यकीय|आरोग्य)",
    re.I,
)
_SKIP = re.compile(
    r"(patrika|पत्रिका|rbd_act|vivah|citizen.?charter|recruitment.?rules|"
    r"facebook|twitter|linkedin|sharer|tender|rfp|assembly.?note|"
    r"government.?orders$|guidelines$|policies$|acts?.?rules|"
    r"termination|probationary)",
    re.I,
)
_NAV_TITLES = {
    "home",
    "documents",
    "advertisements",
    "recruitments",
    "recruitment rules",
    "जाहिरात",
    "भरती",
    "view",
    "download",
    "पहा",
}


class ArogyaCrawler(BaseCrawler):
    """Public Health Department advertisements on phd.maharashtra.gov.in."""

    name = "arogya_crawler"
    source_url = "https://phd.maharashtra.gov.in/en/document-category/advertisement/"
    extra_pages = (
        "https://phd.maharashtra.gov.in/document-category/%E0%A4%9C%E0%A4%BE%E0%A4%B9%E0%A4%BF%E0%A4%B0%E0%A4%BE%E0%A4%A4/",
        "https://phd.maharashtra.gov.in/en/",
        "https://phd.maharashtra.gov.in/en/past-notices/career/",
        "https://phd.maharashtra.gov.in/en/notices/",
    )
    base_url = "https://phd.maharashtra.gov.in"
    apply_url = "https://phd.maharashtra.gov.in/en/document-category/advertisement/"
    max_jobs = 40

    async def fetch(self) -> dict[str, str]:
        out: dict[str, str] = {}
        async with httpx.AsyncClient(
            headers=_BROWSER_HEADERS,
            timeout=HTTP_TIMEOUT,
            follow_redirects=True,
            verify=False,
        ) as client:
            for url in (self.source_url, *self.extra_pages):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    out[url] = response.text
                except Exception as e:
                    self._logger.warning("arogya_page_failed", url=url, error=str(e))
        if not out:
            raise RuntimeError("arogya_crawler: no pages loaded")
        return out

    @staticmethod
    def _clean(text: str, limit: int = 220) -> str:
        return re.sub(r"\s+", " ", text).strip()[:limit]

    @staticmethod
    def _extract_date(text: str) -> str | None:
        match = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b", text)
        if not match:
            return None
        return f"{match.group(1).zfill(2)}/{match.group(2).zfill(2)}/{match.group(3)}"

    def _qual(self, title: str) -> tuple[str | None, str | None]:
        blob = title.lower()
        if any(k in blob for k in ("medical officer", "वैद्यकीय अधिका", "mbbs", "mo group")):
            return "mbbs", "MBBS"
        if any(k in blob for k in ("staff nurse", "nursing", "परिचर्या")):
            return "gnm-bsc-nursing", "GNM / B.Sc Nursing"
        return None, None

    def _apply_url(self, title: str) -> str:
        blob = title.lower()
        if any(k in blob for k in ("medical officer", "वैद्यकीय अधिका", "group a", "गट – अ", "गट-अ")):
            return "https://www.morecruitment.maha-arogya.com/"
        return self.apply_url

    def _keep(self, title: str, href: str) -> bool:
        if not href or href.startswith("#"):
            return False
        blob = f"{title} {href}"
        if _SKIP.search(blob):
            return False
        if title.strip().lower() in _NAV_TITLES:
            return False
        if "/document-category/" in href.lower() and "/document/" not in href.lower():
            return False
        is_file = bool(_FILE_HINT.search(href))
        is_doc = bool(re.search(r"/document/[a-z0-9-]+", href, re.I))
        return bool((is_file or is_doc) and _KEEP.search(blob))

    def _job(
        self,
        title: str,
        url: str,
        published_at: str | None,
    ) -> RawJobData:
        qual_slug, qual_name = self._qual(title)
        return RawJobData(
            title=f"Arogya — {title}",
            notification_url=url,
            apply_url=self._apply_url(title),
            pdf_url=url if _FILE_HINT.search(url) else None,
            published_at=published_at,
            organization_slug="arogya",
            organization_name="Public Health Department (Arogya)",
            organization_url=self.base_url,
            department_slug="phd-recruitment",
            department_name="Public Health Department Recruitment",
            district_slug="all-maharashtra",
            district_name="All Maharashtra",
            qualification_slug=qual_slug,
            qualification_name=qual_name,
        )

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()

        for page_url, html in raw.items():
            soup = BeautifulSoup(html, "lxml")

            for tr in soup.find_all("tr"):
                text = self._clean(tr.get_text(" ", strip=True), 400)
                if not _KEEP.search(text) or _SKIP.search(text):
                    continue
                links = [
                    a
                    for a in tr.find_all("a", href=True)
                    if _FILE_HINT.search(a["href"]) or "/document/" in a["href"]
                ]
                if not links:
                    continue
                title = self._clean(links[0].get_text(" ", strip=True))
                if len(title) < 16 or title.lower() in _NAV_TITLES:
                    title = re.sub(
                        r"\s*(View|Download|Accessible Version|पहा|डाउनलोड).*$",
                        "",
                        text,
                        flags=re.I,
                    )
                    title = self._clean(title)
                if len(title) < 16:
                    continue
                href = urljoin(page_url, links[0]["href"])
                if href in seen or not self._keep(title, href):
                    continue
                seen.add(href)
                jobs.append(self._job(title, href, self._extract_date(text)))
                if len(jobs) >= self.max_jobs:
                    break
            if len(jobs) >= self.max_jobs:
                break

            for a in soup.find_all("a", href=True):
                title = self._clean(a.get_text(" ", strip=True))
                href = a["href"].strip()
                if len(title) < 16:
                    parent = a.find_parent(["li", "div", "article", "td", "p", "h2", "h3"])
                    if parent:
                        title = self._clean(parent.get_text(" ", strip=True))
                if not self._keep(title, href):
                    continue
                url = urljoin(page_url, href)
                if url in seen:
                    continue
                seen.add(url)
                jobs.append(self._job(title, url, self._extract_date(title)))
                if len(jobs) >= self.max_jobs:
                    break
            if len(jobs) >= self.max_jobs:
                break

        self._logger.info("arogya_parsed", total_found=len(jobs))
        return jobs
