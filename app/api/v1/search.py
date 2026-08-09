"""Search router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.jobs.service import JobService
from app.modules.jobs.schemas import JobListItem
from app.shared.pagination import PaginationParams, PaginatedResponse

router = APIRouter(tags=["Search"])


@router.get("/search", response_model=PaginatedResponse[JobListItem])
async def search_jobs(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search across job titles and summaries."""
    service = JobService(db)
    params = PaginationParams(page=page, page_size=page_size)
    return await service.search(q, params)
