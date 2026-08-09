"""Apply create_schema.sql to local PostgreSQL using credentials from .env."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
import os

load_dotenv(ROOT / ".env")


def parse_url(url: str) -> dict:
    # postgresql+asyncpg://user:pass@host:port/db
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

    url = os.getenv("DATABASE_URL", "")
    cfg = parse_url(url)
    sql_path = Path(__file__).resolve().parent / "create_schema.sql"
    sql = sql_path.read_text(encoding="utf-8")

    print(f"Connecting to {cfg['host']}:{cfg['port']}/{cfg['dbname']} as {cfg['user']} ...")
    conn = psycopg2.connect(**cfg)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            tables = [r[0] for r in cur.fetchall()]
        print("Schema applied successfully.")
        print("Tables:", ", ".join(tables))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
