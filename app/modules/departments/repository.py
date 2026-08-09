import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.departments.models import Department


class DepartmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self) -> list[Department]:
        return list((await self._db.execute(
            select(Department).order_by(Department.name)
        )).scalars().all())

    async def get_by_slug(self, slug: str) -> Department | None:
        result = await self._db.execute(
            select(Department).where(Department.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self, slug: str, name: str, organization_id: uuid.UUID
    ) -> Department:
        dept = await self.get_by_slug(slug)
        if not dept:
            dept = Department(slug=slug, name=name, organization_id=organization_id)
            self._db.add(dept)
            await self._db.flush()
        return dept
