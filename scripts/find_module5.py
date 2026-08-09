"""Locate webpack module 5 (CRC/encrypt helpers) in MPSC JS."""

from pathlib import Path
import re

OUT = Path(__file__).resolve().parent / "_probe_out"
# Prefer vendor chunk which usually has helpers
files = list(OUT.glob("_static_js_*.js"))
print("files", [f.name for f in files])

for f in files:
    js = f.read_text(encoding="utf-8", errors="replace")
    # webpack: 5:function(e,t,a){...
    for m in re.finditer(r"(?:^|[,{])5:function\(e,t,a\)\{", js):
        start = m.start()
        print(f.name, "module5 at", start)
        (OUT / f"module5_{f.name}.txt").write_text(js[start : start + 8000], encoding="utf-8")

    # Also search for CryptoJS / AES patterns
    for key in ["AES.encrypt", "AES.decrypt", "CryptoJS", "enc.Utf8", "mode.CBC", "Pad.Pkcs7", "createHash", "md5("]:
        if key in js:
            i = js.find(key)
            print(f.name, key, "at", i)
            (OUT / f"crypto_{key.replace('.','_')}_{f.name}.txt").write_text(
                js[max(0, i - 1000) : i + 2000], encoding="utf-8"
            )
