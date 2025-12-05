"""
Process all PDFs with improved JSON extraction.

This script processes all PDF extractions directly (without Celery worker),
applying the improved JSON parsing and Phase 2 field extraction.

Usage:
    python scripts/process_all_pdfs.py
"""
import sys
from pathlib import Path

# Add Ingestion to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from loguru import logger
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from services.gemini_client import GeminiClient
from services.field_normalizer import FieldNormalizer


def process_all_pdfs():
    """Process all PDF extractions with improved extraction."""

    # Initialize services
    gemini_client = GeminiClient()
    field_normalizer = FieldNormalizer()

    db = next(get_db())

    try:
        # Get all extractions that need processing
        stmt = select(PDFExtraction).where(PDFExtraction.extraction_model == 'pymupdf')
        extractions = db.execute(stmt).scalars().all()

        logger.info(f'Processing {len(extractions)} PDFs with improved extraction...')
        logger.info('=' * 80)

        success_count = 0
        error_count = 0

        for extraction in extractions:
            numero = extraction.numero_convocatoria

            try:
                logger.info(f'\nProcessing {numero}...')

                # Load markdown
                if not extraction.markdown_path:
                    logger.error(f'No markdown path for {numero}')
                    error_count += 1
                    continue

                md_path = Path(extraction.markdown_path)
                if not md_path.exists():
                    logger.error(f'Markdown file not found: {md_path}')
                    error_count += 1
                    continue

                with open(md_path, 'r', encoding='utf-8') as f:
                    text = f.read()

                # Remove metadata header
                if text.startswith('#'):
                    parts = text.split('---', 2)
                    if len(parts) >= 3:
                        text = parts[2].strip()

                # Check text length
                if len(text.strip()) < 50:
                    logger.warning(f'Text too short for {numero}')
                    error_count += 1
                    continue

                # Process with Gemini
                summary, fields, confidence = gemini_client.process_pdf_text(text, numero)

                # Apply normalization
                normalized_fields = field_normalizer.normalize_all_fields(fields)
                fields.update(normalized_fields)

                # Update extraction record
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

                # PHASE 2 FIELDS
                extraction.tipo_administracion_raw = fields.get('tipo_administracion_raw')
                extraction.nivel_administracion_raw = fields.get('nivel_administracion_raw')
                extraction.ambito_raw = fields.get('ambito_raw')
                extraction.tipo_administracion_normalizado = fields.get('tipo_administracion_normalizado')
                extraction.nivel_administracion_normalizado = fields.get('nivel_administracion_normalizado')
                extraction.ambito_normalizado = fields.get('ambito_normalizado')
                extraction.beneficiarios_descripcion_pdf = fields.get('beneficiarios_descripcion_pdf')
                extraction.requisitos_beneficiarios_pdf = fields.get('requisitos_beneficiarios_pdf')
                extraction.importe_total_pdf = fields.get('importe_total_pdf')
                extraction.importe_maximo_pdf = fields.get('importe_maximo_pdf')
                extraction.forma_solicitud_pdf = fields.get('forma_solicitud_pdf')
                extraction.lugar_presentacion_pdf = fields.get('lugar_presentacion_pdf')
                extraction.url_tramite_pdf = fields.get('url_tramite_pdf')
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

                # Update metadata
                extraction.extraction_model = 'gemini-2.0-flash'
                extraction.extraction_confidence = confidence
                extraction.extraction_error = None

                db.commit()

                logger.success(f'Success: {len(fields)} fields, confidence {confidence:.2%}')
                success_count += 1

            except Exception as e:
                logger.error(f'Error processing {numero}: {e}')
                error_count += 1
                db.rollback()

        logger.info('')
        logger.info('=' * 80)
        logger.success(f'Completed: {success_count} successful, {error_count} errors')

        return success_count, error_count

    finally:
        db.close()


if __name__ == '__main__':
    success, errors = process_all_pdfs()

    if errors > 0:
        sys.exit(1)
