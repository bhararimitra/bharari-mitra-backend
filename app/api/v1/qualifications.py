"""Qualifications router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.qualifications.repository import QualificationRepository
from app.modules.qualifications.schemas import QualificationOut

router = APIRouter(prefix="/qualifications", tags=["Qualifications"])


@router.get("", response_model=list[QualificationOut])
async def list_qualifications(db: AsyncSession = Depends(get_db)):
    repo = QualificationRepository(db)
    return await repo.get_all()


@router.get("/{slug}", response_model=QualificationOut)
async def get_qualification(slug: str, db: AsyncSession = Depends(get_db)):
    repo = QualificationRepository(db)
    qual = await repo.get_by_slug(slug)
    if not qual:
        raise HTTPException(status_code=404, detail=f"Qualification '{slug}' not found.")
    return qual
