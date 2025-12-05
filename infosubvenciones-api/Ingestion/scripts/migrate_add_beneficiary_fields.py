"""
Migration: Add beneficiary fields to pdf_extractions table.

Adds:
- beneficiario_nombre (VARCHAR 500) - Specific beneficiary name
- beneficiario_cif (VARCHAR 20) - Tax ID (CIF/NIF)
- proyecto_nombre (VARCHAR 500) - Specific project/activity name
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from config.database import get_db

def migrate():
    """Add beneficiary fields to pdf_extractions table."""
    db = next(get_db())

    try:
        print("📊 Adding beneficiary fields to pdf_extractions table...")

        # Add columns
        migrations = [
            """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS beneficiario_nombre VARCHAR(500);
            """,
            """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS beneficiario_cif VARCHAR(20);
            """,
            """
            ALTER TABLE pdf_extractions
            ADD COLUMN IF NOT EXISTS proyecto_nombre VARCHAR(500);
            """,
        ]

        for i, migration_sql in enumerate(migrations, 1):
            print(f"\n   Running migration {i}/{len(migrations)}...")
            db.execute(text(migration_sql))
            db.commit()
            print(f"   ✅ Migration {i} complete")

        # Verify columns exist
        print("\n📋 Verifying columns...")
        result = db.execute(text("""
            SELECT column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name = 'pdf_extractions'
            AND column_name IN ('beneficiario_nombre', 'beneficiario_cif', 'proyecto_nombre')
            ORDER BY column_name;
        """))

        columns = result.fetchall()
        print("\n   Columns added:")
        for col in columns:
            max_len = col[2] if col[2] else 'N/A'
            print(f"   - {col[0]}: {col[1]} ({max_len})")

        print("\n✅ Migration complete!")
        print("\nℹ️  Next steps:")
        print("   1. Reprocess existing grants to populate these fields")
        print("   2. New grants will automatically extract beneficiary info")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
