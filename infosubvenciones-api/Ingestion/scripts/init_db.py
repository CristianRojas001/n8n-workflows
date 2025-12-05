"""Database initialization script - creates all tables and indexes."""
import os
import sys
from pathlib import Path

# Add parent directory to path to import from config/models
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import text, inspect
from config.database import engine, Base, DATABASE_URL
from models import StagingItem, Convocatoria, PDFExtraction, Embedding


def check_prerequisites():
    """Check database prerequisites before creating schema."""
    print("🔍 Checking prerequisites...")

    try:
        with engine.connect() as conn:
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL version: {version[:80]}...")

            # Check pgvector extension
            result = conn.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
            """))
            has_pgvector = result.fetchone()[0]

            if not has_pgvector:
                print("❌ pgvector extension not enabled!")
                print("   Run this command in Supabase SQL Editor:")
                print("   CREATE EXTENSION IF NOT EXISTS vector;")
                return False

            print("✅ pgvector extension enabled")

            # Check disk space (if applicable)
            result = conn.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database()));
            """))
            db_size = result.fetchone()[0]
            print(f"✅ Current database size: {db_size}")

        return True

    except Exception as e:
        print(f"❌ Prerequisites check failed: {e}")
        return False


def create_tables():
    """Create all database tables."""
    print("\n📦 Creating database tables...")

    try:
        # Create all tables defined in Base metadata
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully")

        # List created tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\n📋 Created tables ({len(tables)}):")
        for table in tables:
            print(f"   - {table}")

        return True

    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def create_indexes():
    """Create additional indexes for performance."""
    print("\n🔧 Creating indexes...")

    indexes = [
        # HNSW index for vector similarity search
        """
        CREATE INDEX IF NOT EXISTS idx_embeddings_vector
        ON embeddings USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
        """,

        # Composite index for filtered search
        """
        CREATE INDEX IF NOT EXISTS idx_conv_sector_region
        ON convocatorias USING GIN (sectores, regiones)
        WHERE sectores IS NOT NULL OR regiones IS NOT NULL;
        """,

        # Index for date-based queries
        """
        CREATE INDEX IF NOT EXISTS idx_conv_dates
        ON convocatorias (fecha_fin_solicitud, abierto)
        WHERE fecha_fin_solicitud IS NOT NULL;
        """,

        # Index for staging items by batch
        """
        CREATE INDEX IF NOT EXISTS idx_staging_batch_status
        ON staging_items (batch_id, status)
        WHERE batch_id IS NOT NULL;
        """,
    ]

    try:
        with engine.connect() as conn:
            for idx, sql in enumerate(indexes, 1):
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"✅ Index {idx}/{len(indexes)} created")
                except Exception as e:
                    print(f"⚠️  Index {idx} failed (may already exist): {e}")

        print("✅ Index creation completed")
        return True

    except Exception as e:
        print(f"❌ Failed to create indexes: {e}")
        return False


def verify_schema():
    """Verify that all tables were created correctly."""
    print("\n🔎 Verifying schema...")

    expected_tables = ['staging_items', 'convocatorias', 'pdf_extractions', 'embeddings']

    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        all_exist = True
        for table in expected_tables:
            if table in tables:
                columns = inspector.get_columns(table)
                print(f"✅ {table}: {len(columns)} columns")
            else:
                print(f"❌ {table}: NOT FOUND")
                all_exist = False

        if all_exist:
            print("\n✅ All tables verified successfully")
        else:
            print("\n❌ Some tables are missing")

        return all_exist

    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False


def show_connection_info():
    """Display connection information."""
    print("\n📊 Database Connection Info:")
    print(f"   URL: {DATABASE_URL[:60]}...")

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user;"))
            db, user = result.fetchone()
            print(f"   Database: {db}")
            print(f"   User: {user}")
    except Exception as e:
        print(f"   Could not retrieve connection info: {e}")


def main():
    """Main initialization function."""
    print("=" * 60)
    print("InfoSubvenciones Database Initialization")
    print("=" * 60)

    show_connection_info()

    # Step 1: Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Fix issues and try again.")
        sys.exit(1)

    # Step 2: Create tables
    if not create_tables():
        print("\n❌ Failed to create tables")
        sys.exit(1)

    # Step 3: Create indexes
    if not create_indexes():
        print("\n⚠️  Some indexes failed, but continuing...")

    # Step 4: Verify schema
    if not verify_schema():
        print("\n❌ Schema verification failed")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ Database initialization completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Test API client (scripts/test_api.py)")
    print("  2. Run test ingestion (scripts/test_pipeline.py)")
    print("  3. Start full ingestion (scripts/run_ingestion.py)")


if __name__ == "__main__":
    main()
