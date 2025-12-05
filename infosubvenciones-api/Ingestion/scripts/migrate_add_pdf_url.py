"""Migration script to add pdf_url and pdf_hash columns to staging_items table."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from loguru import logger

from config.database import engine


def migrate():
    """Add pdf_url and pdf_hash columns to staging_items table."""
    logger.info("Starting migration: Add pdf_url and pdf_hash to staging_items")

    with engine.connect() as conn:
        try:
            # Check if columns already exist
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'staging_items'
                AND column_name IN ('pdf_url', 'pdf_hash')
            """))

            existing_columns = [row[0] for row in result]

            if 'pdf_url' in existing_columns and 'pdf_hash' in existing_columns:
                logger.info("Columns already exist, skipping migration")
                return

            # Add pdf_url column
            if 'pdf_url' not in existing_columns:
                logger.info("Adding pdf_url column...")
                conn.execute(text("""
                    ALTER TABLE staging_items
                    ADD COLUMN IF NOT EXISTS pdf_url TEXT
                """))
                conn.commit()
                logger.success("Added pdf_url column")

            # Add pdf_hash column with index
            if 'pdf_hash' not in existing_columns:
                logger.info("Adding pdf_hash column...")
                conn.execute(text("""
                    ALTER TABLE staging_items
                    ADD COLUMN IF NOT EXISTS pdf_hash VARCHAR(64)
                """))
                conn.commit()
                logger.success("Added pdf_hash column")

                logger.info("Creating index on pdf_hash...")
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_staging_items_pdf_hash
                    ON staging_items(pdf_hash)
                """))
                conn.commit()
                logger.success("Created index on pdf_hash")

            logger.success("Migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    migrate()