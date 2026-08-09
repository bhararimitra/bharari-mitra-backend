"""Departments router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.departments.repository import DepartmentRepository
from app.modules.departments.schemas import DepartmentOut

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=list[DepartmentOut])
async def list_departments(db: AsyncSession = Depends(get_db)):
    repo = DepartmentRepository(db)
    return await repo.get_all()


@router.get("/{slug}", response_model=DepartmentOut)
async def get_department(slug: str, db: AsyncSession = Depends(get_db)):
    repo = DepartmentRepository(db)
    dept = await repo.get_by_slug(slug)
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department '{slug}' not found.")
    return dept
