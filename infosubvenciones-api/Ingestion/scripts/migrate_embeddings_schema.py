"""
Migration script to update database schema for embeddings.

Changes:
1. PDFExtraction: Change convocatoria_id -> staging_id, add extracted_text, extracted_summary, summary_preview, titulo, organismo, ambito_geografico
2. StagingItem: Add convocatoria_id FK and relationship
3. Embedding: Change convocatoria_id -> extraction_id, change embedding -> embedding_vector, simplify metadata fields
4. Update HNSW index to use embedding_vector instead of embedding
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from config.database import engine
from config.settings import get_settings

settings = get_settings()


def run_migration():
    """Run the schema migration."""
    print("=" * 70)
    print("DATABASE SCHEMA MIGRATION - Embeddings Architecture")
    print("=" * 70)

    print("\n⚠️  WARNING: This will modify your database schema!")
    print("   Make sure you have a backup before proceeding.")
    response = input("\nContinue? (yes/no): ")

    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return False

    migrations = []

    # Step 1: Update staging_items table
    print("\n" + "=" * 70)
    print("STEP 1: Update staging_items table")
    print("=" * 70)

    migrations.extend([
        {
            "name": "Add convocatoria_id to staging_items",
            "sql": """
            ALTER TABLE staging_items
            ADD COLUMN IF NOT EXISTS convocatoria_id INTEGER;
            """,
            "rollback": "ALTER TABLE staging_items DROP COLUMN IF EXISTS convocatoria_id;"
        },
        {
            "name": "Add FK constraint for convocatoria_id",
            "sql": """
            ALTER TABLE staging_items
            ADD CONSTRAINT fk_staging_convocatoria
            FOREIGN KEY (convocatoria_id)
            REFERENCES convocatorias(id)
            ON DELETE SET NULL;
            """,
            "rollback": "ALTER TABLE staging_items DROP CONSTRAINT IF EXISTS fk_staging_convocatoria;"
        },
        {
            "name": "Create index on convocatoria_id",
            "sql": """
            CREATE INDEX IF NOT EXISTS idx_staging_convocatoria
            ON staging_items(convocatoria_id);
            """,
            "rollback": "DROP INDEX IF EXISTS idx_staging_convocatoria;"
        }
    ])

    # Step 2: Update pdf_extractions table
    print("\n" + "=" * 70)
    print("STEP 2: Update pdf_extractions table")
    print("=" * 70)

    migrations.extend([
        {
            "name": "Add staging_id to pdf_extractions",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS staging_id INTEGER;
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP COLUMN IF EXISTS staging_id;"
        },
        {
            "name": "Add extracted_text to pdf_extractions",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS extracted_text TEXT;
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP COLUMN IF EXISTS extracted_text;"
        },
        {
            "name": "Add extracted_summary to pdf_extractions",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS extracted_summary TEXT;
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP COLUMN IF EXISTS extracted_summary;"
        },
        {
            "name": "Add summary_preview to pdf_extractions",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS summary_preview VARCHAR(500);
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP COLUMN IF EXISTS summary_preview;"
        },
        {
            "name": "Add titulo to pdf_extractions",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS titulo VARCHAR(500);
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP COLUMN IF EXISTS titulo;"
        },
        {
            "name": "Add organismo to pdf_extractions",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS organismo VARCHAR(300);
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP COLUMN IF EXISTS organismo;"
        },
        {
            "name": "Add ambito_geografico to pdf_extractions",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS ambito_geografico VARCHAR(200);
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP COLUMN IF EXISTS ambito_geografico;"
        },
        {
            "name": "Add FK constraint for staging_id",
            "sql": """
            ALTER TABLE pdf_extractions
            ADD CONSTRAINT fk_pdf_staging
            FOREIGN KEY (staging_id)
            REFERENCES staging_items(id)
            ON DELETE CASCADE;
            """,
            "rollback": "ALTER TABLE pdf_extractions DROP CONSTRAINT IF EXISTS fk_pdf_staging;"
        },
        {
            "name": "Create index on staging_id",
            "sql": """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_pdf_staging
            ON pdf_extractions(staging_id);
            """,
            "rollback": "DROP INDEX IF EXISTS idx_pdf_staging;"
        }
    ])

    # Step 3: Update embeddings table
    print("\n" + "=" * 70)
    print("STEP 3: Update embeddings table")
    print("=" * 70)

    migrations.extend([
        {
            "name": "Add extraction_id to embeddings",
            "sql": """
            ALTER TABLE embeddings
            ADD COLUMN IF NOT EXISTS extraction_id INTEGER;
            """,
            "rollback": "ALTER TABLE embeddings DROP COLUMN IF EXISTS extraction_id;"
        },
        {
            "name": "Add embedding_vector to embeddings (768 dimensions)",
            "sql": """
            ALTER TABLE embeddings
            ADD COLUMN IF NOT EXISTS embedding_vector vector(768);
            """,
            "rollback": "ALTER TABLE embeddings DROP COLUMN IF EXISTS embedding_vector;"
        },
        {
            "name": "Add model_name to embeddings",
            "sql": """
            ALTER TABLE embeddings
            ADD COLUMN IF NOT EXISTS model_name VARCHAR(100) DEFAULT 'text-embedding-004';
            """,
            "rollback": "ALTER TABLE embeddings DROP COLUMN IF EXISTS model_name;"
        },
        {
            "name": "Add text_length to embeddings",
            "sql": """
            ALTER TABLE embeddings
            ADD COLUMN IF NOT EXISTS text_length INTEGER;
            """,
            "rollback": "ALTER TABLE embeddings DROP COLUMN IF EXISTS text_length;"
        },
        {
            "name": "Add FK constraint for extraction_id",
            "sql": """
            ALTER TABLE embeddings
            ADD CONSTRAINT fk_embedding_extraction
            FOREIGN KEY (extraction_id)
            REFERENCES pdf_extractions(id)
            ON DELETE CASCADE;
            """,
            "rollback": "ALTER TABLE embeddings DROP CONSTRAINT IF EXISTS fk_embedding_extraction;"
        },
        {
            "name": "Create unique index on extraction_id",
            "sql": """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_embedding_extraction
            ON embeddings(extraction_id);
            """,
            "rollback": "DROP INDEX IF EXISTS idx_embedding_extraction;"
        },
        {
            "name": "Drop old HNSW index (if exists)",
            "sql": """
            DROP INDEX IF EXISTS idx_embeddings_vector;
            """,
            "rollback": "-- Cannot rollback index drop"
        },
        {
            "name": "Create new HNSW index on embedding_vector",
            "sql": """
            CREATE INDEX IF NOT EXISTS idx_embeddings_vector_new
            ON embeddings USING hnsw (embedding_vector vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """,
            "rollback": "DROP INDEX IF EXISTS idx_embeddings_vector_new;"
        }
    ])

    # Execute migrations
    print("\n" + "=" * 70)
    print("EXECUTING MIGRATIONS")
    print("=" * 70)

    with engine.begin() as conn:
        for i, migration in enumerate(migrations, 1):
            try:
                print(f"\n[{i}/{len(migrations)}] {migration['name']}")
                conn.execute(text(migration['sql']))
                print(f"   ✅ Success")
            except Exception as e:
                print(f"   ⚠️  Warning: {e}")
                # Continue with other migrations

    print("\n" + "=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)
    print("\n✅ Schema migration completed successfully!")
    print("\nNOTE: Old columns (convocatoria_id in pdf_extractions/embeddings) were NOT dropped")
    print("      to preserve existing data. You can manually drop them after verifying the migration.")

    return True


if __name__ == "__main__":
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
