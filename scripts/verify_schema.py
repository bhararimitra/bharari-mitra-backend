"""Print local schema columns for verification."""

import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="bharari123",
    dbname="bhararimitra",
)
cur = conn.cursor()
cur.execute(
    """
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name IN (
        'jobs', 'organizations', 'departments',
        'districts', 'qualifications', 'crawler_history'
      )
    ORDER BY table_name, ordinal_position
    """
)
current = None
for table, column, dtype in cur.fetchall():
    if table != current:
        print(f"\n{table}")
        current = table
    print(f"  - {column}: {dtype}")
conn.close()
