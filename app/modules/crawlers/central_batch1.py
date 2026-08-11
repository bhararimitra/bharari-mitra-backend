"""High-volume central recruitment crawlers: railways, defence, post, SBI, RBI."""

from __future__ import annotations

import json
import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

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
_SKIP_HREF = re.compile(r"facebook|twitter|linkedin|whatsapp|javascript:|mailto:", re.I)


async def fetch_pages(urls: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    async with httpx.AsyncClient(
        headers=_BROWSER_HEADERS,
        timeout=HTTP_TIMEOUT,
        follow_redirects=True,
        verify=False,
    ) as client:
        for url in urls:
            if not url:
                continue
            try:
                response = await client.get(url)
                response.raise_for_status()
                out[url] = response.text
            except Exception:
                continue
    if not out:
        raise RuntimeError("no pages loaded")
    return out


def clean_title(text: str, limit: int = 220) -> str:
    title = re.sub(r"\s+", " ", text).strip()
    return title[:limit]


def extract_ddmmyyyy(text: str) -> tuple[str | None, str | None]:
    dates = re.findall(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b", text)
    if not dates:
        return None, None
    formatted = [f"{d[0].zfill(2)}/{d[1].zfill(2)}/{d[2]}" for d in dates]
    if len(formatted) >= 2:
        return formatted[0], formatted[-1]
    return formatted[0], None


def _job(
    *,
    title: str,
    notification_url: str,
    apply_url: str | None,
    pdf_url: str | None,
    published_at: str | None,
    last_date: str | None,
    organization_slug: str,
    organization_name: str,
    organization_url: str,
    department_slug: str,
    department_name: str,
    qualification_slug: str | None = None,
    qualification_name: str | None = None,
) -> RawJobData:
    return RawJobData(
        title=title,
        notification_url=notification_url,
        apply_url=apply_url,
        pdf_url=pdf_url,
        published_at=published_at,
        last_date=last_date,
        organization_slug=organization_slug,
        organization_name=organization_name,
        organization_url=organization_url,
        department_slug=department_slug,
        department_name=department_name,
        district_slug="all-india",
        district_name="All India",
        qualification_slug=qualification_slug,
        qualification_name=qualification_name,
    )


class CentralHtmlCrawler(BaseCrawler):
    """Link-listing crawler for official all-India recruitment pages."""

    source_url: str = ""
    extra_pages: tuple[str, ...] = ()
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
    keep = re.compile(
        r"(recruit|vacanc|advert|notification|career|agniveer|corrigendum|"
        r"result|merit|hall\s*ticket|cen\b|apply|intake|enlist)",
        re.I,
    )

    async def fetch(self) -> dict[str, str]:
        pages = await fetch_pages([self.source_url, *self.extra_pages])
        if not pages:
            raise RuntimeError(f"{self.name}: no pages loaded")
        return pages

    def _keep_link(self, title: str, href: str) -> bool:
        if not href or href.startswith("#") or _SKIP_HREF.search(href):
            return False
        blob = f"{title} {href}"
        return bool(_FILE_HINT.search(href) or self.keep.search(blob))

    def _enrich_title(self, a, title: str, href: str) -> str:
        if len(title) < 12:
            parent = a.find_parent(["li", "div", "tr", "td", "p", "h2", "h3", "article"])
            if parent:
                richer = clean_title(parent.get_text(" ", strip=True))
                if 12 < len(richer) < 240:
                    title = richer
            if len(title) < 12 and _FILE_HINT.search(href):
                fname = unquote(href.rstrip("/").split("/")[-1].split("?")[0])
                title = re.sub(r"[-_]+", " ", fname.rsplit(".", 1)[0]).strip()
        return title

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        for page_url, html in raw.items():
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                title = clean_title(a.get_text(" ", strip=True))
                href = a["href"].strip()
                if not self._keep_link(title, href):
                    continue
                title = self._enrich_title(a, title, href)
                if len(title) < 12:
                    continue
                if title.lower() in {"home", "careers", "recruitment", "vacancies", "apply online"}:
                    continue
                url = urljoin(page_url, href)
                if url in seen:
                    continue
                seen.add(url)
                prefix = self.title_prefix or self.organization_name
                published, last = extract_ddmmyyyy(title)
                jobs.append(
                    _job(
                        title=f"{prefix} — {title}" if prefix else title,
                        notification_url=url,
                        apply_url=self.apply_url or url,
                        pdf_url=url if _FILE_HINT.search(url) else None,
                        published_at=published,
                        last_date=last,
                        organization_slug=self.organization_slug,
                        organization_name=self.organization_name,
                        organization_url=self.base_url,
                        department_slug=self.department_slug,
                        department_name=self.department_name,
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


class RrbNationalCrawler(BaseCrawler):
    """National CENs from the official RRB portal (Mumbai loc lists all CENs)."""

    name = "rrb_national_crawler"
    source_url = "https://rrb.indianrailways.gov.in/mumbai"
    base_url = "https://rrb.indianrailways.gov.in"
    apply_url = "https://www.rrbapply.gov.in/"
    loc = "mumbai"
    max_jobs = 35
    min_year = 2024

    async def fetch(self) -> dict[str, str]:
        listing = await fetch_pages([self.source_url])
        html = next(iter(listing.values()))
        urls: list[str] = []
        for cen, cats in self._cens_from_listing(html).items():
            if self._cen_year(cen) < self.min_year:
                continue
            if "Notification" not in cats:
                continue
            urls.append(
                f"{self.base_url}/getdata?cennum={cen}&loc={self.loc}&category=Notification"
            )
            if len(urls) >= 22:
                break
        extra = await fetch_pages(urls) if urls else {}
        return {**listing, **extra}

    @staticmethod
    def _cen_year(cen: str) -> int:
        match = re.search(r"(20\d{2})", cen)
        return int(match.group(1)) if match else 0

    def _cens_from_listing(self, html: str) -> dict[str, list[str]]:
        soup = BeautifulSoup(html, "lxml")
        out: dict[str, list[str]] = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "getdata" not in href:
                continue
            qs = parse_qs(urlparse(urljoin(self.base_url + "/", href)).query)
            cen = (qs.get("cennum") or [""])[0].strip()
            cat = (qs.get("category") or [""])[0].strip()
            if not cen:
                continue
            out.setdefault(cen, [])
            if cat and cat not in out[cen]:
                out[cen].append(cat)
        return out

    def _best_pdf(self, html: str) -> tuple[str | None, str | None]:
        paths = re.findall(r"/[-]/image/[^\"'\s<>]+\.pdf/examsDocuments", html, re.I)
        scored: list[tuple[int, str]] = []
        for path in paths:
            name = path.lower()
            if "hindi" in name:
                continue
            score = 0
            if any(k in name for k in ("faq", "score", "calculation", "mock")):
                score -= 10
            if re.search(r"final.?cen|detailed.?cen", name):
                score += 10
            elif "detailed" in name or re.search(r"cen[_-]?\d{1,2}[_-]\d{4}", name):
                score += 6
            if "corrigendum" in name:
                score += 1
            scored.append((score, path))
        if not scored:
            return None, None
        scored.sort(key=lambda item: item[0], reverse=True)
        best = urljoin(self.base_url + "/", scored[0][1])
        return best, self._title_from_pdf_path(best)

    @staticmethod
    def _title_from_pdf_path(path: str) -> str:
        blob = unquote(path)
        match = re.search(r"/image/\d+(.*?)\.pdf", blob, re.I)
        raw = match.group(1) if match else blob.rstrip("/").split("/")[-1]
        raw = re.sub(r"[_]+", " ", raw)
        raw = re.sub(r"FINAL\s*", "", raw, flags=re.I)
        raw = re.sub(r"CEN\s*\d{1,2}\s*\d{4}\s*", "", raw, flags=re.I)
        raw = re.sub(r"\d{1,2}\.\d{1,2}\.\d{4}", "", raw)
        return clean_title(raw)

    @staticmethod
    def _qual(blob: str) -> tuple[str | None, str | None]:
        text = blob.lower()
        if any(k in text for k in ("level-1", "level 1", "group d", "group-d")):
            return "10th-pass", "10th Pass (SSC)"
        if any(k in text for k in ("je", "paramedical", "section controller", "ntpc graduate", "graduate")):
            return "bachelors-degree", "Bachelor's Degree"
        if any(k in text for k in ("technician", "alp", "ntpc")):
            return "12th-pass-hsc", "12th Pass (HSC)"
        return "12th-pass-hsc", "12th Pass (HSC)"

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        listing_html = raw.get(self.source_url) or next(iter(raw.values()))
        listing_cens = self._cens_from_listing(listing_html)

        for url, html in raw.items():
            if "getdata" not in url:
                continue
            cen = (parse_qs(urlparse(url).query).get("cennum") or [""])[0]
            if not cen or cen in seen:
                continue
            seen.add(cen)
            pdf, pdf_title = self._best_pdf(html)
            label = pdf_title if pdf_title and len(pdf_title) >= 6 else "Centralised Employment Notice"
            title = f"RRB CEN {cen} — {label}"
            notification = pdf or url
            qual_slug, qual_name = self._qual(title)
            jobs.append(
                _job(
                    title=title,
                    notification_url=notification,
                    apply_url=self.apply_url,
                    pdf_url=pdf,
                    published_at=None,
                    last_date=None,
                    organization_slug="rrb",
                    organization_name="Railway Recruitment Boards (RRB)",
                    organization_url=self.base_url,
                    department_slug="rrb-cen",
                    department_name="RRB Centralized Employment Notices",
                    qualification_slug=qual_slug,
                    qualification_name=qual_name,
                )
            )
            if len(jobs) >= self.max_jobs:
                break

        if len(jobs) < self.max_jobs:
            for cen, cats in listing_cens.items():
                if cen in seen or self._cen_year(cen) < self.min_year:
                    continue
                if "Notification" not in cats:
                    continue
                seen.add(cen)
                url = f"{self.base_url}/getdata?cennum={cen}&loc={self.loc}&category=Notification"
                jobs.append(
                    _job(
                        title=f"RRB CEN {cen} — Centralised Employment Notice",
                        notification_url=url,
                        apply_url=self.apply_url,
                        pdf_url=None,
                        published_at=None,
                        last_date=None,
                        organization_slug="rrb",
                        organization_name="Railway Recruitment Boards (RRB)",
                        organization_url=self.base_url,
                        department_slug="rrb-cen",
                        department_name="RRB Centralized Employment Notices",
                        qualification_slug="12th-pass-hsc",
                        qualification_name="12th Pass (HSC)",
                    )
                )
                if len(jobs) >= self.max_jobs:
                    break

        self._logger.info("rrb_national_crawler_parsed", total_found=len(jobs))
        return jobs


class RrcCrCrawler(CentralHtmlCrawler):
    name = "rrc_cr_crawler"
    source_url = "https://www.rrccr.com/Home/Home"
    extra_pages = ("https://www.rrccr.com/",)
    base_url = "https://www.rrccr.com"
    apply_url = "https://www.rrccr.com/Home/HowToApply"
    organization_slug = "rrc-central-railway"
    organization_name = "Railway Recruitment Cell — Central Railway"
    department_slug = "rrc-cr-recruitment"
    department_name = "RRC Central Railway Recruitment"
    qualification_slug = "10th-pass"
    qualification_name = "10th Pass (SSC)"
    title_prefix = "RRC CR"
    max_jobs = 25

    def _keep_link(self, title: str, href: str) -> bool:
        low = href.lower()
        blob = f"{title} {href}".lower()
        if any(
            k in low
            for k in (
                "howtoapply",
                "aboutus",
                "admin",
                "contact",
                "archives",
                "scrutiny",
                "/home/home",
                "/home/result",
                "important_instructions",
            )
        ):
            return False
        if "hindi" in blob or "support email" in blob:
            return False
        return bool(_FILE_HINT.search(href) or "groupd_allotment" in low or "provisional" in blob)

    def _enrich_title(self, a, title: str, href: str) -> str:
        title = re.sub(r"^Click here to (view/download|know)\s*", "", title, flags=re.I)
        title = re.sub(r"^the\s+", "", title, flags=re.I)
        title = re.sub(r"\s*[-–]\s*English\s*$", "", title, flags=re.I)
        return super()._enrich_title(a, clean_title(title), href)


class RailwayBoardCrawler(CentralHtmlCrawler):
    name = "railway_board_crawler"
    source_url = "https://indianrailways.gov.in/railwayboard/view_section.jsp?lang=0&id=0,5,373,3147"
    extra_pages = ()
    base_url = "https://indianrailways.gov.in"
    apply_url = "https://indianrailways.gov.in/railwayboard/view_section.jsp?lang=0&id=0,5,373"
    organization_slug = "railway-board"
    organization_name = "Ministry of Railways — Railway Board"
    department_slug = "railway-board-vacancies"
    department_name = "Railway Board Vacancy Circulars"
    title_prefix = "Railway Board"
    max_jobs = 25

    def _keep_link(self, title: str, href: str) -> bool:
        blob = f"{title} {href}".lower()
        if "proforma" in blob or "view_section.jsp" in href.lower():
            return False
        if not _FILE_HINT.search(href):
            return False
        return "irpersonel" in href.lower() or "vacanc" in blob

    def _enrich_title(self, a, title: str, href: str) -> str:
        parent = a.find_parent("tr")
        if parent:
            richer = clean_title(parent.get_text(" ", strip=True), 200)
            if len(richer) > len(title):
                title = richer
        return title


class IndianArmyCrawler(CentralHtmlCrawler):
    name = "indian_army_crawler"
    source_url = "https://indianarmy.nic.in/"
    extra_pages = ()
    base_url = "https://joinindianarmy.nic.in"
    apply_url = "https://joinindianarmy.nic.in/"
    organization_slug = "indian-army"
    organization_name = "Indian Army"
    department_slug = "indian-army-recruitment"
    department_name = "Join Indian Army"
    qualification_slug = "12th-pass-hsc"
    qualification_name = "12th Pass (HSC)"
    title_prefix = "Indian Army"
    max_jobs = 20

    def _keep_link(self, title: str, href: str) -> bool:
        blob = f"{title} {href}".lower()
        if any(
            k in blob
            for k in (
                "vendor",
                "contractor",
                "tender",
                "commendation",
                "army day",
                "graves",
                "honorary",
            )
        ):
            return False
        if "jointerritorialarmy.gov.in" in href.lower() and "news" not in href.lower():
            return False
        if "news/article" in href.lower() or href.lower().endswith(".pdf"):
            return bool(
                re.search(r"join|recruit|officer|agniveer|nda|tes|territorial|enlist|commission", blob, re.I)
            )
        return False


class IndianNavyCrawler(BaseCrawler):
    name = "indian_navy_crawler"
    source_url = "https://www.joinindiannavy.gov.in/"
    base_url = "https://www.joinindiannavy.gov.in"
    apply_url = "https://www.joinindiannavy.gov.in/"
    _ENTRY_PAGES = {
        "/en/page/agniveer-ssr.html": "Agniveer SSR",
        "/en/page/agniveer-mr.html": "Agniveer MR",
        "/en/page/ssr-medical-asst.html": "SSR (Medical Assistant)",
        "/en/page/officers-ways-to-join.html": "Officer entries",
        "/en/page/agniveer-ways-to-join.html": "Agniveer — ways to join",
    }

    async def fetch(self) -> dict[str, str]:
        urls = [self.source_url, *[urljoin(self.base_url, path) for path in self._ENTRY_PAGES]]
        return await fetch_pages(urls)

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        for page_url in raw:
            matched = None
            for suffix, label in self._ENTRY_PAGES.items():
                if suffix in page_url:
                    matched = (urljoin(self.base_url, suffix), label)
                    break
            if not matched:
                continue
            url, label = matched
            if url in seen:
                continue
            seen.add(url)
            jobs.append(
                _job(
                    title=f"Indian Navy — {label}",
                    notification_url=url,
                    apply_url=url,
                    pdf_url=None,
                    published_at=None,
                    last_date=None,
                    organization_slug="indian-navy",
                    organization_name="Indian Navy",
                    organization_url=self.base_url,
                    department_slug="indian-navy-recruitment",
                    department_name="Join Indian Navy",
                    qualification_slug="12th-pass-hsc",
                    qualification_name="12th Pass (HSC)",
                )
            )
        self._logger.info("indian_navy_crawler_parsed", total_found=len(jobs))
        return jobs


class IndianAirForceCrawler(CentralHtmlCrawler):
    name = "indian_air_force_crawler"
    source_url = "https://agnipathvayu.cdac.in/AV/"
    extra_pages = ("https://careerindianairforce.cdac.in/",)
    base_url = "https://agnipathvayu.cdac.in"
    apply_url = "https://agnipathvayu.cdac.in/AV/"
    organization_slug = "indian-air-force"
    organization_name = "Indian Air Force"
    department_slug = "iaf-agniveervayu"
    department_name = "Agniveervayu / IAF Recruitment"
    qualification_slug = "12th-pass-hsc"
    qualification_name = "12th Pass (HSC)"
    title_prefix = "Indian Air Force"
    max_jobs = 20

    def _keep_link(self, title: str, href: str) -> bool:
        blob = f"{title} {href}".lower()
        if any(k in blob for k in ("instruction", "guideline", "application form", "normalisation", "login", "candidate")):
            return False
        if "intake" in blob or "brochure" in blob or "/av/psl" in href.lower():
            return super()._keep_link(title, href)
        return False


class RbiCrawler(CentralHtmlCrawler):
    name = "rbi_crawler"
    source_url = "https://opportunities.rbi.org.in/Scripts/Vacancies.aspx"
    extra_pages = ()
    base_url = "https://opportunities.rbi.org.in"
    apply_url = "https://opportunities.rbi.org.in/Scripts/apply.aspx"
    organization_slug = "rbi"
    organization_name = "Reserve Bank of India"
    department_slug = "rbi-recruitment"
    department_name = "RBI Careers"
    qualification_slug = "bachelors-degree"
    qualification_name = "Bachelor's Degree"
    title_prefix = "RBI"
    max_jobs = 25
    keep = re.compile(
        r"(recruit|vacanc|engagement|officer|engineer|notification|advert|lateral|grade)",
        re.I,
    )

    def _keep_link(self, title: str, href: str) -> bool:
        if "bs_viewcontent.aspx" not in href.lower() and not _FILE_HINT.search(href):
            return False
        if not self.keep.search(title):
            return False
        return True


class SbiCrawler(BaseCrawler):
    name = "sbi_crawler"
    source_url = "https://sbi.bank.in/web/careers/current-openings"
    base_url = "https://sbi.bank.in"
    apply_url = "https://sbi.bank.in/web/careers/current-openings"

    async def fetch(self) -> str:
        pages = await fetch_pages([self.source_url])
        return next(iter(pages.values()))

    async def parse(self, raw: str) -> list[RawJobData]:
        soup = BeautifulSoup(raw, "lxml")
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        for card in soup.select("div.card"):
            text = clean_title(card.get_text(" ", strip=True), 500)
            if "RECRUITMENT" not in text.upper() and "ADVERTISEMENT NO" not in text.upper() and "ENGAGEMENT" not in text.upper():
                continue
            title = re.split(
                r"DOWNLOAD ADVERTISEMENT|APPLY ONLINE|LAST DATE TO APPLY",
                text,
                maxsplit=1,
                flags=re.I,
            )[0]
            title = re.sub(r"\(Apply Online from.*?\)", "", title, flags=re.I)
            title = clean_title(title)
            if len(title) < 16:
                continue

            pdf_url = None
            apply_href = self.apply_url
            for a in card.find_all("a", href=True):
                href = urljoin(self.source_url, a["href"])
                label = a.get_text(" ", strip=True).lower()
                if _FILE_HINT.search(href) and ("english" in label or "advt" in href.lower() or "eng" in href.lower()):
                    if pdf_url is None or "eng" in href.lower():
                        pdf_url = href
                if "apply" in label and href.startswith("http"):
                    apply_href = href
            notification = pdf_url or apply_href or self.source_url
            if notification in seen:
                continue
            seen.add(notification)
            published, last = extract_ddmmyyyy(text)
            last_match = re.search(
                r"LAST DATE TO APPLY\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]20\d{2})", text, re.I
            )
            if last_match:
                last = last_match.group(1).replace("-", "/")
            jobs.append(
                _job(
                    title=f"SBI — {title}",
                    notification_url=notification,
                    apply_url=apply_href,
                    pdf_url=pdf_url,
                    published_at=published,
                    last_date=last,
                    organization_slug="sbi",
                    organization_name="State Bank of India",
                    organization_url=self.base_url,
                    department_slug="sbi-careers",
                    department_name="SBI Careers",
                    qualification_slug="bachelors-degree",
                    qualification_name="Bachelor's Degree",
                )
            )
            if len(jobs) >= 40:
                break
        self._logger.info("sbi_parsed", total_found=len(jobs))
        return jobs


def _extract_next_array(html: str, key: str) -> list[dict]:
    """Parse a JSON array embedded in a Next.js RSC payload."""
    for needle in (f'{key}\\":[', f'{key}":['):
        idx = html.find(needle)
        if idx == -1:
            continue
        start = html.find("[", idx)
        end = html.find('],\\"', start)
        if end == -1:
            end = html.find("]", start)
        else:
            end += 1
        if end == -1:
            continue
        blob = html[start : end + 1] if html[end] == "]" else html[start:end]
        if not blob.endswith("]"):
            blob = blob[: blob.rfind("]") + 1]
        if "\\" in needle:
            blob = blob.replace('\\"', '"')
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            return data
    return []


def _is_stale_notice(title: str) -> bool:
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", title)]
    if not years:
        return False
    if any(y >= 2025 for y in years):
        return False
    return max(years) <= 2022


class IndiaPostCrawler(BaseCrawler):
    name = "india_post_crawler"
    source_url = "https://www.indiapost.gov.in/vacancies"
    extra_pages = (
        "https://www.indiapost.gov.in/vacancies/recruitments",
        "https://www.indiapost.gov.in/vacancies/online-gds",
    )
    base_url = "https://www.indiapost.gov.in"
    apply_url = "https://www.indiapost.gov.in/vacancies"

    async def fetch(self) -> dict[str, str]:
        return await fetch_pages([self.source_url, *self.extra_pages])

    async def parse(self, raw: dict[str, str]) -> list[RawJobData]:
        jobs: list[RawJobData] = []
        seen: set[str] = set()
        for page_url, html in raw.items():
            rows = _extract_next_array(html, "recruitmentData")
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                title = clean_title(a.get_text(" ", strip=True))
                href = urljoin(page_url, a["href"])
                blob = f"{title} {href}".lower()
                if len(title) < 20:
                    continue
                if "/api/documents/file/" not in href and not any(
                    k in blob for k in ("recruit", "gds", "vacanc", "notification", "postman", "mts", "driver", "artisan")
                ):
                    continue
                rows.append({"title": title, "url": href, "date": None, "slug": None})

            for row in rows:
                if not isinstance(row, dict):
                    continue
                title = clean_title(str(row.get("title") or ""))
                if len(title) < 16 or _is_stale_notice(title):
                    continue
                path = str(row.get("url") or "")
                url = path if path.startswith("http") else urljoin(self.base_url + "/", path.lstrip("/"))
                if url in seen:
                    continue
                seen.add(url)
                published, last = extract_ddmmyyyy(str(row.get("date") or title))
                jobs.append(
                    _job(
                        title=f"India Post — {title}",
                        notification_url=url,
                        apply_url=self.apply_url,
                        pdf_url=url if "/api/documents/file/" in url or _FILE_HINT.search(url) else None,
                        published_at=published,
                        last_date=last,
                        organization_slug="india-post",
                        organization_name="India Post",
                        organization_url=self.base_url,
                        department_slug="india-post-recruitment",
                        department_name="Department of Posts Recruitment",
                        qualification_slug="10th-pass",
                        qualification_name="10th Pass (SSC)",
                    )
                )
                if len(jobs) >= 40:
                    break
            if len(jobs) >= 40:
                break
        self._logger.info("india_post_parsed", total_found=len(jobs))
        return jobs
