"""Classify crawled notification titles into NotificationType (CTO keyword rules).

Supports English and Marathi (Devanagari) titles from Maharashtra portals.
Word-boundary \\b is English-only; Marathi terms are matched as substrings.
"""

from __future__ import annotations

import re
import unicodedata

from app.modules.jobs.models import NotificationType

# Ordered: first match wins (most specific first).
_RULES: list[tuple[NotificationType, re.Pattern[str]]] = [
    (
        NotificationType.NOTICE,
        re.compile(
            r"(?:"
            r"\b(?:e[\s-]*tender|tender|quotation|rfp|rfq|auction|holiday\s*list|"
            r"local\s*holiday|gazette|empanelment|turnkey)\b"
            r"|election\s+commission|electoral\s+roll"
            r"|निविदा|दरपत्रक|टेंडर|खरेदी|लिलाव"
            r"|सुट्ट्या|सुट्टी\s*दिनदर्शिका|स्थानिक\s*सुट्ट"
            r"|निवडणूक\s*आयोग"
            r")",
            re.I,
        ),
    ),
    (
        NotificationType.HALL_TICKET,
        re.compile(
            r"(?:"
            r"\b(?:hall\s*ticket|admit\s*card|call\s*letter)\b"
            r"|प्रवेशपत्र|हॉल\s*तिकीट|हॉलतिकिट|ऍडमिट\s*कार्ड"
            r")",
            re.I,
        ),
    ),
    (
        NotificationType.ANSWER_KEY,
        re.compile(
            r"(?:"
            r"\b(?:answer\s*key|model\s*answer|key\s*answer)\b"
            r"|उत्तरसूची|उत्तर\s*सूची|आदर्श\s*उत्तर|उत्तरपत्रिका|उत्तरतालिका|उत्तर\s*तालिका"
            r")",
            re.I,
        ),
    ),
    (
        NotificationType.MERIT_LIST,
        re.compile(
            r"(?:"
            r"\b(?:merit\s*list|waiting\s*list|wait\s*list|select\s*list|"
            r"final\s*selection|provisional\s*selection|provisional\s*waiting|"
            r"cut[\s-]*off\s*list|cutoff\s*list)\b"
            r"|निवड\s*यादी|निवडयादी|निवडसूची|निवड\s*सूची"
            r"|प्रतीक्षा\s*यादी|प्रतीक्षायादी|प्रतीक्षासूची|प्रतीक्षा\s*सूची"
            r"|गुणवत्ता\s*यादी|गुणवत्तायादी"
            r"|तात्पुरती\s*यादी|अंतिम\s*यादी"
            r"|पात्र\s*उमेदवार[ां]*ची\s*.{0,40}यादी"
            r")",
            re.I,
        ),
    ),
    (
        NotificationType.RESULT,
        re.compile(
            r"(?:"
            r"\b(?:result|selection\s*list|final\s*result|exam\s*result|mark\s*sheet|marks?\s*list)\b"
            r"|निकाल|परीक्षा\s*निकाल|निवड\s*रद्द"
            r"|गुणांची\s*.{0,30}यादी|गुण\s*यादी|गुणपत्रक|गुणपत्रिक"
            r")",
            re.I,
        ),
    ),
    (
        NotificationType.CORRIGENDUM,
        re.compile(
            r"(?:"
            r"\b(?:corrigendum|addendum|extension|date\s*extended|revised\s*notification)\b"
            r"|शुद्धिपत्र|मुदत\s*वाढ|मुदतवाढ"
            r")",
            re.I,
        ),
    ),
    (
        NotificationType.ADVERTISEMENT,
        re.compile(
            r"(?:"
            r"\b(?:advertisement|advt\.?|notification|recruitment\s*notice)\b"
            r"|जाहीरात|जाहिरात"
            r")",
            re.I,
        ),
    ),
    (
        NotificationType.NOTICE,
        re.compile(
            r"(?:"
            r"\b(?:press\s*note|important\s*notice|public\s*notice|"
            r"announcement\s+regarding|exam(?:ination)?\s+pattern)\b"
            r"|सूचना|सुचना|कागदपत्र[े]?\s*पडताळणी|उपस्थित\s*राहणे"
            r"|नियुक्ती\s*बाबत|नेमणूक\s*बाबत"
            r"|मैदानी\s*चाचणी|लेखी\s*परीक्षा|पदाची\s*परीक्षा"
            r")",
            re.I,
        ),
    ),
]


def _normalize(text: str) -> str:
    """NFC + strip zero-width / soft-hyphen chars common in scraped Marathi HTML."""
    cleaned = unicodedata.normalize("NFC", text or "")
    return re.sub(r"[\u200b\u200c\u200d\u00ad]", "", cleaned)


def classify_notification(title: str, summary: str | None = None) -> NotificationType:
    """Return notification type from title/summary keywords; default JOB."""
    blob = _normalize(f"{title or ''} {summary or ''}").strip()
    if not blob:
        return NotificationType.JOB
    for ntype, pattern in _RULES:
        if pattern.search(blob):
            return ntype
    return NotificationType.JOB
