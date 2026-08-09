"""Probe live government recruitment URLs for crawler development."""

from __future__ import annotations

import re
import sys

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json,*/*",
}

URLS = [
    ("Police", "https://www.mahapolice.gov.in/police-recruitment"),
    ("NHM", "https://nhm.maharashtra.gov.in/en/notice-category/recruitments/"),
    ("MSRTC home", "https://msrtc.maharashtra.gov.in"),
    ("MSRTC Career", "https://msrtc.maharashtra.gov.in/Career"),
    ("mahaonline msrtc", "https://msrtcrecruitment.mahaonline.gov.in"),
    ("MPSC page", "https://mpsc.gov.in/recruitmentNotification/1"),
    ("MPSC api1", "https://mpsc.gov.in/api/recruitmentNotification/1"),
    ("MPSC api2", "https://mpsc.gov.in/api/RecruitmentNotification/GetAll"),
    ("MPSC online", "https://mpsconline.gov.in"),
]


def main() -> None:
    for name, url in URLS:
        try:
            r = httpx.get(url, headers=HEADERS, timeout=25.0, follow_redirects=True)
            text = r.text
            tables = text.lower().count("<table")
            pdfs = len(re.findall(r"\.pdf", text, re.I))
            ctype = r.headers.get("content-type", "")[:40]
            print(
                f"{name}: {r.status_code} len={len(text)} "
                f"tables={tables} pdfs={pdfs} ctype={ctype} final={str(r.url)[:90]}"
            )
            if "json" in ctype or text.strip().startswith(("{", "[")):
                print(f"  JSON preview: {text[:300]}")
        except Exception as e:
            print(f"{name}: FAIL {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
    sys.exit(0)
