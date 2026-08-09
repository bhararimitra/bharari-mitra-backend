"""Dump raw File cell HTML from MPSC table."""

from pathlib import Path
from bs4 import BeautifulSoup

html = Path(__file__).resolve().parent.joinpath("_probe_out/mpsc_adv_notification_8.html").read_text(encoding="utf-8", errors="replace")
soup = BeautifulSoup(html, "lxml")
table = soup.find("table")
for i, tr in enumerate(table.find_all("tr")[1:4]):
    cols = tr.find_all("td")
    print(f"ROW {i} file cell html:")
    print(cols[4].prettify()[:500])
    print("---")
    print("row html snippet:", str(tr)[:800])
    print("====")
