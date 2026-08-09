"""CrawlerHistory model — records every crawl run."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, UUIDMixin
import enum


class CrawlStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class CrawlerHistory(Base, UUIDMixin):
    __tablename__ = "crawler_history"

    crawler_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[CrawlStatus] = mapped_column(
        SAEnum(
            CrawlStatus,
            name="crawl_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=CrawlStatus.RUNNING,
        nullable=False,
    )
    records_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CrawlerHistory crawler={self.crawler_name} status={self.status}>"
