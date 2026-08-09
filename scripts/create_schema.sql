-- BharariMitra complete schema for local PostgreSQL
-- Database: bhararimitra
-- Apply with:
--   psql -U postgres -d bhararimitra -f scripts/create_schema.sql
-- Or from pgAdmin: open this file and Run.

BEGIN;

-- Enums
DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('active', 'closing_soon', 'closed', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE crawl_status AS ENUM ('running', 'success', 'failed', 'partial');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

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

-- organizations
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY,
    slug VARCHAR(120) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    official_url VARCHAR(512) NOT NULL,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_organizations_slug ON organizations (slug);

-- departments
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY,
    slug VARCHAR(120) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_departments_slug ON departments (slug);
CREATE INDEX IF NOT EXISTS ix_departments_organization_id ON departments (organization_id);

-- districts
CREATE TABLE IF NOT EXISTS districts (
    id UUID PRIMARY KEY,
    slug VARCHAR(120) NOT NULL UNIQUE,
    name VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_districts_slug ON districts (slug);

-- qualifications
CREATE TABLE IF NOT EXISTS qualifications (
    id UUID PRIMARY KEY,
    slug VARCHAR(120) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_qualifications_slug ON qualifications (slug);

-- jobs
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY,
    slug VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(512) NOT NULL,
    summary TEXT,
    organization_id UUID REFERENCES organizations (id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments (id) ON DELETE SET NULL,
    qualification_id UUID REFERENCES qualifications (id) ON DELETE SET NULL,
    district_id UUID REFERENCES districts (id) ON DELETE SET NULL,
    notification_url VARCHAR(1024),
    apply_url VARCHAR(1024),
    pdf_url VARCHAR(1024),
    vacancy_count INTEGER,
    salary_min INTEGER,
    salary_max INTEGER,
    age_min INTEGER,
    age_max INTEGER,
    published_at DATE,
    last_date DATE,
    status job_status NOT NULL DEFAULT 'active',
    notification_type notification_type NOT NULL DEFAULT 'job',
    content_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_jobs_slug ON jobs (slug);
CREATE INDEX IF NOT EXISTS ix_jobs_status ON jobs (status);
CREATE INDEX IF NOT EXISTS ix_jobs_notification_type ON jobs (notification_type);
CREATE INDEX IF NOT EXISTS ix_jobs_last_date ON jobs (last_date);
CREATE INDEX IF NOT EXISTS ix_jobs_published_at ON jobs (published_at);
CREATE INDEX IF NOT EXISTS ix_jobs_organization_id ON jobs (organization_id);
CREATE INDEX IF NOT EXISTS ix_jobs_department_id ON jobs (department_id);
CREATE INDEX IF NOT EXISTS ix_jobs_content_hash ON jobs (content_hash);

-- recruitment_events
CREATE TABLE IF NOT EXISTS recruitment_events (
    id UUID PRIMARY KEY,
    slug VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(512) NOT NULL,
    match_key VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'active',
    organization_id UUID REFERENCES organizations (id) ON DELETE SET NULL,
    department_id UUID REFERENCES departments (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_recruitment_events_slug ON recruitment_events (slug);
CREATE INDEX IF NOT EXISTS ix_recruitment_events_match_key ON recruitment_events (match_key);

ALTER TABLE jobs
ADD COLUMN IF NOT EXISTS recruitment_event_id UUID
REFERENCES recruitment_events (id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS ix_jobs_recruitment_event_id ON jobs (recruitment_event_id);

-- crawler_history
CREATE TABLE IF NOT EXISTS crawler_history (
    id UUID PRIMARY KEY,
    crawler_name VARCHAR(120) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status crawl_status NOT NULL DEFAULT 'running',
    records_added INTEGER NOT NULL DEFAULT 0,
    records_updated INTEGER NOT NULL DEFAULT 0,
    error TEXT
);
CREATE INDEX IF NOT EXISTS ix_crawler_history_crawler_name ON crawler_history (crawler_name);

-- Alembic version tracking (so alembic upgrade head is a no-op after this)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO alembic_version (version_num)
SELECT '003'
WHERE NOT EXISTS (SELECT 1 FROM alembic_version);

COMMIT;

-- Verify
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
