"""Test script for LLM processing (Gemini summaries + field extraction)."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from loguru import logger

from config.database import get_db
from models.pdf_extraction import PDFExtraction
from models.staging import StagingItem, ProcessingStatus
from config.settings import get_settings
from tasks.llm_processor import process_with_llm, process_llm_batch, get_llm_processing_stats

settings = get_settings()


def test_single_llm_processing():
    """Test processing a single PDF extraction with LLM."""
    logger.info("=" * 80)
    logger.info("TEST 1: Single LLM Processing")
    logger.info("=" * 80)

    db: Session = next(get_db())

    try:
        # Find a PDF extraction that hasn't been processed by LLM yet
        stmt = (
            select(PDFExtraction)
            .where(PDFExtraction.extraction_model == 'pymupdf')
            .where(PDFExtraction.pdf_word_count > 0)
            .limit(1)
        )

        extraction = db.execute(stmt).scalar_one_or_none()

        if not extraction:
            logger.warning("No PDF extractions found for LLM processing")
            logger.info("All extractions may already be processed")

            # Show what we have
            stmt = select(func.count(PDFExtraction.id))
            total = db.execute(stmt).scalar()

            stmt = select(func.count(PDFExtraction.id)).where(
                PDFExtraction.extraction_model == settings.gemini_model
            )
            processed = db.execute(stmt).scalar()

            logger.info(f"Total extractions: {total}")
            logger.info(f"LLM processed: {processed}")
            logger.info(f"Pending: {total - processed}")

            return

        logger.info(f"Processing extraction ID: {extraction.id}")
        logger.info(f"Numero: {extraction.numero_convocatoria}")
        logger.info(f"Word count: {extraction.pdf_word_count}")
        logger.info(f"Markdown: {extraction.markdown_path}")

        # Process with LLM (direct call, no Celery worker needed)
        logger.info("\n--- Starting LLM processing ---")
        result = process_with_llm(extraction.id)

        logger.info("\n--- Processing Result ---")
        logger.info(f"Success: {result.get('success')}")

        if result.get('success'):
            if result.get('skipped'):
                logger.warning(f"Skipped: {result.get('reason')}")
            else:
                logger.success("LLM processing successful!")
                logger.info(f"Summary length: {result.get('summary_length')} chars")
                logger.info(f"Fields extracted: {result.get('fields_extracted')}")
                logger.info(f"Confidence: {result.get('confidence'):.2f}")
                logger.info(f"Fields: {result.get('fields')}")

                # Verify database update
                logger.info("\n--- Verifying Database ---")
                db.refresh(extraction)

                logger.info(f"Extraction model: {extraction.extraction_model}")
                logger.info(f"Confidence: {extraction.extraction_confidence}")
                logger.info(f"Gastos subvencionables: {extraction.gastos_subvencionables[:100] if extraction.gastos_subvencionables else 'None'}...")
                logger.info(f"Cuantía: {extraction.cuantia_subvencion}")
                logger.info(f"Plazo ejecución: {extraction.plazo_ejecucion}")

                # Show summary (stored in raw_gastos_subvencionables temporarily)
                if extraction.raw_gastos_subvencionables:
                    summary_preview = extraction.raw_gastos_subvencionables[:300]
                    logger.info(f"\nSummary preview:\n{summary_preview}...")
        else:
            logger.error(f"Processing failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        db.close()


def test_batch_llm_processing():
    """Test processing a batch of PDF extractions with LLM."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Batch LLM Processing")
    logger.info("=" * 80)

    logger.info("Processing batch of 3 extractions...")

    try:
        result = process_llm_batch(limit=3, offset=0)

        logger.info("\n--- Batch Result ---")
        logger.info(f"Success: {result.get('success')}")

        if result.get('success'):
            logger.info(f"Batch Size: {result.get('batch_size', 0)}")
            logger.info(f"Message: {result.get('message')}")

            if result.get('batch_size', 0) > 0:
                logger.success(f"Started processing {result.get('batch_size')} extractions")
                logger.info("Note: Tasks are running in parallel")
                logger.info("Check stats test to see progress")
        else:
            logger.error(f"Batch processing failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Batch test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def test_get_llm_stats():
    """Test getting LLM processing statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: LLM Processing Statistics")
    logger.info("=" * 80)

    try:
        stats = get_llm_processing_stats()

        if 'error' in stats:
            logger.error(f"Failed to get stats: {stats['error']}")
            return

        logger.info("\n--- LLM Processing Stats ---")
        logger.info(f"Total Extractions: {stats.get('total_extractions', 0)}")
        logger.info(f"LLM Processed: {stats.get('llm_processed', 0)}")
        logger.info(f"Pending LLM: {stats.get('pending_llm', 0)}")
        logger.info(f"Extraction Errors: {stats.get('extraction_errors', 0)}")
        logger.info(f"Average Confidence: {stats.get('avg_confidence', 0):.2f}")
        logger.info(f"Completion Rate: {stats.get('completion_rate', 0):.2f}%")

    except Exception as e:
        logger.error(f"Stats test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def test_field_quality():
    """Test quality of extracted fields."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Field Extraction Quality")
    logger.info("=" * 80)

    db: Session = next(get_db())

    try:
        # Get extractions processed by LLM
        stmt = (
            select(PDFExtraction)
            .where(PDFExtraction.extraction_model == settings.gemini_model)
            .limit(3)
        )

        extractions = db.execute(stmt).scalars().all()

        if not extractions:
            logger.warning("No LLM-processed extractions found")
            return

        logger.info(f"Analyzing {len(extractions)} LLM-processed extractions\n")

        for extraction in extractions:
            logger.info(f"--- {extraction.numero_convocatoria} ---")
            logger.info(f"Confidence: {extraction.extraction_confidence:.2f}")

            # Count non-null fields
            fields_populated = 0
            field_names = [
                'gastos_subvencionables', 'cuantia_subvencion', 'cuantia_min', 'cuantia_max',
                'intensidad_ayuda', 'plazo_ejecucion', 'plazo_justificacion',
                'forma_justificacion', 'forma_pago', 'pago_anticipado',
                'garantias', 'obligaciones_beneficiario', 'requisitos_tecnicos'
            ]

            for field in field_names:
                value = getattr(extraction, field, None)
                if value:
                    fields_populated += 1
                    # Show first 80 chars of value
                    value_str = str(value)[:80]
                    logger.info(f"  {field}: {value_str}...")

            logger.info(f"Fields populated: {fields_populated}/{len(field_names)}\n")

    except Exception as e:
        logger.error(f"Field quality test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        db.close()


if __name__ == "__main__":
    logger.info("LLM Processor Test Suite")
    logger.info("=" * 80)

    # Run tests
    test_single_llm_processing()
    test_batch_llm_processing()
    test_get_llm_stats()
    test_field_quality()

    logger.info("\n" + "=" * 80)
    logger.info("Test suite completed!")
    logger.info("=" * 80)
