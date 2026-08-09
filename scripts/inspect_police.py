"""Inspect police recruitment page without removing marquees; find title+pdf pairing."""

from pathlib import Path
import httpx
from bs4 import BeautifulSoup

OUT = Path(__file__).resolve().parent / "_probe_out"
HEADERS = {"User-Agent": "Mozilla/5.0"}
r = httpx.get("https://www.mahapolice.gov.in/police-recruitment", headers=HEADERS, timeout=40, follow_redirects=True)
soup = BeautifulSoup(r.text, "lxml")

lines = []
# All h2/h3/h4 with nearby links
for tag in soup.find_all(["h2", "h3", "h4", "h5", "strong", "b"]):
    title = tag.get_text(" ", strip=True)
    if len(title) < 20:
        continue
    # find pdf in same parent / next siblings
    parent = tag.parent
    pdf = None
    if parent:
        a = parent.find("a", href=True)
        if a and ".pdf" in a["href"].lower():
            pdf = a["href"]
    if not pdf:
        nxt = tag.find_next("a", href=True)
        if nxt and ".pdf" in nxt["href"].lower():
            pdf = nxt["href"]
    if pdf:
        lines.append(f"H|{title[:120].encode('ascii','replace').decode()}|{pdf[:120]}")

# Marquee items: often <a href=pdf>title</a>
marquee = soup.find("marquee")
if marquee:
    for a in marquee.find_all("a", href=True):
        if ".pdf" in a["href"].lower() and len(a.get_text(strip=True)) >= 20:
            lines.append(
                f"M|{a.get_text(' ', strip=True)[:120].encode('ascii','replace').decode()}|{a['href'][:120]}"
            )

# Look for accordion / list in main
for sel in [".rightSide", ".leftSide", ".midContent", ".news", ".updates", "#Primary_content", ".Primary_content"]:
    nodes = soup.select(sel)
    lines.append(f"SEL {sel}={len(nodes)}")

# Dump first 3k of body text tags classes used heavily
from collections import Counter
classes = Counter()
for el in soup.find_all(True):
    for c in el.get("class") or []:
        classes[c] += 1
lines.append("TOP_CLASSES:")
for c, n in classes.most_common(30):
    lines.append(f"  {c}={n}")

(OUT / "police_deep.txt").write_text("\n".join(lines[:200]), encoding="utf-8")
print("wrote", len(lines), "lines; marquee links sample done")
