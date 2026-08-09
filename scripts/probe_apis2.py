"""Find CRC header logic and probe public MPSC APIs + MSRTC recruitment HTML."""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
}
OUT = Path(__file__).resolve().parent / "_probe_out"


def load_js() -> str:
    parts = []
    for p in OUT.glob("*chunk.js"):
        parts.append(p.read_text(encoding="utf-8", errors="replace"))
    # also vendor chunk named with underscores
    for p in OUT.glob("_static_js_*.js"):
        parts.append(p.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


js = load_js()
print(f"JS total chars={len(js)}")

# Find CRC related code
for pat in [r".{0,80}CRC.{0,120}", r".{0,80}crc.{0,120}", r".{0,40}X-CRC.{0,80}", r".{0,40}crcHeader.{0,80}"]:
    hits = re.findall(pat, js)
    print(f"pattern {pat[:20]}... hits={len(hits)}")
    for h in hits[:8]:
        print(" ", h.replace("\n", " ")[:200])

# Probe public endpoints
public = [
    "https://mpsc.gov.in/web/api/v1/getallcontent",
    "https://mpsc.gov.in/web/api/v1/getcontentdata",
    "https://mpsc.gov.in/web/api/v1/getwebcontents",
    "https://mpsc.gov.in/web/api/v1/home",
    "https://mpsc.gov.in/web/api/v1/getmenuoptions",
    "https://smbmpscweb.com/web/api/v1/getallcontent",
    "https://smbmpscweb.com/web/api/v1/getwebcontents",
    "https://smbmpscweb.com/web/api/v1/home",
]

print("\n=== Public APIs ===")
for url in public:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=25.0, follow_redirects=True)
        print(f"{url}: {r.status_code} {r.text[:180].replace(chr(10),' ')}")
        if r.status_code == 200 and r.text.strip().startswith(("{", "[")):
            data = r.json()
            name = url.rstrip("/").split("/")[-1]
            (OUT / f"mpsc_{name}.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False)[:300000], encoding="utf-8"
            )
            if isinstance(data, dict):
                print(f"  keys={list(data.keys())[:15]}")
            elif isinstance(data, list):
                print(f"  list={len(data)}")
    except Exception as e:
        print(f"{url}: FAIL {e}")

# Try with common CRC header guesses after searching
crc_contexts = re.findall(r".{0,200}CRC.{0,200}", js, flags=re.I)
(OUT / "crc_contexts.txt").write_text("\n---\n".join(crc_contexts[:50]), encoding="utf-8")
print(f"\nWrote {min(50, len(crc_contexts))} CRC contexts")

# MSRTC recruitment page
print("\n=== MSRTC Recruitment.aspx ===")
r = httpx.get(
    "https://msrtc.maharashtra.gov.in/GeneralPages/Recruitment.aspx",
    headers=HEADERS,
    timeout=30.0,
    follow_redirects=True,
)
(OUT / "msrtc_recruitment.html").write_text(r.text, encoding="utf-8", errors="replace")
soup = BeautifulSoup(r.text, "lxml")
print(f"status={r.status_code} tables={len(soup.find_all('table'))} len={len(r.text)}")
for i, table in enumerate(soup.find_all("table")[:3]):
    rows = table.find_all("tr")
    print(f"table[{i}] rows={len(rows)}")
    for j, tr in enumerate(rows[:5]):
        cols = [c.get_text(" ", strip=True)[:50] for c in tr.find_all(["td", "th"])]
        a = tr.find("a", href=True)
        href = a["href"] if a else ""
        print(f"  r{j}: {cols} | {href[:100]}")

# Also list links
hits = []
for a in soup.find_all("a", href=True):
    text = a.get_text(" ", strip=True)
    if len(text) >= 8:
        hits.append((text[:100], a["href"][:120]))
print(f"links with text={len(hits)}")
for t, u in hits[:15]:
    print(f"  - {t.encode('ascii','replace').decode()} | {u}")

# Police: main content PDFs not in marquee
print("\n=== POLICE main content ===")
police = BeautifulSoup((OUT / "police.html").read_text(encoding="utf-8", errors="replace"), "lxml")
# remove marquees
for m in police.find_all("marquee"):
    m.decompose()
main = police.select_one("#mainContent, .mainContent, .content, main, .page-content, .innerContent")
print(f"main container={main.name if main else None} class={main.get('class') if main else None}")
# look for list of news/recruitment
candidates = police.select(".newsList li, .recruitmentList li, .list-unstyled li, ul li a[href$='.pdf']")
print(f"list candidates={len(candidates)}")
pdfs = []
for a in police.find_all("a", href=True):
    href = a["href"]
    if "/uploads/" in href and href.lower().endswith(".pdf"):
        title = a.get_text(" ", strip=True)
        if len(title) >= 20:
            pdfs.append((title[:120], href if href.startswith("http") else f"https://www.mahapolice.gov.in{href}"))
print(f"meaningful upload pdfs={len(pdfs)}")
for t, u in pdfs[:10]:
    print(f"  - {t.encode('ascii','replace').decode()} | {u[:100]}")
