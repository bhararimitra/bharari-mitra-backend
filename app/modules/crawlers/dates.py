"""Pull last-apply dates out of notification titles when crawlers omit them."""

from __future__ import annotations

import re
from datetime import datetime

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_DMY = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b")
_MON = re.compile(
    r"\b(\d{1,2})\s*(?:st|nd|rd|th)?[\s.\-]*"
    r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
    r"Nov(?:ember)?|Dec(?:ember)?)"
    r"[\s.\-]*(20\d{2})\b",
    re.I,
)
_LAST_HINT = re.compile(
    r"(last\s*date|closing\s*date|apply\s*by|last\s*date\s*to\s*apply|"
    r"upto|up\s*to|till|deadline|"
    r"अंतिम\s*दिनांक|अर्ज.{0,20}शेवट|मुदत)",
    re.I,
)


def _latin_digits(text: str) -> str:
    return (text or "").translate(_DEVANAGARI_DIGITS)


def _iso_dmy(day: str, month: str, year: str) -> str | None:
    try:
        d = datetime(int(year), int(month), int(day)).date()
    except ValueError:
        return None
    return d.strftime("%d/%m/%Y")


def dates_in_text(text: str) -> list[str]:
    blob = _latin_digits(text)
    found: list[str] = []
    seen: set[str] = set()
    for day, month, year in _DMY.findall(blob):
        iso = _iso_dmy(day, month, year)
        if iso and iso not in seen:
            seen.add(iso)
            found.append(iso)
    for day, mon, year in _MON.findall(blob):
        try:
            parsed = datetime.strptime(f"{int(day):02d} {mon[:3].title()} {year}", "%d %b %Y")
        except ValueError:
            continue
        iso = parsed.strftime("%d/%m/%Y")
        if iso not in seen:
            seen.add(iso)
            found.append(iso)
    return found


def infer_last_date(text: str) -> str | None:
    """Return dd/mm/yyyy last-apply date when the text actually implies one.

    A single unmatched date is usually the publication date — do not treat it
    as a deadline. Two dates (start–end) or an explicit last-date hint are ok.
    """
    blob = _latin_digits(text)
    found = dates_in_text(blob)
    if not found:
        return None
    if _LAST_HINT.search(blob):
        return found[-1]
    if len(found) >= 2:
        return max(found, key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
    return None
