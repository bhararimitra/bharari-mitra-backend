# BharariMitra Backend

FastAPI backend for the BharariMitra Maharashtra Government Jobs platform.

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL · Redis · APScheduler · Docker

---

## Quick Start (Local)

### 1. Prerequisites
- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (for containerised setup)

### 2. Setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Run Migrations

```bash
alembic upgrade head
```

### 4. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

---

## Docker (Recommended)

```bash
cp .env.example .env
# Set POSTGRES_PASSWORD in .env

docker compose up --build
```

Services started:
- API: http://localhost:8000
- Postgres: localhost:5432
- Redis: localhost:6379
- Nginx: http://localhost:80

---

## Run Migrations in Docker

```bash
docker compose exec api alembic upgrade head
```

---

## Public API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/jobs` | List jobs (filterable, paginated) |
| GET | `/api/v1/jobs/latest` | Latest active notifications |
| GET | `/api/v1/jobs/closing-soon` | Closing within 7 days |
| GET | `/api/v1/jobs/{slug}` | Job detail |
| GET | `/api/v1/search?q=` | Full-text search |
| GET | `/api/v1/departments` | All departments |
| GET | `/api/v1/departments/{slug}` | Department detail |
| GET | `/api/v1/districts` | All districts |
| GET | `/api/v1/districts/{slug}` | District detail |
| GET | `/api/v1/qualifications` | All qualifications |
| GET | `/api/v1/organizations` | All organizations |

Query parameters for `/api/v1/jobs`:
- `page`, `page_size` — pagination
- `status` — active / closing_soon / closed
- `organization`, `department`, `district`, `qualification` — slug filters
- `sort_by` — published_at / last_date / vacancy_count
- `sort_order` — asc / desc

---

## Running Tests

```bash
pip install aiosqlite  # for in-memory SQLite test DB
pytest
```

---

## Adding a New Crawler

1. Create `app/modules/crawlers/<name>.py`
2. Subclass `BaseCrawler`, implement `fetch()` and `parse()`
3. Register in `app/modules/crawlers/scheduler.py` CRAWLERS list
4. Add the source to `app/modules/crawlers/sources/maharashtra.json` (or `central.json`)
5. Done — no other changes needed

### Live smoke test (fetch+parse, no DB)

```bash
python scripts/smoke_crawlers.py
```

MPSC requires Playwright Chromium once:

```bash
pip install playwright
playwright install chromium
```

---

## Background Crawler Worker (recommended)

Crawlers run as a **separate background process**, not inside the API
(so API restarts don't interrupt crawls, and you don't get double runs).

```bash
# Foreground (see logs)
python scripts/crawler_worker.py

# One-shot batch then exit
python scripts/crawler_worker.py --once

# Windows — start hidden in background
.\scripts\start_crawler_worker.ps1
```

Schedule (default):
- First run ~5 seconds after worker start (`CRAWLER_RUN_ON_STARTUP=true`)
- Then every `CRAWLER_INTERVAL_HOURS` (default 6)

Config in `.env`:

```env
CRAWLER_INTERVAL_HOURS=6
CRAWLER_RUN_ON_STARTUP=true
ENABLE_API_SCHEDULER=false
```

Set `ENABLE_API_SCHEDULER=true` only if you want crawlers inside `uvicorn`
instead of the dedicated worker (not both).

---

## Project Structure

```
backend/
├── app/
│   ├── core/          # config, logging
│   ├── database/      # SQLAlchemy base, session
│   ├── shared/        # pagination, exceptions, cache
│   ├── modules/
│   │   ├── jobs/      # model, schema, repo, service
│   │   ├── organizations/
│   │   ├── departments/
│   │   ├── districts/
│   │   ├── qualifications/
│   │   └── crawlers/  # base, mpsc, scheduler
│   ├── api/v1/        # all routers
│   └── main.py
├── alembic/           # migrations
├── tests/
├── docker/
├── Dockerfile
└── docker-compose.yml
```

---

## Coding Standards

- Type hints everywhere
- Black for formatting: `black app/ tests/`
- Ruff for linting: `ruff check app/ tests/`
- No hardcoded secrets — `.env` only

---

*Built for a single developer, low cost, boring and reliable.*
