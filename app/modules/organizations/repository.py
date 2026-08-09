from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.organizations.models import Organization


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self, active_only: bool = True) -> list[Organization]:
        q = select(Organization)
        if active_only:
            q = q.where(Organization.active == True)  # noqa: E712
        q = q.order_by(Organization.name)
        return list((await self._db.execute(q)).scalars().all())

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, slug: str, name: str, official_url: str) -> Organization:
        org = await self.get_by_slug(slug)
        if not org:
            org = Organization(slug=slug, name=name, official_url=official_url)
            self._db.add(org)
            await self._db.flush()
        return org
