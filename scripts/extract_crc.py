"""Extract CRC header generation from MPSC JS bundles."""

from __future__ import annotations

import re
from pathlib import Path

OUT = Path(__file__).resolve().parent / "_probe_out"
js = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in OUT.glob("_static_js_*.js"))

# Find axios interceptor / CRC assignment snippets
patterns = [
    r".{0,300}CRC.{0,300}",
    r"headers\[[^\]]{0,40}\]\s*=\s*[^;]{0,200}",
    r"CRC[A-Za-z_]*\s*[:=]\s*[^,;}]{0,200}",
    r"crypto|CryptoJS|md5|sha256|hmac|btoa\([^)]{0,80}\)",
]

found = []
for pat in patterns:
    for m in re.finditer(pat, js, flags=re.I):
        found.append(m.group(0))

# Deduplicate and write
uniq = []
seen = set()
for f in found:
    key = f[:120]
    if key not in seen:
        seen.add(key)
        uniq.append(f)

(OUT / "crc_deep.txt").write_text("\n\n====\n\n".join(uniq[:80]), encoding="utf-8")
print(f"wrote {len(uniq[:80])} snippets")

# Specifically search for 'CRC' near 'headers'
for m in re.finditer(r".{0,500}headers.{0,200}CRC.{0,200}|.{0,200}CRC.{0,200}headers.{0,500}", js, flags=re.I):
    (OUT / "crc_headers_near.txt").write_text(
        ((OUT / "crc_headers_near.txt").read_text(encoding="utf-8") if (OUT / "crc_headers_near.txt").exists() else "")
        + "\n\n====\n\n"
        + m.group(0),
        encoding="utf-8",
    )
print("done headers near")

# Look for request interceptor function body containing CRC
idx = js.find("CRC header")
print("CRC header idx", idx)
idx2 = js.find("CRC_VALUE_NOT_MATCH")
print("CRC_VALUE idx", idx2)
if idx2 > 0:
    snippet = js[max(0, idx2 - 2500) : idx2 + 1500]
    (OUT / "crc_around_error.txt").write_text(snippet, encoding="utf-8")
    print("wrote crc_around_error.txt len", len(snippet))

# Search encrypt / hash helpers near axios create
for key in ["isactiveadvertisment", "getwebcontents", "getallcontent", "interceptors.request", "CRC"]:
    positions = [m.start() for m in re.finditer(re.escape(key), js)]
    print(key, "count", len(positions))
