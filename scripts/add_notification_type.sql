-- Incremental: add notification_type for existing local DBs
BEGIN;

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

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS notification_type notification_type
NOT NULL DEFAULT 'job';

CREATE INDEX IF NOT EXISTS ix_jobs_notification_type ON jobs (notification_type);

UPDATE alembic_version SET version_num = '002'
WHERE version_num = '001';

INSERT INTO alembic_version (version_num)
SELECT '002'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version);

COMMIT;
