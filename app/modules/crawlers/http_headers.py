"""Shared HTTP defaults for government site crawlers."""

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BharariMitraBot/1.0; "
        "+https://bhararimitra.in/bot)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,mr;q=0.8",
}

HTTP_TIMEOUT = 40.0
