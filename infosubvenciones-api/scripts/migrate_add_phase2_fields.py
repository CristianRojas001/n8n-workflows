"""
Migration script to add Phase 2 PDF extraction fields.

This script adds raw_* fields and additional extraction fields that provide
debugging/verification capabilities and capture information that may be
missing from the API.

Phase 2 fields include:
- All raw_* fields for verification
- importe_total_pdf, importe_maximo_pdf (fallbacks when API is null)
- tipo_administracion_raw, nivel_administracion_raw, ambito_raw (for inference)

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
    """Add Phase 2 fields to pdf_extractions table."""

    logger.info("Starting migration: add Phase 2 PDF extraction fields")

    migration_sql = """
    -- Amounts from PDF (fallbacks when API is null)
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS importe_total_pdf TEXT,
    ADD COLUMN IF NOT EXISTS importe_maximo_pdf DOUBLE PRECISION;

    -- Inference fields (raw text before normalization)
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS tipo_administracion_raw TEXT,
    ADD COLUMN IF NOT EXISTS nivel_administracion_raw TEXT,
    ADD COLUMN IF NOT EXISTS ambito_raw TEXT;

    -- Normalized inference fields
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS tipo_administracion_normalizado VARCHAR(100),
    ADD COLUMN IF NOT EXISTS nivel_administracion_normalizado VARCHAR(100),
    ADD COLUMN IF NOT EXISTS ambito_normalizado VARCHAR(100);

    -- Beneficiary details from PDF
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS beneficiarios_descripcion_pdf TEXT,
    ADD COLUMN IF NOT EXISTS requisitos_beneficiarios_pdf TEXT;

    -- Application/submission details
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS forma_solicitud_pdf TEXT,
    ADD COLUMN IF NOT EXISTS lugar_presentacion_pdf TEXT,
    ADD COLUMN IF NOT EXISTS url_tramite_pdf TEXT;

    -- Normativa from PDF
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS bases_reguladoras_pdf TEXT,
    ADD COLUMN IF NOT EXISTS normativa_pdf JSONB;

    -- === RAW FIELDS (for debugging/verification) ===
    ALTER TABLE pdf_extractions
    ADD COLUMN IF NOT EXISTS raw_objeto TEXT,
    ADD COLUMN IF NOT EXISTS raw_finalidad TEXT,
    ADD COLUMN IF NOT EXISTS raw_ambito TEXT,
    ADD COLUMN IF NOT EXISTS raw_beneficiarios TEXT,
    ADD COLUMN IF NOT EXISTS raw_requisitos_beneficiarios TEXT,
    ADD COLUMN IF NOT EXISTS raw_importe_total TEXT,
    ADD COLUMN IF NOT EXISTS raw_importe_maximo TEXT,
    ADD COLUMN IF NOT EXISTS raw_porcentaje_financiacion TEXT,
    ADD COLUMN IF NOT EXISTS raw_forma_solicitud TEXT,
    ADD COLUMN IF NOT EXISTS raw_lugar_presentacion TEXT,
    ADD COLUMN IF NOT EXISTS raw_bases_reguladoras TEXT,
    ADD COLUMN IF NOT EXISTS raw_normativa TEXT;

    -- Indexes for commonly queried fields
    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_tipo_admin
    ON pdf_extractions(tipo_administracion_normalizado);

    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_nivel_admin
    ON pdf_extractions(nivel_administracion_normalizado);

    CREATE INDEX IF NOT EXISTS idx_pdf_extractions_ambito
    ON pdf_extractions(ambito_normalizado);
    """

    try:
        with engine.connect() as conn:
            # Execute migration
            conn.execute(text(migration_sql))
            conn.commit()

        logger.success("Migration completed successfully!")
        logger.info("Added field categories:")
        logger.info("  - Fallback amount fields (importe_total_pdf, importe_maximo_pdf)")
        logger.info("  - Inference fields (tipo/nivel/ambito: raw + normalized)")
        logger.info("  - Beneficiary details from PDF")
        logger.info("  - Application/submission details from PDF")
        logger.info("  - Normativa from PDF")
        logger.info("  - 12 raw_* fields for debugging")
        logger.info("  - 3 new indexes created")

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
        'importe_total_pdf',
        'importe_maximo_pdf',
        'tipo_administracion_raw',
        'nivel_administracion_raw',
        'ambito_raw',
        'tipo_administracion_normalizado',
        'nivel_administracion_normalizado',
        'ambito_normalizado',
        'beneficiarios_descripcion_pdf',
        'requisitos_beneficiarios_pdf',
        'forma_solicitud_pdf',
        'lugar_presentacion_pdf',
        'url_tramite_pdf',
        'bases_reguladoras_pdf',
        'normativa_pdf',
        'raw_objeto',
        'raw_finalidad',
        'raw_ambito',
        'raw_beneficiarios',
        'raw_requisitos_beneficiarios',
        'raw_importe_total',
        'raw_importe_maximo',
        'raw_porcentaje_financiacion',
        'raw_forma_solicitud',
        'raw_lugar_presentacion',
        'raw_bases_reguladoras',
        'raw_normativa'
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

        expected_count = 27  # Total new fields
        if len(columns) == expected_count:
            logger.success("All new columns verified!")
            return True
        else:
            logger.warning(f"Expected {expected_count} columns, found {len(columns)}")
            return False

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PDF Extractions Schema Migration - Phase 2")
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
