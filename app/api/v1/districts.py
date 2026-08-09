"""Districts router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.districts.repository import DistrictRepository
from app.modules.districts.schemas import DistrictOut

router = APIRouter(prefix="/districts", tags=["Districts"])


@router.get("", response_model=list[DistrictOut])
async def list_districts(db: AsyncSession = Depends(get_db)):
    repo = DistrictRepository(db)
    return await repo.get_all()


@router.get("/{slug}", response_model=DistrictOut)
async def get_district(slug: str, db: AsyncSession = Depends(get_db)):
    repo = DistrictRepository(db)
    dist = await repo.get_by_slug(slug)
    if not dist:
        raise HTTPException(status_code=404, detail=f"District '{slug}' not found.")
    return dist
