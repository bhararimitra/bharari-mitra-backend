"""Job model — core recruitment notification."""

import uuid
from datetime import date
from sqlalchemy import String, Text, Integer, Date, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base, UUIDMixin, TimestampMixin
import enum


class JobStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSING_SOON = "closing_soon"
    CLOSED = "closed"
    UNKNOWN = "unknown"


class NotificationType(str, enum.Enum):
    JOB = "job"
    ADVERTISEMENT = "advertisement"
    CORRIGENDUM = "corrigendum"
    HALL_TICKET = "hall_ticket"
    ANSWER_KEY = "answer_key"
    RESULT = "result"
    MERIT_LIST = "merit_list"
    NOTICE = "notice"


# Types shown on the main jobs / latest listings (not hall tickets/results).
RECRUITMENT_NOTIFICATION_TYPES: tuple[NotificationType, ...] = (
    NotificationType.JOB,
    NotificationType.ADVERTISEMENT,
)


class Job(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "jobs"

    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    notification_type: Mapped[NotificationType] = mapped_column(
        SAEnum(
            NotificationType,
            name="notification_type",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=NotificationType.JOB,
        nullable=False,
        index=True,
    )

    # Foreign keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
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
    qualification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qualifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    district_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("districts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recruitment_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recruitment_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Job details
    notification_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    apply_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    vacancy_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Dates
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    last_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Status and dedup
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(
            JobStatus,
            name="job_status",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        default=JobStatus.ACTIVE,
        nullable=False,
        index=True,
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(  # noqa: F821
        "Organization", back_populates="jobs"
    )
    department: Mapped["Department | None"] = relationship(  # noqa: F821
        "Department", back_populates="jobs"
    )
    qualification: Mapped["Qualification | None"] = relationship(  # noqa: F821
        "Qualification", back_populates="jobs"
    )
    district: Mapped["District | None"] = relationship(  # noqa: F821
        "District", back_populates="jobs"
    )
    recruitment_event: Mapped["RecruitmentEvent | None"] = relationship(  # noqa: F821
        "RecruitmentEvent",
        back_populates="items",
    )


# Ensure related mappers are registered for string relationship names.
from app.modules.recruitments.models import RecruitmentEvent  # noqa: E402, F401

