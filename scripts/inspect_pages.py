"""Inspect HTML structure for working recruitment pages."""

from __future__ import annotations

import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}
OUT = Path(__file__).resolve().parent / "_probe_out"
OUT.mkdir(exist_ok=True)
LOG = OUT / "report.txt"
_log_lines: list[str] = []


def save(name: str, text: str) -> None:
    (OUT / name).write_text(text, encoding="utf-8", errors="replace")


def log(msg: str) -> None:
    _log_lines.append(msg)
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", "replace").decode("ascii"))


def inspect_police() -> None:
    url = "https://www.mahapolice.gov.in/police-recruitment"
    r = httpx.get(url, headers=HEADERS, timeout=40.0, follow_redirects=True)
    save("police.html", r.text)
    soup = BeautifulSoup(r.text, "lxml")

    # Drupal-style views often use article / views-row
    rows = soup.select(".views-row, article.node, .views-field-title a, h2 a, h3 a, h4 a")
    log(f"Police status={r.status_code} views_like={len(rows)}")

    # Prefer structured Drupal view rows
    view_rows = soup.select(".views-row")
    log(f"Police views-row count={len(view_rows)}")
    for i, row in enumerate(view_rows[:8]):
        a = row.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        full = href if href.startswith("http") else f"https://www.mahapolice.gov.in{href}"
        log(f"  view[{i}] title_len={len(a.get_text(strip=True))} href={full[:140]}")

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(" ", strip=True)
        if not text or len(text) < 15:
            continue
        low = text.lower()
        if (
            "भरती" in text
            or "recruit" in low
            or "bharti" in low
            or "notification" in low
            or href.lower().endswith(".pdf")
        ):
            full = href if href.startswith("http") else f"https://www.mahapolice.gov.in{href}"
            links.append((text[:120], full[:160]))

    log(f"Police candidate links={len(links)}")
    for t, u in links[:12]:
        log(f"  - {t} | {u}")


def inspect_nhm() -> None:
    url = "https://nhm.maharashtra.gov.in/en/notice-category/recruitments/"
    r = httpx.get(url, headers=HEADERS, timeout=40.0, follow_redirects=True)
    save("nhm.html", r.text)
    soup = BeautifulSoup(r.text, "lxml")
    log(f"NHM status={r.status_code} tables={len(soup.find_all('table'))}")

    table = soup.find("table")
    if table:
        for i, tr in enumerate(table.find_all("tr")[:8]):
            cols = [c.get_text(" ", strip=True)[:60] for c in tr.find_all(["td", "th"])]
            link = tr.find("a", href=True)
            href = link["href"] if link else ""
            log(f"  row{i}: {cols} | {href[:100]}")

    pdf_links = [
        (a.get_text(" ", strip=True)[:80], a["href"])
        for a in soup.find_all("a", href=True)
        if ".pdf" in a["href"].lower() or "notice" in a["href"].lower() or "upload" in a["href"].lower()
    ]
    log(f"NHM notice/pdf links={len(pdf_links)}")
    for t, u in pdf_links[:8]:
        log(f"  - {t} | {u[:120]}")


def inspect_msrtc() -> None:
    url = "https://msrtc.maharashtra.gov.in/GeneralPages/Home.aspx"
    r = httpx.get(url, headers=HEADERS, timeout=40.0, follow_redirects=True)
    save("msrtc_home.html", r.text)
    soup = BeautifulSoup(r.text, "lxml")
    log(f"MSRTC home status={r.status_code}")

    keywords = ["career", "recruit", "job", "bharti", "भरती", "vacancy", "notification", "tender", "apprentice"]
    hits = []
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        blob = f"{text} {a['href']}".lower()
        if any(k in blob for k in keywords) or "भरती" in text:
            hits.append((text[:80], a["href"][:160]))
    log(f"MSRTC keyword links={len(hits)}")
    for t, u in hits[:20]:
        log(f"  - {t} | {u}")


def find_mpsc_api() -> None:
    r = httpx.get("https://mpsc.gov.in", headers=HEADERS, timeout=30.0, follow_redirects=True)
    save("mpsc_home.html", r.text)
    js_files = re.findall(r'src="(/static/js/[^"]+)"', r.text)
    log(f"MPSC js bundles={js_files}")

    api_hits: set[str] = set()
    for path in js_files:
        js_url = f"https://mpsc.gov.in{path}"
        try:
            jr = httpx.get(js_url, headers=HEADERS, timeout=40.0, follow_redirects=True)
            save(path.replace("/", "_"), jr.text[:500000])
            for m in re.findall(r'["\'](/[^"\']*(?:recruit|notification|advert|exam)[^"\']*)["\']', jr.text, re.I):
                api_hits.add(m)
            for m in re.findall(r'["\'](https?://[^"\']*(?:mpsc|recruit|notification)[^"\']*)["\']', jr.text, re.I):
                api_hits.add(m)
            for m in re.findall(r'["\'](/api/[^"\']+)["\']', jr.text, re.I):
                api_hits.add(m)
            # Also catch axios baseURL patterns
            for m in re.findall(r'baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']', jr.text, re.I):
                api_hits.add(f"baseURL:{m}")
            log(f"  scanned {path} len={len(jr.text)}")
        except Exception as e:
            log(f"  fail {path}: {e}")

    log("MPSC candidate endpoints:")
    for h in sorted(api_hits)[:50]:
        log(f"  {h}")


if __name__ == "__main__":
    log("=== POLICE ===")
    inspect_police()
    log("\n=== NHM ===")
    inspect_nhm()
    log("\n=== MSRTC ===")
    inspect_msrtc()
    log("\n=== MPSC ===")
    find_mpsc_api()
    LOG.write_text("\n".join(_log_lines), encoding="utf-8")
    print(f"Wrote report to {LOG}")
