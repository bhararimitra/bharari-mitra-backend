from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.qualifications.models import Qualification


class QualificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_all(self) -> list[Qualification]:
        return list((await self._db.execute(
            select(Qualification).order_by(Qualification.name)
        )).scalars().all())

    async def get_by_slug(self, slug: str) -> Qualification | None:
        result = await self._db.execute(
            select(Qualification).where(Qualification.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, slug: str, name: str) -> Qualification:
        q = await self.get_by_slug(slug)
        if not q:
            q = Qualification(slug=slug, name=name)
            self._db.add(q)
            await self._db.flush()
        return q
