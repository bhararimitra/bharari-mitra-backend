from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.districts.models import District


class DistrictRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self) -> list[District]:
        return list((await self._db.execute(
            select(District).order_by(District.name)
        )).scalars().all())

    async def get_by_slug(self, slug: str) -> District | None:
        result = await self._db.execute(
            select(District).where(District.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, slug: str, name: str) -> District:
        d = await self.get_by_slug(slug)
        if not d:
            d = District(slug=slug, name=name)
            self._db.add(d)
            await self._db.flush()
        return d
