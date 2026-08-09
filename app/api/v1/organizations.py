"""Organizations router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import OrganizationOut

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=list[OrganizationOut])
async def list_organizations(db: AsyncSession = Depends(get_db)):
    repo = OrganizationRepository(db)
    return await repo.get_all(active_only=True)


@router.get("/{slug}", response_model=OrganizationOut)
async def get_organization(slug: str, db: AsyncSession = Depends(get_db)):
    repo = OrganizationRepository(db)
    org = await repo.get_by_slug(slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{slug}' not found.")
    return org
