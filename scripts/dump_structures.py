"""Save cleaned structure samples for Police / NHM / MSRTC (ASCII-safe)."""

from __future__ import annotations

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parent / "_probe_out"
OUT.mkdir(exist_ok=True)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def ascii(s: str) -> str:
    return s.encode("ascii", "replace").decode("ascii")


def dump_msrtc() -> None:
    url = "https://msrtc.maharashtra.gov.in/GeneralPages/Recruitment.aspx"
    r = httpx.get(url, headers=HEADERS, timeout=40, follow_redirects=True)
    soup = BeautifulSoup(r.text, "lxml")
    lines = [f"status={r.status_code} tables={len(soup.find_all('table'))}"]
    table = soup.find("table")
    if table:
        for i, tr in enumerate(table.find_all("tr")):
            cols = [ascii(c.get_text(" ", strip=True)[:80]) for c in tr.find_all(["td", "th"])]
            a = tr.find("a", href=True)
            href = a["href"] if a else ""
            lines.append(f"row{i}|{cols}|{href}")
    (OUT / "msrtc_structure.txt").write_text("\n".join(lines), encoding="utf-8")
    print("msrtc rows", len(lines) - 1)


def dump_police() -> None:
    url = "https://www.mahapolice.gov.in/police-recruitment"
    r = httpx.get(url, headers=HEADERS, timeout=40, follow_redirects=True)
    soup = BeautifulSoup(r.text, "lxml")
    for m in soup.find_all("marquee"):
        m.decompose()
    lines = []
    # Try common content wrappers
    for sel in [
        ".page-content a[href]",
        ".content-area a[href]",
        "#content a[href]",
        ".innerpage a[href]",
        "main a[href]",
        ".container a[href]",
    ]:
        nodes = soup.select(sel)
        lines.append(f"SEL {sel} count={len(nodes)}")

    pdfs = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(" ", strip=True)
        if "/uploads/" in href and href.lower().endswith(".pdf") and len(title) >= 25:
            full = href if href.startswith("http") else f"https://www.mahapolice.gov.in{href}"
            # skip medals/flags etc
            low = href.lower()
            if "external_links" in low:
                continue
            pdfs.append((ascii(title[:140]), full))

    # unique by url
    seen = set()
    uniq = []
    for t, u in pdfs:
        if u not in seen:
            seen.add(u)
            uniq.append((t, u))
    lines.append(f"unique_pdfs={len(uniq)}")
    for t, u in uniq[:25]:
        lines.append(f"{t} || {u}")
    (OUT / "police_structure.txt").write_text("\n".join(lines), encoding="utf-8")
    print("police unique pdfs", len(uniq))


def dump_nhm() -> None:
    url = "https://nhm.maharashtra.gov.in/en/notice-category/recruitments/"
    r = httpx.get(url, headers=HEADERS, timeout=40, follow_redirects=True)
    soup = BeautifulSoup(r.text, "lxml")
    lines = []
    table = soup.find("table")
    for i, tr in enumerate(table.find_all("tr")[:12] if table else []):
        cols = [ascii(c.get_text(" ", strip=True)[:70]) for c in tr.find_all(["td", "th"])]
        a = tr.find("a", href=True)
        href = a["href"] if a else ""
        lines.append(f"row{i}|{cols}|{href}")
    (OUT / "nhm_structure.txt").write_text("\n".join(lines), encoding="utf-8")
    print("nhm rows", len(lines))


if __name__ == "__main__":
    dump_msrtc()
    dump_police()
    dump_nhm()
