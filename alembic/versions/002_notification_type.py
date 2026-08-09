"""Add notification_type to jobs.

Revision ID: 002
Revises: 001
Create Date: 2026-08-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE notification_type AS ENUM (
                'job',
                'advertisement',
                'corrigendum',
                'hall_ticket',
                'answer_key',
                'result',
                'merit_list',
                'notice'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        ALTER TABLE jobs
        ADD COLUMN IF NOT EXISTS notification_type notification_type
        NOT NULL DEFAULT 'job';
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_jobs_notification_type ON jobs (notification_type);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_jobs_notification_type;")
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS notification_type;")
    op.execute("DROP TYPE IF EXISTS notification_type;")
