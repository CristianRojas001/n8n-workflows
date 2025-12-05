import os

try:
    import psycopg
except ImportError as e:
    raise SystemExit("psycopg not installed. Run: pip install 'psycopg[binary]'") from e

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("DATABASE_URL not set. Put it in .env or set it in your shell first.")

with psycopg.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        cur.execute("select version();")
        print("Connected ?")
        print(cur.fetchone()[0])

        cur.execute(
            """
            select tablename
            from pg_tables
            where schemaname='public'
            order by tablename;
            """
        )
        print("Tables:", [r[0] for r in cur.fetchall()])
