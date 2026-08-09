"""Dump axios interceptor region from MPSC main/vendor JS."""

from pathlib import Path

OUT = Path(__file__).resolve().parent / "_probe_out"
js = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in OUT.glob("_static_js_*.js"))

idx = js.find("interceptors.request")
print("interceptors.request at", idx)
(OUT / "axios_interceptor.txt").write_text(js[max(0, idx - 500) : idx + 4000], encoding="utf-8")

# Also search for headers["CRC"] or .CRC =
for key in ['["CRC"]', "['CRC']", ".CRC=", "CRC:", '"CRC"', "headers.CRC", "setRequestHeader"]:
    i = js.find(key)
    print(key, i)
    if i >= 0:
        (OUT / f"key_{key.strip(chr(34)+chr(39)+'[]=.')} .txt".replace(" ", "_")).write_text(
            js[max(0, i - 800) : i + 800], encoding="utf-8"
        )

# Find encrypt function used for request
for key in ["encrypt", "Encrypt", "AES", "CryptoJS", "JSEncrypt", "forge", "crc32", "CRC32"]:
    count = js.count(key)
    print(f"{key} count={count}")

# Look near getwebcontents call site
i = js.find("getwebcontents")
(OUT / "getwebcontents_site.txt").write_text(js[max(0, i - 1500) : i + 1500], encoding="utf-8")
i = js.find("getallcontent")
(OUT / "getallcontent_site.txt").write_text(js[max(0, i - 1500) : i + 1500], encoding="utf-8")
print("done")
