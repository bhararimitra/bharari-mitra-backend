"""District model — Maharashtra districts."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, UUIDMixin, TimestampMixin


class District(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "districts"

    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    jobs: Mapped[list["Job"]] = relationship(  # noqa: F821
        "Job", back_populates="district", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<District slug={self.slug}>"
