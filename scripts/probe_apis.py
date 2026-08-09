"""Probe discovered MPSC API and MSRTC Recruitment.aspx."""

from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
}
OUT = Path(__file__).resolve().parent / "_probe_out"
OUT.mkdir(exist_ok=True)


def try_get(name: str, url: str) -> None:
    try:
        r = httpx.get(url, headers=HEADERS, timeout=30.0, follow_redirects=True)
        ctype = r.headers.get("content-type", "")
        preview = r.text[:500].replace("\n", " ")
        print(f"{name}: {r.status_code} ctype={ctype[:40]} len={len(r.text)}")
        print(f"  preview: {preview[:300]}")
        safe = re.sub(r"[^\w.-]+", "_", name)
        (OUT / f"{safe}.txt").write_text(r.text[:200000], encoding="utf-8", errors="replace")
        if "json" in ctype or r.text.strip().startswith(("{", "[")):
            try:
                data = r.json()
                (OUT / f"{safe}.json").write_text(
                    json.dumps(data, indent=2, ensure_ascii=False)[:200000],
                    encoding="utf-8",
                )
                if isinstance(data, list):
                    print(f"  list len={len(data)}")
                    if data:
                        print(f"  first keys={list(data[0].keys()) if isinstance(data[0], dict) else type(data[0])}")
                elif isinstance(data, dict):
                    print(f"  dict keys={list(data.keys())[:20]}")
            except Exception as e:
                print(f"  json parse fail: {e}")
    except Exception as e:
        print(f"{name}: FAIL {type(e).__name__}: {e}")


# Search JS for more recruitment-related paths
js = (OUT / "_static_js_main.1fed3850.chunk.js").read_text(encoding="utf-8", errors="replace") if (OUT / "_static_js_main.1fed3850.chunk.js").exists() else ""
if not js:
    # download main again
    r = httpx.get("https://mpsc.gov.in/static/js/main.1fed3850.chunk.js", headers=HEADERS, timeout=40)
    js = r.text
    (OUT / "_static_js_main.1fed3850.chunk.js").write_text(js[:500000], encoding="utf-8", errors="replace")

paths = sorted(set(re.findall(r'["\'](/web/api/v1/[^"\']+)["\']', js)))
print("All /web/api/v1 paths in main chunk:")
for p in paths:
    print(f"  {p}")

BASES = [
    "https://mpsc.gov.in",
    "https://smbmpscweb.com",
]
ENDPOINTS = [
    "/web/api/v1/admin/content/isactiveadvertisment",
    "/web/api/v1/admin/exam_name/listAll",
    "/web/api/v1/admin/exam_type/listAll",
]

print("\n=== MPSC API ===")
for base in BASES:
    for ep in ENDPOINTS:
        try_get(f"{base}{ep}", f"{base}{ep}")

# Also try common REST patterns from recruitmentNotification route
for base in BASES:
    for ep in [
        "/web/api/v1/admin/content/recruitmentNotification",
        "/web/api/v1/admin/content/listAll",
        "/web/api/v1/admin/advertisement/listAll",
        "/web/api/v1/admin/advertisement/active",
        "/web/api/v1/public/advertisement",
        "/web/api/v1/public/recruitment",
    ]:
        try_get(f"{base}{ep}", f"{base}{ep}")

print("\n=== MSRTC Recruitment ===")
for url in [
    "https://msrtc.maharashtra.gov.in/Recruitment.aspx",
    "https://msrtc.maharashtra.gov.in/GeneralPages/Recruitment.aspx",
    "https://msrtc.maharashtra.gov.in/GeneralPages/Home.aspx",
]:
    try_get(url, url)

# Police page structure - look for PDF list pattern in saved HTML
police_html = (OUT / "police.html").read_text(encoding="utf-8", errors="replace")
from bs4 import BeautifulSoup

soup = BeautifulSoup(police_html, "lxml")
print("\n=== POLICE structure ===")
# Find containers with many PDF links
pdf_as = [a for a in soup.find_all("a", href=True) if a["href"].lower().endswith(".pdf") and "/uploads/" in a["href"]]
print(f"upload pdf links={len(pdf_as)}")
parents = {}
for a in pdf_as[:5]:
    p = a.parent
    print(f"parent tag={p.name} class={p.get('class')} text_len={len(a.get_text(strip=True))}")
    # walk up
    for _ in range(4):
        if p and p.parent:
            p = p.parent
            print(f"  up tag={p.name} class={p.get('class')}")
