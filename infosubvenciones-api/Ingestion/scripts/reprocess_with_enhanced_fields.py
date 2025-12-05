"""
Reprocess existing PDF extractions with enhanced field extraction.

This script reprocesses PDFs that were already extracted but are missing
the new fields identified in the enhancement.

Features:
- Reprocesses only PDFs that need updating
- Batch processing with configurable size
- Progress tracking
- Can filter by specific convocatorias or process all

Usage:
    # Dry run (test mode)
    python scripts/reprocess_with_enhanced_fields.py --limit 10

    # Process specific convocatoria
    python scripts/reprocess_with_enhanced_fields.py --numero 870434 --save

    # Process all missing extractions (use with caution!)
    python scripts/reprocess_with_enhanced_fields.py --all --save

Author: Claude
Date: 2025-12-03
"""

import sys
from pathlib import Path

# Add Ingestion to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from sqlalchemy import select, func, or_
from loguru import logger
from typing import List, Optional

from config.database import get_db, engine
from models.pdf_extraction import PDFExtraction
from services.gemini_client import GeminiClient
from services.field_normalizer import FieldNormalizer


def find_extractions_needing_update(limit: Optional[int] = None, numero: Optional[str] = None) -> List[PDFExtraction]:
    """
    Find PDF extractions that need reprocessing with new fields.

    Args:
        limit: Maximum number to return
        numero: Specific convocatoria number (optional)

    Returns:
        List of PDFExtraction records
    """
    db = next(get_db())

    try:
        # Build query for extractions missing new fields
        stmt = select(PDFExtraction).where(
            # Has markdown (text available)
            PDFExtraction.markdown_path.isnot(None),
            # Has some extraction done (not failed)
            PDFExtraction.pdf_word_count > 0,
            # Missing at least one of the new fields
            or_(
                PDFExtraction.finalidad_pdf.is_(None),
                PDFExtraction.sectores_inferidos.is_(None),
                PDFExtraction.instrumento_normalizado.is_(None),
                PDFExtraction.region_nuts.is_(None),
                PDFExtraction.firmantes.is_(None)
            )
        )

        # Filter by specific numero if provided
        if numero:
            stmt = stmt.where(PDFExtraction.numero_convocatoria == numero)

        # Apply limit
        if limit:
            stmt = stmt.limit(limit)

        # Order by ID for consistent processing
        stmt = stmt.order_by(PDFExtraction.id)

        extractions = db.execute(stmt).scalars().all()

        logger.info(f"Found {len(extractions)} extractions needing update")
        return extractions

    finally:
        db.close()


def reprocess_extraction(extraction: PDFExtraction, dry_run: bool = True) -> bool:
    """
    Reprocess a single extraction with enhanced fields.

    Args:
        extraction: PDFExtraction record
        dry_run: If True, don't save to database

    Returns:
        True if successful
    """
    numero = extraction.numero_convocatoria

    try:
        # Load markdown
        md_path = Path(extraction.markdown_path)
        if not md_path.exists():
            logger.error(f"Markdown not found for {numero}: {md_path}")
            return False

        with open(md_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Remove metadata header
        if text.startswith('#'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                text = parts[2].strip()

        if len(text) < 50:
            logger.warning(f"Text too short for {numero}")
            return False

        # Process with Gemini
        gemini_client = GeminiClient()
        normalizer = FieldNormalizer()

        logger.info(f"Processing {numero}...")

        summary, fields, confidence = gemini_client.process_pdf_text(text, numero)

        # Apply normalization
        normalized_fields = normalizer.normalize_all_fields(fields)
        fields.update(normalized_fields)

        # Update database if not dry run
        if not dry_run:
            db = next(get_db())
            try:
                # Update all fields
                extraction.extracted_text = text
                extraction.extracted_summary = summary
                extraction.summary_preview = summary[:500] if summary else None
                extraction.extraction_confidence = confidence

                # Basic info
                extraction.titulo = fields.get('titulo')
                extraction.organismo = fields.get('organismo')
                extraction.ambito_geografico = fields.get('ambito_geografico')

                # Beneficiary
                extraction.beneficiario_nombre = fields.get('beneficiario_nombre')
                extraction.beneficiario_cif = fields.get('beneficiario_cif')
                extraction.proyecto_nombre = fields.get('proyecto_nombre')

                # NEW FIELDS
                extraction.finalidad_pdf = fields.get('finalidad_pdf')
                extraction.finalidad_descripcion_pdf = fields.get('finalidad_descripcion_pdf')
                extraction.tipos_beneficiario_raw = fields.get('tipos_beneficiario_raw')
                extraction.tipos_beneficiario_normalized = fields.get('tipos_beneficiario_normalized')
                extraction.sectores_raw = fields.get('sectores_raw')
                extraction.sectores_inferidos = fields.get('sectores_inferidos')
                extraction.instrumentos_raw = fields.get('instrumentos_raw')
                extraction.instrumento_normalizado = fields.get('instrumento_normalizado')
                extraction.procedimiento = fields.get('procedimiento')
                extraction.region_mencionada = fields.get('region_mencionada')
                extraction.region_nuts = fields.get('region_nuts')
                extraction.firmantes = fields.get('firmantes')
                extraction.csv_codigo = fields.get('csv_codigo')
                extraction.url_verificacion = fields.get('url_verificacion')
                extraction.memoria_obligatoria = fields.get('memoria_obligatoria')
                extraction.es_compatible_otras_ayudas = fields.get('es_compatible_otras_ayudas')

                # Financial (update all for consistency)
                extraction.gastos_subvencionables = fields.get('gastos_subvencionables')
                extraction.cuantia_subvencion = fields.get('cuantia_subvencion')
                extraction.cuantia_min = fields.get('cuantia_min')
                extraction.cuantia_max = fields.get('cuantia_max')
                extraction.intensidad_ayuda = fields.get('intensidad_ayuda')
                extraction.compatibilidad_otras_ayudas = fields.get('compatibilidad_otras_ayudas')

                # Deadlines
                extraction.plazo_ejecucion = fields.get('plazo_ejecucion')
                extraction.plazo_justificacion = fields.get('plazo_justificacion')
                extraction.fecha_inicio_ejecucion = fields.get('fecha_inicio_ejecucion')
                extraction.fecha_fin_ejecucion = fields.get('fecha_fin_ejecucion')
                extraction.plazo_resolucion = fields.get('plazo_resolucion')

                # Justification
                extraction.forma_justificacion = fields.get('forma_justificacion')
                extraction.documentacion_requerida = fields.get('documentacion_requerida')
                extraction.sistema_evaluacion = fields.get('sistema_evaluacion')

                # Payment
                extraction.forma_pago = fields.get('forma_pago')
                extraction.pago_anticipado = fields.get('pago_anticipado')
                extraction.garantias = fields.get('garantias')
                extraction.exige_aval = fields.get('exige_aval')

                # Obligations
                extraction.obligaciones_beneficiario = fields.get('obligaciones_beneficiario')
                extraction.publicidad_requerida = fields.get('publicidad_requerida')
                extraction.subcontratacion = fields.get('subcontratacion')
                extraction.modificaciones_permitidas = fields.get('modificaciones_permitidas')

                # Requirements
                extraction.requisitos_tecnicos = fields.get('requisitos_tecnicos')
                extraction.criterios_valoracion = fields.get('criterios_valoracion')
                extraction.documentos_fase_solicitud = fields.get('documentos_fase_solicitud')

                db.commit()
                logger.success(f"✓ Updated {numero}")

            except Exception as e:
                logger.error(f"Database update failed for {numero}: {e}")
                db.rollback()
                return False
            finally:
                db.close()
        else:
            logger.info(f"[DRY RUN] Would update {numero}")

        return True

    except Exception as e:
        logger.error(f"Reprocessing failed for {numero}: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Reprocess PDF extractions with enhanced fields'
    )
    parser.add_argument(
        '--numero',
        type=str,
        help='Specific convocatoria number to reprocess'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum number of extractions to process (default: 10)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Process all extractions needing update (ignores --limit)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save to database (default is dry run)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("Enhanced Field Reprocessing Script")
    logger.info("=" * 80)

    if not args.save:
        logger.warning("⚠️  DRY RUN MODE - Database will NOT be updated")
        logger.info("Add --save flag to save results")
        logger.info("=" * 80)

    # Find extractions to process
    limit = None if args.all else args.limit

    extractions = find_extractions_needing_update(
        limit=limit,
        numero=args.numero
    )

    if not extractions:
        logger.info("No extractions need updating!")
        return

    logger.info(f"\nProcessing {len(extractions)} extractions...")
    logger.info("-" * 80)

    # Process each extraction
    success_count = 0
    fail_count = 0

    for i, extraction in enumerate(extractions, 1):
        logger.info(f"\n[{i}/{len(extractions)}] {extraction.numero_convocatoria}")

        success = reprocess_extraction(extraction, dry_run=not args.save)

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("REPROCESSING SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  Total: {len(extractions)}")
    logger.info(f"  ✓ Success: {success_count}")
    logger.info(f"  ✗ Failed: {fail_count}")

    if not args.save:
        logger.info("\n⚠️  DRY RUN MODE - No changes saved")
        logger.info("Run with --save to update database")
    else:
        logger.success("\n✓ Database updated!")


if __name__ == "__main__":
    main()
