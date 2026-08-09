"""Qualification model — minimum educational qualification."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDMixin, TimestampMixin


class Qualification(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "qualifications"

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job", back_populates="qualification", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Qualification slug={self.slug}>"
