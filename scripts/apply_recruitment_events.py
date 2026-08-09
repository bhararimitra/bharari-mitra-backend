"""Apply add_recruitment_events.sql using DATABASE_URL from .env."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def parse_url(url: str) -> dict:
    m = re.match(
        r"postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(.+)",
        url,
    )
    if not m:
        raise SystemExit(f"Cannot parse DATABASE_URL: {url}")
    return {
        "user": m.group(1),
        "password": m.group(2),
        "host": m.group(3),
        "port": int(m.group(4) or 5432),
        "dbname": m.group(5).split("?")[0],
    }


def main() -> None:
    import psycopg2

    cfg = parse_url(os.getenv("DATABASE_URL", ""))
    sql = (Path(__file__).resolve().parent / "add_recruitment_events.sql").read_text(
        encoding="utf-8"
    )
    print(f"Applying recruitment_events on {cfg['host']}/{cfg['dbname']} ...")
    conn = psycopg2.connect(**cfg)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "SELECT to_regclass('public.recruitment_events'), version_num FROM alembic_version"
            )
            print("result:", cur.fetchone())
    finally:
        conn.close()
    print("Done. Next: python scripts/backfill_recruitment_links.py")


if __name__ == "__main__":
    main()
