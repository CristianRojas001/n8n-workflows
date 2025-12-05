#!/usr/bin/env python
"""
One-off helper script to align the Postgres schema with the new embedding/vector
code introduced on Day 11-12.

It performs the following steps (idempotently):
1. Adds missing FK columns/constraints to staging_items and pdf_extractions.
2. Adds the new extracted_text/summary columns required by the embedder.
3. Rebuilds the embeddings table with the new layout (extraction_id + pgvector).

Run it once from the repo root:
    python scripts/update_embedding_schema.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent

from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parents[1]
INGESTION_DIR = REPO_ROOT / "Ingestion"
if str(INGESTION_DIR) not in sys.path:
    sys.path.insert(0, str(INGESTION_DIR))

from config.database import engine  # type: ignore  # pylint: disable=import-error


def column_exists(conn, table: str, column: str) -> bool:
    query = text(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = :table
          AND column_name = :column
        """
    )
    return conn.execute(query, {"table": table, "column": column}).first() is not None


def ensure_column(conn, table: str, column: str, definition: str) -> None:
    if not column_exists(conn, table, column):
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        print(f"[schema] Added column {table}.{column} ({definition})")


def ensure_constraint(conn, name: str, ddl: str) -> None:
    query = text(
        """
        SELECT 1
        FROM pg_constraint
        WHERE conname = :name
    """
    )
    if conn.execute(query, {"name": name}).first():
        return
    conn.execute(text(ddl))
    print(f"[schema] Added constraint {name}")


def rebuild_embeddings_table(conn) -> None:
    has_extraction_id = column_exists(conn, "embeddings", "extraction_id")
    if has_extraction_id:
        print("[schema] embeddings table already matches expected structure")
        return

    row_count = conn.execute(text("SELECT COUNT(*) FROM embeddings")).scalar() or 0
    if row_count > 0:
        raise RuntimeError(
            "Cannot rebuild embeddings table automatically because it contains "
            f"{row_count} rows. Please migrate the data manually and rerun."
        )

    conn.execute(text("DROP TABLE IF EXISTS embeddings CASCADE"))
    conn.execute(
        text(
            dedent(
                """
                CREATE TABLE embeddings (
                    id SERIAL PRIMARY KEY,
                    extraction_id INTEGER NOT NULL UNIQUE
                        REFERENCES pdf_extractions(id) ON DELETE CASCADE,
                    embedding_vector VECTOR(768) NOT NULL,
                    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-004',
                    embedding_dimensions INTEGER NOT NULL DEFAULT 768,
                    text_length INTEGER,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
    )
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS embeddings_hnsw_idx "
            "ON embeddings USING hnsw (embedding_vector vector_cosine_ops)"
        )
    )
    print("[schema] Recreated embeddings table with extraction_id + pgvector column")


def backfill_staging_ids(conn) -> None:
    conn.execute(
        text(
            dedent(
                """
                UPDATE pdf_extractions p
                SET staging_id = s.id
                FROM staging_items s
                WHERE p.staging_id IS NULL
                  AND s.numero_convocatoria = p.numero_convocatoria
                """
            )
        )
    )


def main() -> None:
    with engine.begin() as conn:
        # staging_items: ensure convocatoria_id FK exists
        ensure_column(conn, "staging_items", "convocatoria_id", "INTEGER")
        ensure_constraint(
            conn,
            "staging_items_convocatoria_id_fkey",
            """
            ALTER TABLE staging_items
            ADD CONSTRAINT staging_items_convocatoria_id_fkey
            FOREIGN KEY (convocatoria_id)
            REFERENCES convocatorias(id)
            ON DELETE SET NULL
            """,
        )

        # pdf_extractions: new linkage + text fields
        ensure_column(conn, "pdf_extractions", "staging_id", "INTEGER")
        ensure_column(conn, "pdf_extractions", "extracted_text", "TEXT")
        ensure_column(conn, "pdf_extractions", "extracted_summary", "TEXT")
        ensure_column(conn, "pdf_extractions", "summary_preview", "VARCHAR(500)")
        ensure_column(conn, "pdf_extractions", "titulo", "VARCHAR(500)")
        ensure_column(conn, "pdf_extractions", "organismo", "VARCHAR(300)")
        ensure_column(conn, "pdf_extractions", "ambito_geografico", "VARCHAR(200)")

        ensure_constraint(
            conn,
            "pdf_extractions_staging_id_key",
            """
            ALTER TABLE pdf_extractions
            ADD CONSTRAINT pdf_extractions_staging_id_key
            UNIQUE (staging_id)
            """,
        )
        ensure_constraint(
            conn,
            "pdf_extractions_staging_id_fkey",
            """
            ALTER TABLE pdf_extractions
            ADD CONSTRAINT pdf_extractions_staging_id_fkey
            FOREIGN KEY (staging_id)
            REFERENCES staging_items(id)
            ON DELETE CASCADE
            """,
        )

        backfill_staging_ids(conn)
        rebuild_embeddings_table(conn)

    print("Schema update complete.")


if __name__ == "__main__":
    main()
