"""Test script for PDF processing pipeline (download + text extraction)."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from loguru import logger

from config.database import get_db
from models.staging import StagingItem, ProcessingStatus
from models.convocatoria import Convocatoria
from models.pdf_extraction import PDFExtraction
from tasks.pdf_processor import process_pdf, process_pdf_batch, get_pdf_processing_stats


def test_single_pdf_processing():
    """Test processing a single PDF from staging queue."""
    logger.info("=" * 80)
    logger.info("TEST 1: Single PDF Processing")
    logger.info("=" * 80)

    db: Session = next(get_db())

    try:
        # Find a staging item with a PDF URL that hasn't been processed yet
        stmt = (
            select(StagingItem)
            .where(StagingItem.pdf_url.isnot(None))
            .where(StagingItem.status == ProcessingStatus.PENDING)
            .limit(1)
        )

        staging_item = db.execute(stmt).scalar_one_or_none()

        if not staging_item:
            logger.warning("No staging items with PDFs found for testing")
            logger.info("Creating a test staging item first...")

            # Check if we have any convocatorias with PDF URLs
            stmt = (
                select(Convocatoria)
                .where(Convocatoria.documentos.isnot(None))
                .limit(1)
            )

            conv = db.execute(stmt).scalar_one_or_none()

            if conv:
                logger.info(f"Found convocatoria with documents: {conv.numero_convocatoria}")
                logger.info(f"Documents: {conv.documentos}")
                logger.info("\nPlease run the fetcher first to populate staging_items with PDF URLs")
            else:
                logger.error("No convocatorias found in database")
                logger.info("Please run test_fetcher.py first")

            return

        logger.info(f"Processing PDF for staging item {staging_item.id}")
        logger.info(f"Numero: {staging_item.numero_convocatoria}")
        logger.info(f"PDF URL: {staging_item.pdf_url}")
        logger.info(f"Current status: {staging_item.status}")

        # Process the PDF (direct call, no Celery worker needed)
        logger.info("\n--- Starting PDF processing ---")
        result = process_pdf(staging_item.id)

        logger.info("\n--- Processing Result ---")
        logger.info(f"Success: {result.get('success')}")

        if result.get('success'):
            if result.get('skipped'):
                logger.warning(f"Skipped: {result.get('reason')}")
            else:
                logger.success("PDF processed successfully!")
                logger.info(f"PDF Hash: {result.get('pdf_hash')}")
                logger.info(f"File Size: {result.get('file_size')} bytes")
                logger.info(f"Page Count: {result.get('page_count')}")
                logger.info(f"Word Count: {result.get('word_count')}")
                logger.info(f"Is Scanned: {result.get('is_scanned')}")
                logger.info(f"Markdown Path: {result.get('markdown_path')}")

                # Verify database records
                logger.info("\n--- Verifying Database ---")

                # Check staging item status
                db.refresh(staging_item)
                logger.info(f"Staging item status: {staging_item.status}")

                # Check PDF extraction record
                stmt = select(PDFExtraction).where(
                    PDFExtraction.numero_convocatoria == staging_item.numero_convocatoria
                )
                extraction = db.execute(stmt).scalar_one_or_none()

                if extraction:
                    logger.success("PDF extraction record created!")
                    logger.info(f"Extraction ID: {extraction.id}")
                    logger.info(f"Page Count: {extraction.pdf_page_count}")
                    logger.info(f"Word Count: {extraction.pdf_word_count}")
                    logger.info(f"Markdown Path: {extraction.markdown_path}")
                    logger.info(f"Extraction Model: {extraction.extraction_model}")
                else:
                    logger.error("PDF extraction record not found!")
        else:
            logger.error(f"Processing failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())

    finally:
        db.close()


def test_batch_pdf_processing():
    """Test processing a batch of PDFs."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Batch PDF Processing")
    logger.info("=" * 80)

    logger.info("Processing batch of 5 PDFs...")

    try:
        result = process_pdf_batch(limit=5, offset=0)

        logger.info("\n--- Batch Result ---")
        logger.info(f"Success: {result.get('success')}")

        if result.get('success'):
            logger.info(f"Batch Size: {result.get('batch_size', 0)}")
            logger.info(f"Message: {result.get('message')}")

            if result.get('batch_size', 0) > 0:
                logger.success(f"Started processing {result.get('batch_size')} PDFs")
                logger.info("Note: Tasks are running in parallel via Celery")
                logger.info("Check logs or run get_stats test to see progress")
        else:
            logger.error(f"Batch processing failed: {result.get('error')}")

    except Exception as e:
        logger.error(f"Batch test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def test_get_stats():
    """Test getting PDF processing statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: PDF Processing Statistics")
    logger.info("=" * 80)

    try:
        stats = get_pdf_processing_stats()

        if 'error' in stats:
            logger.error(f"Failed to get stats: {stats['error']}")
            return

        logger.info("\n--- Staging Items by Status ---")
        status_counts = stats.get('staging_status_counts', {})
        for status, count in status_counts.items():
            logger.info(f"  {status}: {count}")

        logger.info("\n--- PDF Extractions ---")
        logger.info(f"Total Extractions: {stats.get('total_pdf_extractions', 0)}")
        logger.info(f"Extraction Errors: {stats.get('extraction_errors', 0)}")
        logger.info(f"Success Rate: {stats.get('success_rate', 0):.2f}%")

        # Get additional stats from database
        db: Session = next(get_db())

        try:
            # Count PDFs with text extracted
            stmt = select(func.count(PDFExtraction.id)).where(
                PDFExtraction.pdf_word_count > 0
            )
            pdfs_with_text = db.execute(stmt).scalar()

            # Count scanned PDFs
            stmt = select(func.count(PDFExtraction.id)).where(
                PDFExtraction.extraction_error.like('%scanned%')
            )
            scanned_pdfs = db.execute(stmt).scalar()

            logger.info(f"PDFs with extracted text: {pdfs_with_text}")
            logger.info(f"Scanned PDFs (no text): {scanned_pdfs}")

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Stats test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def test_downloader_stats():
    """Test PDF downloader statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: PDF Downloader Statistics")
    logger.info("=" * 80)

    try:
        from services.pdf_downloader import PDFDownloader

        with PDFDownloader() as downloader:
            stats = downloader.get_download_stats()

            logger.info("\n--- Download Stats ---")
            logger.info(f"Total PDFs Downloaded: {stats['total_count']}")
            logger.info(f"Total Size: {stats['total_size_mb']:.2f} MB")
            logger.info(f"Downloads Directory: {stats['downloads_dir']}")

            if stats['total_count'] > 0:
                avg_size = stats['total_size_mb'] / stats['total_count']
                logger.info(f"Average PDF Size: {avg_size:.2f} MB")

    except Exception as e:
        logger.error(f"Downloader stats test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    logger.info("PDF Processor Test Suite")
    logger.info("=" * 80)

    # Run tests
    test_single_pdf_processing()
    test_batch_pdf_processing()
    test_get_stats()
    test_downloader_stats()

    logger.info("\n" + "=" * 80)
    logger.info("Test suite completed!")
    logger.info("=" * 80)
