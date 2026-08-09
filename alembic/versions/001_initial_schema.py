"""Initial schema — all core tables.

Revision ID: 001
Revises:
Create Date: 2025-08-03
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    op.execute("CREATE TYPE job_status AS ENUM ('active','closing_soon','closed','unknown')")
    op.execute("CREATE TYPE crawl_status AS ENUM ('running','success','failed','partial')")

    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("official_url", sa.String(512), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("active", sa.Boolean, default=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"])

    # departments
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_departments_slug", "departments", ["slug"])
    op.create_index("ix_departments_organization_id", "departments", ["organization_id"])

    # districts
    op.create_table(
        "districts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_districts_slug", "districts", ["slug"])

    # qualifications
    op.create_table(
        "qualifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_qualifications_slug", "qualifications", ["slug"])

    # jobs
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("qualification_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("qualifications.id", ondelete="SET NULL"), nullable=True),
        sa.Column("district_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("districts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notification_url", sa.String(1024), nullable=True),
        sa.Column("apply_url", sa.String(1024), nullable=True),
        sa.Column("pdf_url", sa.String(1024), nullable=True),
        sa.Column("vacancy_count", sa.Integer, nullable=True),
        sa.Column("salary_min", sa.Integer, nullable=True),
        sa.Column("salary_max", sa.Integer, nullable=True),
        sa.Column("age_min", sa.Integer, nullable=True),
        sa.Column("age_max", sa.Integer, nullable=True),
        sa.Column("published_at", sa.Date, nullable=True),
        sa.Column("last_date", sa.Date, nullable=True),
        sa.Column("status", postgresql.ENUM("active", "closing_soon", "closed", "unknown",
                  name="job_status", create_type=False), nullable=False, server_default="active"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    for col in ["slug", "status", "last_date", "published_at",
                "organization_id", "department_id", "content_hash"]:
        op.create_index(f"ix_jobs_{col}", "jobs", [col])

    # crawler_history
    op.create_table(
        "crawler_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("crawler_name", sa.String(120), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", postgresql.ENUM("running", "success", "failed", "partial",
                  name="crawl_status", create_type=False), nullable=False, server_default="running"),
        sa.Column("records_added", sa.Integer, default=0, nullable=False),
        sa.Column("records_updated", sa.Integer, default=0, nullable=False),
        sa.Column("error", sa.Text, nullable=True),
    )
    op.create_index("ix_crawler_history_crawler_name", "crawler_history", ["crawler_name"])


def downgrade() -> None:
    op.drop_table("crawler_history")
    op.drop_table("jobs")
    op.drop_table("qualifications")
    op.drop_table("districts")
    op.drop_table("departments")
    op.drop_table("organizations")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS crawl_status")
