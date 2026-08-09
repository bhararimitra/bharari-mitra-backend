"""Typed notification list aliases (hall tickets, results, notifications feed)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.jobs.service import JobService
from app.modules.jobs.schemas import JobListItem
from app.modules.jobs.models import NotificationType
from app.shared.pagination import PaginationParams, PaginatedResponse

router = APIRouter(tags=["Notifications"])


def _job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


async def _list_type(
    notification_type: NotificationType,
    page: int,
    page_size: int,
    service: JobService,
    organization: str | None = None,
    department: str | None = None,
) -> PaginatedResponse:
    params = PaginationParams(page=page, page_size=page_size)
    return await service.list_by_type(
        notification_type,
        params,
        organization_slug=organization,
        department_slug=department,
    )


@router.get("/notifications", response_model=PaginatedResponse[JobListItem])
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    organization: str | None = None,
    department: str | None = None,
    service: JobService = Depends(_job_service),
):
    """Recruitment notifications / notices / corrigenda (not jobs or results)."""
    params = PaginationParams(page=page, page_size=page_size)
    return await service.list_notifications(
        params, organization_slug=organization, department_slug=department
    )


@router.get("/halltickets", response_model=PaginatedResponse[JobListItem])
@router.get("/hall-tickets", response_model=PaginatedResponse[JobListItem])
async def list_hall_tickets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    organization: str | None = None,
    department: str | None = None,
    service: JobService = Depends(_job_service),
):
    return await _list_type(
        NotificationType.HALL_TICKET, page, page_size, service, organization, department
    )


@router.get("/results", response_model=PaginatedResponse[JobListItem])
async def list_results(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    organization: str | None = None,
    department: str | None = None,
    service: JobService = Depends(_job_service),
):
    return await _list_type(
        NotificationType.RESULT, page, page_size, service, organization, department
    )


@router.get("/answer-keys", response_model=PaginatedResponse[JobListItem])
async def list_answer_keys(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    organization: str | None = None,
    department: str | None = None,
    service: JobService = Depends(_job_service),
):
    return await _list_type(
        NotificationType.ANSWER_KEY, page, page_size, service, organization, department
    )


@router.get("/merit-lists", response_model=PaginatedResponse[JobListItem])
@router.get("/selection-lists", response_model=PaginatedResponse[JobListItem])
async def list_merit_lists(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    organization: str | None = None,
    department: str | None = None,
    service: JobService = Depends(_job_service),
):
    return await _list_type(
        NotificationType.MERIT_LIST, page, page_size, service, organization, department
    )
