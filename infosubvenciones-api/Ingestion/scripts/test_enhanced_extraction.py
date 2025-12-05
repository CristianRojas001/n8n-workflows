"""
Test script for enhanced PDF extraction with new fields.

Tests the complete extraction pipeline on a specific convocatoria:
1. Reads existing PDF markdown
2. Processes with enhanced LLM extraction
3. Applies field normalization
4. Updates database
5. Displays results for validation

Usage:
    python scripts/test_enhanced_extraction.py 870434

Author: Claude
Date: 2025-12-03
"""

import sys
from pathlib import Path

# Add Ingestion to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from loguru import logger
import json

from config.database import get_db
from models.pdf_extraction import PDFExtraction
from services.gemini_client import GeminiClient
from services.field_normalizer import FieldNormalizer


def test_extraction(numero_convocatoria: str, dry_run: bool = True):
    """
    Test enhanced extraction on a specific convocatoria.

    Args:
        numero_convocatoria: Grant ID to test
        dry_run: If True, don't save to database (default)
    """
    logger.info(f"Testing enhanced extraction for: {numero_convocatoria}")
    logger.info(f"Dry run mode: {dry_run}")
    logger.info("=" * 80)

    db = next(get_db())

    try:
        # 1. Fetch existing extraction
        stmt = select(PDFExtraction).where(
            PDFExtraction.numero_convocatoria == numero_convocatoria
        )
        extraction = db.execute(stmt).scalar_one_or_none()

        if not extraction:
            logger.error(f"Extraction not found for {numero_convocatoria}")
            return False

        # 2. Load markdown
        if not extraction.markdown_path:
            logger.error("No markdown path found")
            return False

        md_path = Path(extraction.markdown_path)
        if not md_path.exists():
            logger.error(f"Markdown file not found: {md_path}")
            return False

        with open(md_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Remove metadata header
        if text.startswith('#'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                text = parts[2].strip()

        logger.info(f"Loaded markdown: {len(text)} chars, {len(text.split())} words")
        logger.info("-" * 80)

        # 3. Process with enhanced LLM
        logger.info("Processing with Gemini (enhanced prompt)...")
        gemini_client = GeminiClient()

        summary, fields, confidence = gemini_client.process_pdf_text(
            text,
            numero_convocatoria
        )

        logger.success(f"LLM processing complete!")
        logger.info(f"  Summary length: {len(summary)} chars")
        logger.info(f"  Fields extracted: {len(fields)}")
        logger.info(f"  Confidence: {confidence:.2%}")
        logger.info("-" * 80)

        # 4. Apply normalization
        logger.info("Applying field normalization...")
        normalizer = FieldNormalizer()

        normalized_fields = normalizer.normalize_all_fields(fields)
        fields.update(normalized_fields)

        logger.success(f"Normalization complete! Added {len(normalized_fields)} normalized fields")
        logger.info("-" * 80)

        # 5. Display results
        logger.info("EXTRACTION RESULTS:")
        logger.info("=" * 80)

        # Summary
        logger.info("\n📄 SUMMARY:")
        logger.info(summary[:500] + "..." if len(summary) > 500 else summary)

        # New fields
        new_fields_display = {
            'Finalidad (PDF)': 'finalidad_pdf',
            'Finalidad Descripción (PDF)': 'finalidad_descripcion_pdf',
            'Tipos Beneficiario (Raw)': 'tipos_beneficiario_raw',
            'Tipos Beneficiario (Normalized)': 'tipos_beneficiario_normalized',
            'Sectores (Raw)': 'sectores_raw',
            'Sectores (Inferidos)': 'sectores_inferidos',
            'Instrumentos (Raw)': 'instrumentos_raw',
            'Instrumento (Normalizado)': 'instrumento_normalizado',
            'Procedimiento': 'procedimiento',
            'Región Mencionada': 'region_mencionada',
            'Región NUTS': 'region_nuts',
            'Firmantes': 'firmantes',
            'CSV Código': 'csv_codigo',
            'URL Verificación': 'url_verificacion',
            'Memoria Obligatoria': 'memoria_obligatoria',
            'Es Compatible Otras Ayudas': 'es_compatible_otras_ayudas'
        }

        logger.info("\n🆕 NEW EXTRACTED FIELDS:")
        for label, field_name in new_fields_display.items():
            value = fields.get(field_name)
            if value is not None:
                if isinstance(value, (list, dict)):
                    logger.info(f"\n  {label}:")
                    logger.info(f"    {json.dumps(value, ensure_ascii=False, indent=4)}")
                elif isinstance(value, str) and len(value) > 100:
                    logger.info(f"\n  {label}:")
                    logger.info(f"    {value[:100]}...")
                else:
                    logger.info(f"  {label}: {value}")

        # Financial fields (for comparison)
        logger.info("\n💰 FINANCIAL DETAILS:")
        logger.info(f"  Cuantía: {fields.get('cuantia_subvencion')}")
        logger.info(f"  Cuantía Min: {fields.get('cuantia_min')}")
        logger.info(f"  Cuantía Max: {fields.get('cuantia_max')}")
        logger.info(f"  Intensidad: {fields.get('intensidad_ayuda')}")
        logger.info(f"  Compatibilidad: {fields.get('compatibilidad_otras_ayudas')}")

        # Beneficiary info
        logger.info("\n👤 BENEFICIARY INFO:")
        logger.info(f"  Nombre: {fields.get('beneficiario_nombre')}")
        logger.info(f"  CIF: {fields.get('beneficiario_cif')}")
        logger.info(f"  Proyecto: {fields.get('proyecto_nombre')}")

        # Deadlines
        logger.info("\n📅 DEADLINES:")
        logger.info(f"  Plazo Ejecución: {fields.get('plazo_ejecucion')}")
        logger.info(f"  Plazo Justificación: {fields.get('plazo_justificacion')}")
        logger.info(f"  Fecha Inicio: {fields.get('fecha_inicio_ejecucion')}")
        logger.info(f"  Fecha Fin: {fields.get('fecha_fin_ejecucion')}")

        logger.info("\n" + "=" * 80)

        # 6. Update database if not dry run
        if not dry_run:
            logger.info("\nUpdating database...")

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

            # Financial
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

            # PHASE 2 FIELDS
            # Scope inference
            extraction.tipo_administracion_raw = fields.get('tipo_administracion_raw')
            extraction.nivel_administracion_raw = fields.get('nivel_administracion_raw')
            extraction.ambito_raw = fields.get('ambito_raw')
            extraction.tipo_administracion_normalizado = fields.get('tipo_administracion_normalizado')
            extraction.nivel_administracion_normalizado = fields.get('nivel_administracion_normalizado')
            extraction.ambito_normalizado = fields.get('ambito_normalizado')

            # Beneficiary details
            extraction.beneficiarios_descripcion_pdf = fields.get('beneficiarios_descripcion_pdf')
            extraction.requisitos_beneficiarios_pdf = fields.get('requisitos_beneficiarios_pdf')

            # Financial fallbacks
            extraction.importe_total_pdf = fields.get('importe_total_pdf')
            extraction.importe_maximo_pdf = fields.get('importe_maximo_pdf')

            # Application/submission
            extraction.forma_solicitud_pdf = fields.get('forma_solicitud_pdf')
            extraction.lugar_presentacion_pdf = fields.get('lugar_presentacion_pdf')
            extraction.url_tramite_pdf = fields.get('url_tramite_pdf')

            # Normativa
            extraction.bases_reguladoras_pdf = fields.get('bases_reguladoras_pdf')
            extraction.normativa_pdf = fields.get('normativa_pdf')

            # RAW FIELDS
            extraction.raw_objeto = fields.get('raw_objeto')
            extraction.raw_finalidad = fields.get('raw_finalidad')
            extraction.raw_ambito = fields.get('raw_ambito')
            extraction.raw_beneficiarios = fields.get('raw_beneficiarios')
            extraction.raw_requisitos_beneficiarios = fields.get('raw_requisitos_beneficiarios')
            extraction.raw_importe_total = fields.get('raw_importe_total')
            extraction.raw_importe_maximo = fields.get('raw_importe_maximo')
            extraction.raw_porcentaje_financiacion = fields.get('raw_porcentaje_financiacion')
            extraction.raw_forma_solicitud = fields.get('raw_forma_solicitud')
            extraction.raw_lugar_presentacion = fields.get('raw_lugar_presentacion')
            extraction.raw_bases_reguladoras = fields.get('raw_bases_reguladoras')
            extraction.raw_normativa = fields.get('raw_normativa')
            extraction.raw_gastos_subvencionables = fields.get('raw_gastos_subvencionables')
            extraction.raw_forma_justificacion = fields.get('raw_forma_justificacion')
            extraction.raw_plazo_ejecucion = fields.get('raw_plazo_ejecucion')
            extraction.raw_plazo_justificacion = fields.get('raw_plazo_justificacion')
            extraction.raw_forma_pago = fields.get('raw_forma_pago')
            extraction.raw_compatibilidad = fields.get('raw_compatibilidad')
            extraction.raw_publicidad = fields.get('raw_publicidad')
            extraction.raw_garantias = fields.get('raw_garantias')
            extraction.raw_subcontratacion = fields.get('raw_subcontratacion')

            db.commit()
            logger.success("✓ Database updated successfully!")
        else:
            logger.info("\n⚠️  DRY RUN MODE - Database not updated")

        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python test_enhanced_extraction.py <numero_convocatoria> [--save]")
        logger.info("Example: python test_enhanced_extraction.py 870434")
        logger.info("         python test_enhanced_extraction.py 870434 --save")
        logger.info("\nNote: This script ALWAYS reprocesses (bypasses deduplication)")
        sys.exit(1)

    numero = sys.argv[1]
    save_to_db = '--save' in sys.argv

    logger.info("Enhanced Extraction Test Script")
    logger.info("⚠️  Force reprocess mode: Will extract even if already processed")
    logger.info("=" * 80)

    success = test_extraction(numero, dry_run=not save_to_db)

    if success:
        logger.success("\n✓ Test completed successfully!")
        if not save_to_db:
            logger.info("\nTo save results to database, run with --save flag:")
            logger.info(f"  python scripts/test_enhanced_extraction.py {numero} --save")
    else:
        logger.error("\n✗ Test failed")
        sys.exit(1)
