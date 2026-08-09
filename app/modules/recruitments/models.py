"""Recruitment event — parent lifecycle for related jobs/updates."""

from __future__ import annotations

import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base, UUIDMixin, TimestampMixin


class RecruitmentEvent(Base, UUIDMixin, TimestampMixin):
    """One recruitment campaign that groups jobs, hall tickets, results, etc."""

    __tablename__ = "recruitment_events"

    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    # Normalized key for matching related updates (org-scoped).
    match_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    organization: Mapped["Organization | None"] = relationship(  # noqa: F821
        "Organization"
    )
    department: Mapped["Department | None"] = relationship(  # noqa: F821
        "Department"
    )
    items: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job",
        back_populates="recruitment_event",
    )

    def __repr__(self) -> str:
        return f"<RecruitmentEvent slug={self.slug}>"
