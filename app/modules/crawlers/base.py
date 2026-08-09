"""BaseCrawler — every government website crawler inherits this."""

import hashlib
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import get_logger
from app.modules.crawlers.models import CrawlerHistory, CrawlStatus
from app.modules.crawlers.repository import CrawlerHistoryRepository
from app.modules.crawlers.classify import classify_notification
from app.modules.jobs.models import Job, JobStatus
from app.modules.jobs.repository import JobRepository
from app.modules.organizations.repository import OrganizationRepository
from app.modules.departments.repository import DepartmentRepository
from app.modules.districts.repository import DistrictRepository
from app.modules.qualifications.repository import QualificationRepository
from app.modules.recruitments.linking import link_job_to_recruitment
from app.shared.exceptions import ValidationError
from slugify import slugify


class RawJobData:
    """Intermediate representation of a crawled job before saving."""

    def __init__(
        self,
        title: str,
        notification_url: str,
        apply_url: str | None = None,
        pdf_url: str | None = None,
        vacancy_count: int | None = None,
        salary_min: int | None = None,
        salary_max: int | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        published_at: str | None = None,
        last_date: str | None = None,
        summary: str | None = None,
        organization_slug: str = "",
        organization_name: str = "",
        organization_url: str = "",
        department_slug: str | None = None,
        department_name: str | None = None,
        district_slug: str | None = None,
        district_name: str | None = None,
        qualification_slug: str | None = None,
        qualification_name: str | None = None,
    ) -> None:
        self.title = title.strip()
        self.notification_url = notification_url.strip()
        self.apply_url = apply_url
        self.pdf_url = pdf_url
        self.vacancy_count = vacancy_count
        self.salary_min = salary_min
        self.salary_max = salary_max
        self.age_min = age_min
        self.age_max = age_max
        self.published_at = published_at
        self.last_date = last_date
        self.summary = summary
        self.organization_slug = organization_slug
        self.organization_name = organization_name
        self.organization_url = organization_url
        self.department_slug = department_slug
        self.department_name = department_name
        self.district_slug = district_slug
        self.district_name = district_name
        self.qualification_slug = qualification_slug
        self.qualification_name = qualification_name


class BaseCrawler(ABC):
    """
    Abstract base for all BharariMitra crawlers.

    Workflow per run:
        fetch() -> parse() -> normalize() -> validate() -> save()

    To add a new department: subclass BaseCrawler, implement the abstract
    methods, register in scheduler. Nothing else changes.
    """

    name: str  # e.g. "mpsc_crawler"
    source_url: str  # official website URL

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._logger = get_logger(self.__class__.__name__)
        self._history_repo = CrawlerHistoryRepository(db)
        self._job_repo = JobRepository(db)
        self._org_repo = OrganizationRepository(db)
        self._dept_repo = DepartmentRepository(db)
        self._district_repo = DistrictRepository(db)
        self._qual_repo = QualificationRepository(db)

    # ── Abstract interface ────────────────────────────────────────────────

    @abstractmethod
    async def fetch(self) -> Any:
        """Download raw page/content from the source. Return raw HTML/bytes/json."""

    @abstractmethod
    async def parse(self, raw: Any) -> list[RawJobData]:
        """Parse raw content into a list of RawJobData objects."""

    # ── Concrete helpers ──────────────────────────────────────────────────

    def normalize(self, raw: RawJobData) -> RawJobData:
        """Clean and normalise a RawJobData. Override to add custom logic."""
        raw.title = re.sub(r"\s+", " ", raw.title).strip()
        if raw.summary:
            raw.summary = re.sub(r"\s+", " ", raw.summary).strip()
        return raw

    def validate(self, raw: RawJobData) -> None:
        """Raise ValidationError if critical fields are missing or invalid."""
        if not raw.title:
            raise ValidationError("title", "Title cannot be empty.")
        if not raw.notification_url:
            raise ValidationError("notification_url", "notification_url is required.")
        if not raw.notification_url.startswith("http"):
            raise ValidationError("notification_url", f"Invalid URL: {raw.notification_url}")
        if not raw.organization_slug:
            raise ValidationError("organization_slug", "organization_slug is required.")

    def build_content_hash(self, raw: RawJobData) -> str:
        """SHA-256 hash of title + notification_url for duplicate detection."""
        content = f"{raw.title.lower()}|{raw.notification_url.lower()}"
        return hashlib.sha256(content.encode()).hexdigest()

    def build_slug(self, title: str, extra: str = "") -> str:
        # Keep uniqueness suffix intact — slugify truncation can drop a trailing hash.
        suffix = slugify(extra, max_length=40) if extra else ""
        if suffix:
            title_part = slugify(title, max_length=max(40, 220 - len(suffix) - 1))
            return f"{title_part}-{suffix}" if title_part else suffix
        return slugify(title, max_length=220)

    async def _parse_date(self, date_str: str | None):
        """Parse dd/mm/yyyy or yyyy-mm-dd to date. Returns None if invalid."""
        if not date_str:
            return None
        from datetime import date
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y", "%d %B %Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue
        self._logger.warning("unparseable_date", value=date_str)
        return None

    # ── Main run method ───────────────────────────────────────────────────

    async def run(self) -> CrawlerHistory:
        """Execute a full crawl run. Returns the history record."""
        record = await self._history_repo.start_run(self.name)
        self._logger.info("crawler_started", crawler=self.name)

        added = 0
        updated = 0
        error_msg: str | None = None

        try:
            raw_content = await self.fetch()
            raw_jobs = await self.parse(raw_content)
            self._logger.info("crawler_parsed", count=len(raw_jobs))

            for raw in raw_jobs:
                try:
                    raw = self.normalize(raw)
                    self.validate(raw)
                    result = await self._save_job(raw)
                    if result == "added":
                        added += 1
                    elif result == "updated":
                        updated += 1
                except ValidationError as e:
                    self._logger.warning("validation_failed", error=str(e))
                    continue
                except Exception as e:
                    await self._db.rollback()
                    self._logger.error("job_save_failed", error=str(e))
                    continue

            status = CrawlStatus.SUCCESS

        except Exception as e:
            error_msg = str(e)
            status = CrawlStatus.FAILED
            self._logger.error("crawler_failed", crawler=self.name, error=error_msg)

        await self._history_repo.finish_run(
            record,
            status=status,
            records_added=added,
            records_updated=updated,
            error=error_msg,
        )
        self._logger.info(
            "crawler_finished",
            crawler=self.name,
            status=status,
            added=added,
            updated=updated,
        )
        return record

    async def _save_job(self, raw: RawJobData) -> str:
        """Insert or update a job. Returns 'added' or 'updated' or 'skipped'."""
        content_hash = self.build_content_hash(raw)

        # Check duplicate
        existing = await self._job_repo.get_by_content_hash(content_hash)

        # Resolve FK entities
        org = await self._org_repo.get_or_create(
            raw.organization_slug, raw.organization_name, raw.organization_url
        )
        dept = None
        if raw.department_slug and raw.department_name:
            dept = await self._dept_repo.get_or_create(
                raw.department_slug, raw.department_name, org.id
            )
        district = None
        if raw.district_slug and raw.district_name:
            district = await self._district_repo.get_or_create(
                raw.district_slug, raw.district_name
            )
        qual = None
        if raw.qualification_slug and raw.qualification_name:
            qual = await self._qual_repo.get_or_create(
                raw.qualification_slug, raw.qualification_name
            )

        last_date = await self._parse_date(raw.last_date)
        published_at = await self._parse_date(raw.published_at)
        notification_type = classify_notification(raw.title, raw.summary)

        if existing:
            # Update mutable fields only
            existing.title = raw.title
            existing.summary = raw.summary
            existing.apply_url = raw.apply_url
            existing.pdf_url = raw.pdf_url
            existing.vacancy_count = raw.vacancy_count
            existing.last_date = last_date
            existing.notification_type = notification_type
            if not existing.recruitment_event_id:
                await link_job_to_recruitment(self._db, existing)
            await self._job_repo.update(existing)
            return "updated"

        # Create new — include content hash so truncated Marathi slugs stay unique
        # even before prior inserts are visible to get_by_slug in the same session.
        slug = self.build_slug(raw.title, f"{org.slug}-{content_hash[:8]}")
        if await self._job_repo.get_by_slug(slug):
            slug = self.build_slug(raw.title, f"{org.slug}-{content_hash[:16]}")

        job = Job(
            slug=slug,
            title=raw.title,
            summary=raw.summary,
            organization_id=org.id,
            department_id=dept.id if dept else None,
            district_id=district.id if district else None,
            qualification_id=qual.id if qual else None,
            notification_url=raw.notification_url,
            apply_url=raw.apply_url,
            pdf_url=raw.pdf_url,
            vacancy_count=raw.vacancy_count,
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            age_min=raw.age_min,
            age_max=raw.age_max,
            published_at=published_at,
            last_date=last_date,
            status=JobStatus.ACTIVE,
            notification_type=notification_type,
            content_hash=content_hash,
        )
        await self._job_repo.create(job)
        await link_job_to_recruitment(self._db, job)
        await self._job_repo.update(job)
        return "added"
