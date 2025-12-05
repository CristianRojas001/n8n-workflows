"""
Migration script to add missing PDF extraction fields.

This script adds new fields identified in:
docs/Missing Fields vs What CAN Be Extracted From the PDF.md

New fields include:
- Purpose/finalidad (from PDF)
- Beneficiary types (raw + normalized)
- Sectors (raw + inferred)
- Instruments (raw + normalized)
- Procedure
- Region (mentioned + NUTS code)
- Signatories (firmantes)
- CSV verification code and URL
- Required reports checklist
- Compatibility boolean flag

Author: Claude
Date: 2025-12-03
"""

import sys
from pathlib import Path

# Add Ingestion to path
sys.path.insert(0, str(Path(__file__).parent.parent / "Ingestion"))

from sqlalchemy import text
from loguru import logger
from config.database import engine

def run_migration():
    """Add new fields to pdf_extractions table."""

    logger.info("Starting migration: add missing PDF extraction fields")

    migration_sql = """
    -- Purpose/Finalidad from PDF
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS finalidad_pdf TEXT,
    ADD COLUMN IF NOT EXISTS finalidad_descripcion_pdf TEXT;

    -- Beneficiary types (raw + normalized)
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS tipos_beneficiario_raw TEXT,
    ADD COLUMN IF NOT EXISTS tipos_beneficiario_normalized TEXT[];

    -- Sectors (raw + inferred)
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS sectores_raw TEXT,
    ADD COLUMN IF NOT EXISTS sectores_inferidos TEXT[];

    -- Instruments (raw + normalized)
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS instrumentos_raw TEXT,
    ADD COLUMN IF NOT EXISTS instrumento_normalizado VARCHAR(200);

    -- Procedure
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS procedimiento VARCHAR(200);

    -- Region (mentioned + NUTS)
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS region_mencionada TEXT,
    ADD COLUMN IF NOT EXISTS region_nuts VARCHAR(20);

    -- Signatories
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS firmantes JSONB;

    -- CSV verification
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS csv_codigo VARCHAR(200),
    ADD COLUMN IF NOT EXISTS url_verificacion TEXT;

    -- Required reports checklist
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS memoria_obligatoria JSONB;

    -- Compatibility boolean (derived from compatibilidad_otras_ayudas)
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS es_compatible_otras_ayudas BOOLEAN;

    -- Add indexes for commonly queried fields
    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_instrumento
    ON pdf_extractions(instrumento_normalizado);

    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_procedimiento
    ON pdf_extractions(procedimiento);

    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_region_nuts
    ON pdf_extractions(region_nuts);

    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_sectores
    ON pdf_extractions USING GIN(sectores_inferidos);

    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_tipos_beneficiario
    ON pdf_extractions USING GIN(tipos_beneficiario_normalized);
    """

    try:
        with engine.connect() as conn:
            # Execute migration
            conn.execute(text(migration_sql))
            conn.commit()

        logger.success("Migration completed successfully!")
        logger.info("Added fields:")
        logger.info("  - finalidad_pdf, finalidad_descripcion_pdf")
        logger.info("  - tipos_beneficiario_raw, tipos_beneficiario_normalized")
        logger.info("  - sectores_raw, sectores_inferidos")
        logger.info("  - instrumentos_raw, instrumento_normalizado")
        logger.info("  - procedimiento")
        logger.info("  - region_mencionada, region_nuts")
        logger.info("  - firmantes (JSONB)")
        logger.info("  - csv_codigo, url_verificacion")
        logger.info("  - memoria_obligatoria (JSONB)")
        logger.info("  - es_compatible_otras_ayudas (BOOLEAN)")
        logger.info("  - 5 new indexes created")

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def verify_migration():
    """Verify that new columns exist."""

    logger.info("Verifying migration...")

    verify_sql = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'pdf_extractions'
    AND column_name IN (
        'finalidad_pdf',
        'finalidad_descripcion_pdf',
        'tipos_beneficiario_raw',
        'tipos_beneficiario_normalized',
        'sectores_raw',
        'sectores_inferidos',
        'instrumentos_raw',
        'instrumento_normalizado',
        'procedimiento',
        'region_mencionada',
        'region_nuts',
        'firmantes',
        'csv_codigo',
        'url_verificacion',
        'memoria_obligatoria',
        'es_compatible_otras_ayudas'
    )
    ORDER BY column_name;
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(text(verify_sql))
            columns = result.fetchall()

        logger.info(f"Found {len(columns)} new columns:")
        for col_name, data_type in columns:
            logger.info(f"  ✓ {col_name}: {data_type}")

        if len(columns) == 16:
            logger.success("All new columns verified!")
            return True
        else:
            logger.warning(f"Expected 16 columns, found {len(columns)}")
            return False

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PDF Extractions Schema Migration")
    logger.info("=" * 60)

    # Run migration
    success = run_migration()

    if success:
        # Verify
        verify_migration()
        logger.success("✓ Migration completed and verified!")
    else:
        logger.error("✗ Migration failed")
        sys.exit(1)
