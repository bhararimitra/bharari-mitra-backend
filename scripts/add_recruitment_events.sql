-- Incremental: recruitment_events + jobs.recruitment_event_id
BEGIN;

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
CREATE INDEX IF NOT EXISTS ix_recruitment_events_slug ON recruitment_events (slug);
CREATE INDEX IF NOT EXISTS ix_recruitment_events_match_key ON recruitment_events (match_key);
CREATE INDEX IF NOT EXISTS ix_recruitment_events_organization_id ON recruitment_events (organization_id);

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS recruitment_event_id UUID
REFERENCES recruitment_events (id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS ix_jobs_recruitment_event_id ON jobs (recruitment_event_id);

UPDATE alembic_version SET version_num = '003' WHERE version_num IN ('001', '002');
INSERT INTO alembic_version (version_num)
SELECT '003'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version);

COMMIT;
