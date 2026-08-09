"""Inspect MPSC adv table row HTML structure."""

from pathlib import Path
from bs4 import BeautifulSoup

html = Path(__file__).resolve().parent.joinpath("_probe_out/mpsc_adv_notification_8.html").read_text(encoding="utf-8", errors="replace")
soup = BeautifulSoup(html, "lxml")
table = soup.find("table")
print("table classes", table.get("class") if table else None)
for i, tr in enumerate(table.find_all("tr")[:4] if table else []):
    cols = tr.find_all(["td", "th"])
    print(f"ROW {i} cols={len(cols)}")
    for j, c in enumerate(cols):
        a = c.find("a", href=True)
        text = c.get_text(" ", strip=True)[:100]
        href = a["href"] if a else ""
        print(f"  [{j}] {text.encode('ascii','replace').decode()} | {href[:120]}")
