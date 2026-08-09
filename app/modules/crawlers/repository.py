"""CrawlerHistory repository."""

from datetime import datetime, timezone
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.crawlers.models import CrawlerHistory, CrawlStatus


class CrawlerHistoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def start_run(self, crawler_name: str) -> CrawlerHistory:
        record = CrawlerHistory(
            crawler_name=crawler_name,
            started_at=datetime.now(timezone.utc),
            status=CrawlStatus.RUNNING,
        )
        self._db.add(record)
        await self._db.flush()
        return record

    async def finish_run(
        self,
        record: CrawlerHistory,
        status: CrawlStatus,
        records_added: int = 0,
        records_updated: int = 0,
        error: str | None = None,
    ) -> CrawlerHistory:
        record.finished_at = datetime.now(timezone.utc)
        record.status = status
        record.records_added = records_added
        record.records_updated = records_updated
        record.error = error
        await self._db.flush()
        return record

    async def get_recent(self, crawler_name: str, limit: int = 5) -> list[CrawlerHistory]:
        q = (
            select(CrawlerHistory)
            .where(CrawlerHistory.crawler_name == crawler_name)
            .order_by(desc(CrawlerHistory.started_at))
            .limit(limit)
        )
        return list((await self._db.execute(q)).scalars().all())
