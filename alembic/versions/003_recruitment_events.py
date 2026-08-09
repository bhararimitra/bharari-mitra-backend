"""Add recruitment_events and jobs.recruitment_event_id.

Revision ID: 003
Revises: 002
Create Date: 2026-08-08
"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS recruitment_events (
            id UUID PRIMARY KEY,
            slug VARCHAR(255) NOT NULL UNIQUE,
            title VARCHAR(512) NOT NULL,
            match_key VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(40) NOT NULL DEFAULT 'active',
            organization_id UUID REFERENCES organizations (id) ON DELETE SET NULL,
            department_id UUID REFERENCES departments (id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_recruitment_events_slug ON recruitment_events (slug);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_recruitment_events_match_key ON recruitment_events (match_key);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_recruitment_events_organization_id ON recruitment_events (organization_id);"
    )
    op.execute(
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS recruitment_event_id UUID
        REFERENCES recruitment_events (id) ON DELETE SET NULL;
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_jobs_recruitment_event_id ON jobs (recruitment_event_id);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_jobs_recruitment_event_id;")
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS recruitment_event_id;")
    op.execute("DROP TABLE IF EXISTS recruitment_events;")
