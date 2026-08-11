"""Job repository — all database access for jobs."""

import uuid
from datetime import date
from sqlalchemy import select, func, or_, desc, asc, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.modules.jobs.models import (
    Job,
    JobStatus,
    NotificationType,
    RECRUITMENT_NOTIFICATION_TYPES,
)
from app.shared.pagination import PaginationParams


class JobRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base_query(self):
        return select(Job).options(
            selectinload(Job.organization),
            selectinload(Job.department),
            selectinload(Job.qualification),
            selectinload(Job.district),
            selectinload(Job.recruitment_event),
        )

    async def get_by_slug(self, slug: str) -> Job | None:
        result = await self._db.execute(
            self._base_query().where(Job.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        result = await self._db.execute(
            self._base_query().where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        params: PaginationParams,
        status: JobStatus | None = None,
        organization_slug: str | None = None,
        department_slug: str | None = None,
        district_slug: str | None = None,
        qualification_slug: str | None = None,
        notification_type: NotificationType | None = None,
        notification_types: list[NotificationType] | None = None,
        sort_by: str = "published_at",
        sort_order: str = "desc",
    ) -> tuple[list[Job], int]:
        from app.modules.organizations.models import Organization
        from app.modules.departments.models import Department
        from app.modules.districts.models import District
        from app.modules.qualifications.models import Qualification

        q = self._base_query()

        if status:
            q = q.where(Job.status == status)
        if notification_type:
            q = q.where(Job.notification_type == notification_type)
        elif notification_types:
            q = q.where(Job.notification_type.in_(notification_types))
        if organization_slug:
            q = q.join(Organization).where(Organization.slug == organization_slug)
        if department_slug:
            q = q.join(Department).where(Department.slug == department_slug)
        if district_slug:
            q = q.join(District).where(District.slug == district_slug)
        if qualification_slug:
            q = q.join(Qualification).where(Qualification.slug == qualification_slug)

        # Sorting
        sort_col = getattr(Job, sort_by, Job.published_at)
        order_fn = desc if sort_order == "desc" else asc
        q = q.order_by(order_fn(sort_col))

        # Count
        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._db.execute(count_q)).scalar_one()

        # Paginate
        q = q.offset(params.offset).limit(params.limit)
        rows = (await self._db.execute(q)).scalars().all()
        return list(rows), total

    async def search(self, query: str, params: PaginationParams) -> tuple[list[Job], int]:
        q = self._base_query().where(
            or_(
                Job.title.ilike(f"%{query}%"),
                Job.summary.ilike(f"%{query}%"),
            )
        ).order_by(desc(Job.published_at))

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self._db.execute(count_q)).scalar_one()
        q = q.offset(params.offset).limit(params.limit)
        rows = (await self._db.execute(q)).scalars().all()
        return list(rows), total

    async def get_latest(self, limit: int = 10) -> list[Job]:
        q = self._base_query().where(
            Job.status == JobStatus.ACTIVE,
            Job.notification_type.in_(RECRUITMENT_NOTIFICATION_TYPES),
        ).order_by(desc(Job.published_at)).limit(limit)
        return list((await self._db.execute(q)).scalars().all())

    async def get_closing_soon(self, limit: int = 10) -> list[Job]:
        from datetime import date, timedelta
        today = date.today()
        soon = today + timedelta(days=7)
        q = self._base_query().where(
            Job.status == JobStatus.ACTIVE,
            Job.notification_type.in_(RECRUITMENT_NOTIFICATION_TYPES),
            Job.last_date >= today,
            Job.last_date <= soon,
        ).order_by(Job.last_date)
        return list((await self._db.execute(q)).scalars().all())

    async def get_by_notification_type(
        self, notification_type: NotificationType, limit: int = 10
    ) -> list[Job]:
        q = (
            self._base_query()
            .where(Job.notification_type == notification_type)
            .order_by(desc(Job.published_at))
            .limit(limit)
        )
        return list((await self._db.execute(q)).scalars().all())

    async def get_by_content_hash(self, content_hash: str) -> Job | None:
        result = await self._db.execute(
            select(Job).where(Job.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def list_by_recruitment_event(
        self, recruitment_event_id, exclude_id=None
    ) -> list[Job]:
        q = self._base_query().where(Job.recruitment_event_id == recruitment_event_id)
        if exclude_id is not None:
            q = q.where(Job.id != exclude_id)
        q = q.order_by(desc(Job.published_at))
        return list((await self._db.execute(q)).scalars().all())

    async def list_by_types(
        self,
        params: PaginationParams,
        types: list[NotificationType],
        organization_slug: str | None = None,
        department_slug: str | None = None,
    ) -> tuple[list[Job], int]:
        return await self.list_jobs(
            params=params,
            notification_types=types,
            organization_slug=organization_slug,
            department_slug=department_slug,
        )

    async def create(self, job: Job) -> Job:
        self._db.add(job)
        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def update(self, job: Job) -> Job:
        await self._db.flush()
        await self._db.refresh(job)
        return job

    async def count_expired(self, cutoff: date) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(Job)
            .where(Job.last_date.is_not(None), Job.last_date < cutoff)
        )
        return int(result.scalar_one())

    async def count_past_deadline(self, today: date) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(Job)
            .where(
                Job.last_date.is_not(None),
                Job.last_date < today,
                Job.status != JobStatus.CLOSED,
            )
        )
        return int(result.scalar_one())

    async def delete_expired(self, cutoff: date) -> int:
        result = await self._db.execute(
            delete(Job).where(Job.last_date.is_not(None), Job.last_date < cutoff)
        )
        await self._db.flush()
        return int(result.rowcount or 0)

    async def close_past_deadline(self, today: date) -> int:
        result = await self._db.execute(
            update(Job)
            .where(
                Job.last_date.is_not(None),
                Job.last_date < today,
                Job.status != JobStatus.CLOSED,
            )
            .values(status=JobStatus.CLOSED)
        )
        await self._db.flush()
        return int(result.rowcount or 0)
