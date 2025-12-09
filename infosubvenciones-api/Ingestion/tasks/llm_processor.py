"""LLM Processor Celery task - processes PDF text with Gemini to generate summaries and extract fields."""
from celery import Task, group
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from loguru import logger
import traceback
from pathlib import Path

from config.celery_app import app as celery_app
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from models.staging import StagingItem, ProcessingStatus
from models.convocatoria import Convocatoria
from services.gemini_client import GeminiClient
from services.field_normalizer import FieldNormalizer
from config.settings import get_settings

settings = get_settings()


class LLMProcessorTask(Task):
    """Base task for LLM processing with shared Gemini client and normalizer."""

    _gemini_client = None
    _field_normalizer = None

    @property
    def gemini_client(self) -> GeminiClient:
        """Lazy-load Gemini client (reused across task invocations)."""
        if self._gemini_client is None:
            self._gemini_client = GeminiClient()
        return self._gemini_client

    @property
    def field_normalizer(self) -> FieldNormalizer:
        """Lazy-load field normalizer (reused across task invocations)."""
        if self._field_normalizer is None:
            self._field_normalizer = FieldNormalizer()
        return self._field_normalizer


@celery_app.task(
    bind=True,
    base=LLMProcessorTask,
    name='tasks.process_with_llm',
    max_retries=3,
    default_retry_delay=120,  # 2 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes
    retry_jitter=True
)
def process_with_llm(self, extraction_id: int, force_reprocess: bool = False) -> Dict[str, Any]:
    """
    Process a PDF extraction with Gemini LLM.

    This task:
    1. Fetches the PDF extraction record
    2. Loads the markdown text
    3. Generates summary with Gemini
    4. Extracts structured fields with Gemini
    5. Updates pdf_extractions table

    Args:
        extraction_id: ID of pdf_extractions record to process
        force_reprocess: If True, bypass deduplication check and reprocess (default: False)

    Returns:
        Dictionary with processing results
    """
    db: Session = next(get_db())

    try:
        # Fetch PDF extraction
        stmt = select(PDFExtraction).where(PDFExtraction.id == extraction_id)
        extraction = db.execute(stmt).scalar_one_or_none()

        if not extraction:
            logger.error(f"PDF extraction {extraction_id} not found")
            return {'success': False, 'error': 'Extraction not found'}

        numero = extraction.numero_convocatoria

        # Check if already processed by LLM (skip if force_reprocess is True)
        target_model = settings.gemini_model
        if extraction.extraction_model == target_model and not force_reprocess:
            logger.info(f"Extraction {extraction_id} already processed with LLM, skipping")
            return {
                'success': True,
                'skipped': True,
                'reason': 'Already processed with LLM',
                'numero_convocatoria': numero
            }

        if force_reprocess:
            logger.warning(f"Force reprocess enabled - reprocessing extraction {extraction_id}")

        # Load markdown text
        if not extraction.markdown_path:
            logger.error(f"No markdown path for extraction {extraction_id}")
            extraction.extraction_error = "No markdown file available"
            db.commit()
            return {
                'success': False,
                'error': 'No markdown file',
                'numero_convocatoria': numero
            }

        # Read markdown file
        try:
            md_path = Path(extraction.markdown_path)
            if not md_path.exists():
                raise FileNotFoundError(f"Markdown file not found: {extraction.markdown_path}")

            with open(md_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Remove metadata header from markdown
            if text.startswith('#'):
                parts = text.split('---', 2)
                if len(parts) >= 3:
                    text = parts[2].strip()

        except Exception as e:
            logger.error(f"Failed to read markdown for extraction {extraction_id}: {e}")
            extraction.extraction_error = f"Failed to read markdown: {str(e)}"
            db.commit()
            return {
                'success': False,
                'error': f'Failed to read markdown: {str(e)}',
                'numero_convocatoria': numero
            }

        # Check if text is sufficient
        if not text or len(text.strip()) < 50:
            logger.warning(f"Text too short for LLM processing: {numero}")
            extraction.extraction_error = "Text too short for LLM processing"
            extraction.extraction_model = target_model
            extraction.extraction_confidence = 0.0
            db.commit()
            return {
                'success': True,
                'skipped': True,
                'reason': 'Text too short',
                'numero_convocatoria': numero
            }

        logger.info(f"Processing with LLM: {numero} ({len(text)} chars)")

        # Process with Gemini
        try:
            summary, fields, confidence = self.gemini_client.process_pdf_text(
                text,
                numero
            )

        except Exception as e:
            logger.error(f"Gemini API error for {numero}: {e}")
            extraction.extraction_error = f"Gemini API error: {str(e)}"
            db.commit()
            raise  # Re-raise for Celery retry

        # Apply field normalization
        try:
            normalized_fields = self.field_normalizer.normalize_all_fields(fields)
            # Merge normalized fields back into fields dict
            fields.update(normalized_fields)
            logger.debug(f"Normalized {len(normalized_fields)} fields for {numero}")
        except Exception as e:
            logger.warning(f"Field normalization failed for {numero}: {e}")
            # Continue with raw fields if normalization fails

        # Update extraction record with LLM results
        try:
            # Store full text and summary
            extraction.extracted_text = text  # Full PDF text
            extraction.extracted_summary = summary  # LLM-generated summary
            extraction.summary_preview = summary[:500] if summary else None  # First 500 chars

            # Extract basic info from fields (LLM extracts these too)
            extraction.titulo = fields.get('titulo')
            extraction.organismo = fields.get('organismo')
            extraction.ambito_geografico = fields.get('ambito_geografico')

            # Beneficiary info (for nominative grants)
            extraction.beneficiario_nombre = fields.get('beneficiario_nombre')
            extraction.beneficiario_cif = fields.get('beneficiario_cif')
            extraction.proyecto_nombre = fields.get('proyecto_nombre')

            # === NEW FIELDS ===

            # Purpose/Finalidad
            extraction.finalidad_pdf = fields.get('finalidad_pdf')
            extraction.finalidad_descripcion_pdf = fields.get('finalidad_descripcion_pdf')

            # Beneficiary types (raw + normalized)
            extraction.tipos_beneficiario_raw = fields.get('tipos_beneficiario_raw')
            extraction.tipos_beneficiario_normalized = fields.get('tipos_beneficiario_normalized')

            # Sectors (raw + inferred)
            extraction.sectores_raw = fields.get('sectores_raw')
            extraction.sectores_inferidos = fields.get('sectores_inferidos')

            # Instruments (raw + normalized)
            extraction.instrumentos_raw = fields.get('instrumentos_raw')
            extraction.instrumento_normalizado = fields.get('instrumento_normalizado')

            # Procedure
            extraction.procedimiento = fields.get('procedimiento')

            # Region (mentioned + NUTS)
            extraction.region_mencionada = fields.get('region_mencionada')
            extraction.region_nuts = fields.get('region_nuts')

            # Signatories
            extraction.firmantes = fields.get('firmantes')

            # CSV verification
            extraction.csv_codigo = fields.get('csv_codigo')
            extraction.url_verificacion = fields.get('url_verificacion')

            # Required reports
            extraction.memoria_obligatoria = fields.get('memoria_obligatoria')

            # Compatibility flag
            extraction.es_compatible_otras_ayudas = fields.get('es_compatible_otras_ayudas')

            # === PHASE 2 FIELDS ===

            # Scope inference (objeto is in convocatorias table, not here)
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

            # Update structured fields (financial details)
            extraction.gastos_subvencionables = fields.get('gastos_subvencionables')
            extraction.cuantia_subvencion = fields.get('cuantia_subvencion')
            extraction.cuantia_min = fields.get('cuantia_min')
            extraction.cuantia_max = fields.get('cuantia_max')
            extraction.intensidad_ayuda = fields.get('intensidad_ayuda')
            extraction.compatibilidad_otras_ayudas = fields.get('compatibilidad_otras_ayudas')

            # Deadlines & execution
            extraction.plazo_ejecucion = fields.get('plazo_ejecucion')
            extraction.plazo_justificacion = fields.get('plazo_justificacion')
            extraction.fecha_inicio_ejecucion = fields.get('fecha_inicio_ejecucion')
            extraction.fecha_fin_ejecucion = fields.get('fecha_fin_ejecucion')
            extraction.plazo_resolucion = fields.get('plazo_resolucion')

            # Justification requirements
            extraction.forma_justificacion = fields.get('forma_justificacion')
            extraction.documentacion_requerida = fields.get('documentacion_requerida')
            extraction.sistema_evaluacion = fields.get('sistema_evaluacion')

            # Payment & guarantees
            extraction.forma_pago = fields.get('forma_pago')
            extraction.pago_anticipado = fields.get('pago_anticipado')
            extraction.garantias = fields.get('garantias')
            extraction.exige_aval = fields.get('exige_aval')

            # Obligations & conditions
            extraction.obligaciones_beneficiario = fields.get('obligaciones_beneficiario')
            extraction.publicidad_requerida = fields.get('publicidad_requerida')
            extraction.subcontratacion = fields.get('subcontratacion')
            extraction.modificaciones_permitidas = fields.get('modificaciones_permitidas')

            # Specific requirements
            extraction.requisitos_tecnicos = fields.get('requisitos_tecnicos')
            extraction.criterios_valoracion = fields.get('criterios_valoracion')
            extraction.documentos_fase_solicitud = fields.get('documentos_fase_solicitud')

            # Update metadata
            extraction.extraction_model = target_model
            extraction.extraction_confidence = confidence
            extraction.extraction_error = None  # Clear any previous errors

            # Update convocatorias table with titulo and pdf_url
            try:
                stmt = select(Convocatoria).where(
                    Convocatoria.id == extraction.convocatoria_id
                )
                convocatoria = db.execute(stmt).scalar_one_or_none()

                if convocatoria:
                    # Update titulo if extracted and not already set
                    if extraction.titulo and not convocatoria.titulo:
                        convocatoria.titulo = extraction.titulo
                        logger.info(f"Updated convocatoria titulo: {extraction.titulo[:50]}...")

                    # Backfill sectors from LLM if API sectors are empty
                    if (not convocatoria.sectores or len(convocatoria.sectores) == 0) and extraction.sectores_inferidos:
                        convocatoria.sectores = extraction.sectores_inferidos
                        logger.info("Updated convocatoria sectores from LLM")
                    # Backfill normalized sectors if missing
                    if (not convocatoria.sectores_normalizados or len(convocatoria.sectores_normalizados) == 0):
                        if convocatoria.sectores and len(convocatoria.sectores) > 0:
                            convocatoria.sectores_normalizados = convocatoria.sectores
                        elif extraction.sectores_inferidos:
                            convocatoria.sectores_normalizados = extraction.sectores_inferidos
                            logger.info("Updated convocatoria sectores_normalizados from LLM")
                    # Backfill beneficiaries normalized if missing
                    if (not convocatoria.beneficiarios_normalizados or len(convocatoria.beneficiarios_normalizados) == 0) and extraction.tipos_beneficiario_normalized:
                        convocatoria.beneficiarios_normalizados = extraction.tipos_beneficiario_normalized
                        logger.info("Updated convocatoria beneficiarios_normalizados from LLM")
                    # Backfill region_nuts if missing
                    if (not convocatoria.region_nuts or len(convocatoria.region_nuts) == 0) and extraction.region_nuts:
                        if isinstance(extraction.region_nuts, list):
                            convocatoria.region_nuts = extraction.region_nuts
                        else:
                            convocatoria.region_nuts = [extraction.region_nuts]
                        logger.info("Updated convocatoria region_nuts from LLM")

                    # Get pdf_url from staging_items if not already set
                    if not convocatoria.pdf_url:
                        stmt_staging = select(StagingItem).where(
                            StagingItem.numero_convocatoria == numero
                        )
                        staging_item = db.execute(stmt_staging).scalar_one_or_none()
                        if staging_item and staging_item.pdf_url:
                            convocatoria.pdf_url = staging_item.pdf_url
                            logger.info(f"Updated convocatoria pdf_url")
                else:
                    logger.warning(f"Convocatoria not found for extraction {extraction_id}")

            except Exception as e:
                logger.warning(f"Failed to update convocatoria table: {e}")
                # Don't fail the whole task if this update fails

            db.commit()

            logger.success(
                f"LLM processing completed for {numero}: "
                f"summary={len(summary)} chars, fields={len(fields)}, confidence={confidence:.2f}"
            )

            return {
                'success': True,
                'numero_convocatoria': numero,
                'summary_length': len(summary),
                'fields_extracted': len(fields),
                'confidence': confidence,
                'fields': list(fields.keys())
            }

        except Exception as e:
            logger.error(f"Failed to update extraction {extraction_id}: {e}")
            db.rollback()
            raise

    except Exception as e:
        logger.error(f"Unexpected error processing extraction {extraction_id}: {e}")
        logger.error(traceback.format_exc())
        raise

    finally:
        db.close()


@celery_app.task(name='tasks.process_llm_batch')
def process_llm_batch(limit: int = 10, offset: int = 0) -> Dict[str, Any]:
    """
    Process a batch of PDF extractions with LLM.

    This task:
    1. Fetches pdf_extractions not yet processed by LLM
    2. Creates parallel process_with_llm tasks
    3. Returns summary of batch processing

    Args:
        limit: Number of items to process in this batch
        offset: Offset for pagination

    Returns:
        Dictionary with batch processing summary
    """
    db: Session = next(get_db())

    try:
        # Fetch extractions ready for LLM processing
        # (extraction_model = 'pymupdf' means PDF extracted but not LLM processed)
        stmt = (
            select(PDFExtraction)
            .where(PDFExtraction.extraction_model == 'pymupdf')
            .where(PDFExtraction.pdf_word_count > 0)  # Only non-empty PDFs
            .limit(limit)
            .offset(offset)
        )

        extractions = db.execute(stmt).scalars().all()

        if not extractions:
            logger.info("No PDF extractions ready for LLM processing")
            return {
                'success': True,
                'processed': 0,
                'message': 'No items to process'
            }

        logger.info(f"Processing batch of {len(extractions)} extractions with LLM")

        # Create parallel tasks
        task_group = group(
            process_with_llm.s(extraction.id) for extraction in extractions
        )

        # Execute tasks in parallel
        result = task_group.apply_async()

        return {
            'success': True,
            'batch_size': len(extractions),
            'task_group_id': result.id,
            'message': f'Started LLM processing for {len(extractions)} extractions'
        }

    except Exception as e:
        logger.error(f"Error creating LLM batch: {e}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

    finally:
        db.close()


@celery_app.task(name='tasks.get_llm_processing_stats')
def get_llm_processing_stats() -> Dict[str, Any]:
    """
    Get statistics about LLM processing progress.

    Returns:
        Dictionary with processing stats
    """
    db: Session = next(get_db())

    try:
        from sqlalchemy import func

        # Count extractions by processing status
        stmt = select(func.count(PDFExtraction.id))
        total_extractions = db.execute(stmt).scalar()

        # Count LLM-processed
        stmt = select(func.count(PDFExtraction.id)).where(
            PDFExtraction.extraction_model == settings.gemini_model
        )
        llm_processed = db.execute(stmt).scalar()

        # Count pending (pymupdf only)
        stmt = select(func.count(PDFExtraction.id)).where(
            PDFExtraction.extraction_model == 'pymupdf'
        )
        pending_llm = db.execute(stmt).scalar()

        # Count with errors
        stmt = select(func.count(PDFExtraction.id)).where(
            PDFExtraction.extraction_error.isnot(None)
        )
        error_count = db.execute(stmt).scalar()

        # Average confidence
        stmt = select(func.avg(PDFExtraction.extraction_confidence)).where(
            PDFExtraction.extraction_confidence.isnot(None)
        )
        avg_confidence = db.execute(stmt).scalar() or 0.0

        return {
            'total_extractions': total_extractions,
            'llm_processed': llm_processed,
            'pending_llm': pending_llm,
            'extraction_errors': error_count,
            'avg_confidence': float(avg_confidence),
            'completion_rate': (
                (llm_processed / total_extractions * 100)
                if total_extractions > 0 else 0
            )
        }

    except Exception as e:
        logger.error(f"Error getting LLM processing stats: {e}")
        return {
            'error': str(e)
        }

    finally:
        db.close()


# Direct execution support (for testing without Celery worker)
if __name__ == "__main__":
    logger.info("Testing LLM processor task...")

    # Test with an extraction ID
    test_extraction_id = 1

    try:
        result = process_with_llm(test_extraction_id)
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
