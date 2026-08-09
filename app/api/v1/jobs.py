"""Jobs router — recruitment-facing job endpoints."""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.jobs.service import JobService
from app.modules.jobs.schemas import JobListItem, JobDetail, JobFilters
from app.modules.jobs.models import JobStatus, NotificationType
from app.shared.pagination import PaginationParams, PaginatedResponse
from app.shared.exceptions import NotFoundError
from app.shared.cache import cache_get, cache_set

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(db)


@router.get("", response_model=PaginatedResponse[JobListItem])
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: JobStatus | None = None,
    organization: str | None = None,
    department: str | None = None,
    district: str | None = None,
    qualification: str | None = None,
    notification_type: NotificationType | None = None,
    sort_by: str = Query(default="published_at", pattern="^(published_at|last_date|vacancy_count)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    service: JobService = Depends(_job_service),
):
    """List recruitment jobs (job + advertisement by default)."""
    params = PaginationParams(page=page, page_size=page_size)
    filters = JobFilters(
        status=status,
        organization_slug=organization,
        department_slug=department,
        district_slug=district,
        qualification_slug=qualification,
        notification_type=notification_type,
        recruitment_only=notification_type is None,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return await service.list_jobs(params, filters)


@router.get("/latest", response_model=list[JobListItem])
async def get_latest(
    limit: int = Query(default=10, ge=1, le=50),
    service: JobService = Depends(_job_service),
):
    """Return the latest active job/advertisement notifications."""
    cache_key = f"latest_jobs:{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    jobs = await service.get_latest(limit)
    result = [JobListItem.model_validate(j).model_dump(mode="json") for j in jobs]
    await cache_set(cache_key, result)
    return result


@router.get("/closing-soon", response_model=list[JobListItem])
async def get_closing_soon(
    limit: int = Query(default=10, ge=1, le=50),
    service: JobService = Depends(_job_service),
):
    """Return jobs closing within 7 days."""
    jobs = await service.get_closing_soon(limit)
    return jobs


@router.get("/{slug}", response_model=JobDetail)
async def get_job(slug: str, service: JobService = Depends(_job_service)):
    """Return full details for a single job, including related recruitment updates."""
    try:
        return await service.get_detail(slug)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
