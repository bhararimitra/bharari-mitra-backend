"""Link crawled items into recruitment_events by org + normalized title key."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.modules.jobs.models import Job, NotificationType
from app.modules.recruitments.models import RecruitmentEvent

# Strip type-specific noise so "Police Constable Hall Ticket" ≈ "Police Constable Recruitment"
_STRIP_PATTERNS = [
    r"\bhall\s*tickets?\b",
    r"\badmit\s*cards?\b",
    r"\bcall\s*letters?\b",
    r"\banswer\s*keys?\b",
    r"\bmodel\s*answers?\b",
    r"\bmerit\s*lists?\b",
    r"\bwaiting\s*lists?\b",
    r"\bwait\s*lists?\b",
    r"\bselection\s*lists?\b",
    r"\bfinal\s*selection\b",
    r"\bfinal\s*results?\b",
    r"\bexam\s*results?\b",
    r"\bresults?\b",
    r"\bcorrigendums?\b",
    r"\baddendums?\b",
    r"\bextensions?\b",
    r"\bdate\s*extended\b",
    r"\brevised\s*notifications?\b",
    r"\badvertisements?\b",
    r"\badvt\.?\b",
    r"\bnotifications?\b",
    r"\brecruitments?\b",
    r"\breleased?\b",
    r"\bdeclared?\b",
    r"\bpublished?\b",
    r"\bdownload\b",
    r"\bonline\b",
    r"\bfor\s+the\b",
]


def normalize_match_key(title: str) -> str:
    """Produce a stable org-scoped key from a title."""
    text = (title or "").lower()
    text = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
    for pattern in _STRIP_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.I)
    text = re.sub(r"\b(19|20)\d{2}\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Keep enough tokens for matching; slugify for storage.
    key = slugify(text, max_length=200) or "recruitment"
    return key


def display_title_from_key(match_key: str, fallback_title: str) -> str:
    words = match_key.replace("-", " ").strip()
    if not words or words == "recruitment":
        return fallback_title.strip()[:512]
    titled = " ".join(w.capitalize() for w in words.split())
    return f"{titled} Recruitment"[:512]


async def get_or_create_recruitment_event(
    db: AsyncSession,
    *,
    title: str,
    organization_id: uuid.UUID | None,
    department_id: uuid.UUID | None,
    notification_type: NotificationType,
) -> RecruitmentEvent | None:
    """Find or create a recruitment event for this update."""
    match_key = normalize_match_key(title)
    if not match_key or match_key == "recruitment":
        # Too generic — only attach if we already have an exact org+key later.
        match_key = slugify(title, max_length=200) or "item"

    q = select(RecruitmentEvent).where(RecruitmentEvent.match_key == match_key)
    if organization_id:
        q = q.where(RecruitmentEvent.organization_id == organization_id)
    else:
        q = q.where(RecruitmentEvent.organization_id.is_(None))

    existing = (await db.execute(q)).scalar_one_or_none()
    if existing:
        return existing

    # Only create a new event from job/advertisement seeds (or if nothing matches).
    display = display_title_from_key(match_key, title)
    slug_base = slugify(display, max_length=200) or match_key
    slug = slug_base
    # Ensure unique slug
    for i in range(0, 20):
        clash = (
            await db.execute(select(RecruitmentEvent).where(RecruitmentEvent.slug == slug))
        ).scalar_one_or_none()
        if not clash:
            break
        slug = f"{slug_base}-{i + 2}"

    event = RecruitmentEvent(
        slug=slug,
        title=display,
        match_key=match_key,
        organization_id=organization_id,
        department_id=department_id,
        status="active",
    )
    db.add(event)
    await db.flush()
    return event


async def link_job_to_recruitment(db: AsyncSession, job: Job) -> RecruitmentEvent | None:
    """Assign recruitment_event_id on a job row."""
    event = await get_or_create_recruitment_event(
        db,
        title=job.title,
        organization_id=job.organization_id,
        department_id=job.department_id,
        notification_type=job.notification_type,
    )
    if event:
        job.recruitment_event_id = event.id
    return event
