"""Job service — business logic layer."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.jobs.repository import JobRepository
from app.modules.jobs.models import Job, NotificationType, RECRUITMENT_NOTIFICATION_TYPES
from app.modules.jobs.schemas import JobFilters, JobDetail, JobListItem
from app.shared.pagination import PaginationParams, PaginatedResponse
from app.shared.exceptions import NotFoundError

NOTIFICATION_FEED_TYPES: tuple[NotificationType, ...] = (
    NotificationType.ADVERTISEMENT,
    NotificationType.NOTICE,
    NotificationType.CORRIGENDUM,
)


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = JobRepository(db)

    async def list_jobs(
        self, params: PaginationParams, filters: JobFilters
    ) -> PaginatedResponse[Job]:
        notification_types = None
        if filters.notification_type is None and filters.recruitment_only:
            notification_types = list(RECRUITMENT_NOTIFICATION_TYPES)

        items, total = await self._repo.list_jobs(
            params=params,
            status=filters.status,
            organization_slug=filters.organization_slug,
            department_slug=filters.department_slug,
            district_slug=filters.district_slug,
            qualification_slug=filters.qualification_slug,
            notification_type=filters.notification_type,
            notification_types=notification_types,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
        )
        return PaginatedResponse.create(items, total, params)

    async def list_by_type(
        self,
        notification_type: NotificationType,
        params: PaginationParams,
        sort_by: str = "published_at",
        sort_order: str = "desc",
        organization_slug: str | None = None,
        department_slug: str | None = None,
    ) -> PaginatedResponse[Job]:
        items, total = await self._repo.list_jobs(
            params=params,
            notification_type=notification_type,
            organization_slug=organization_slug,
            department_slug=department_slug,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return PaginatedResponse.create(items, total, params)

    async def list_notifications(
        self,
        params: PaginationParams,
        organization_slug: str | None = None,
        department_slug: str | None = None,
    ) -> PaginatedResponse[Job]:
        items, total = await self._repo.list_by_types(
            params=params,
            types=list(NOTIFICATION_FEED_TYPES),
            organization_slug=organization_slug,
            department_slug=department_slug,
        )
        return PaginatedResponse.create(items, total, params)

    async def get_by_slug(self, slug: str) -> Job:
        job = await self._repo.get_by_slug(slug)
        if not job:
            raise NotFoundError("Job", slug)
        return job

    async def get_detail(self, slug: str) -> JobDetail:
        job = await self.get_by_slug(slug)
        related: list[Job] = []
        if job.recruitment_event_id:
            related = await self._repo.list_by_recruitment_event(
                job.recruitment_event_id, exclude_id=job.id
            )
        detail = JobDetail.model_validate(job)
        detail.related_updates = [JobListItem.model_validate(r) for r in related]
        return detail

    async def search(
        self, query: str, params: PaginationParams
    ) -> PaginatedResponse[Job]:
        items, total = await self._repo.search(query, params)
        return PaginatedResponse.create(items, total, params)

    async def get_latest(self, limit: int = 10) -> list[Job]:
        return await self._repo.get_latest(limit)

    async def get_closing_soon(self, limit: int = 10) -> list[Job]:
        return await self._repo.get_closing_soon(limit)

    async def get_by_type(self, notification_type: NotificationType, limit: int = 10) -> list[Job]:
        return await self._repo.get_by_notification_type(notification_type, limit)
