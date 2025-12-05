"""PDF Processor Celery task - downloads and extracts text from PDFs."""
from celery import Task, group, chord
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional
from loguru import logger
import traceback

from config.celery_app import app as celery_app
from config.database import get_db
from models.staging import StagingItem, ProcessingStatus
from models.convocatoria import Convocatoria
from models.pdf_extraction import PDFExtraction
from services.pdf_downloader import PDFDownloader
from services.text_extractor import TextExtractor


class PDFProcessorTask(Task):
    """Base task for PDF processing with shared resources."""

    _downloader = None
    _extractor = None

    @property
    def downloader(self) -> PDFDownloader:
        """Lazy-load PDF downloader (reused across task invocations)."""
        if self._downloader is None:
            self._downloader = PDFDownloader()
        return self._downloader

    @property
    def extractor(self) -> TextExtractor:
        """Lazy-load text extractor (reused across task invocations)."""
        if self._extractor is None:
            self._extractor = TextExtractor()
        return self._extractor


@celery_app.task(
    bind=True,
    base=PDFProcessorTask,
    name='tasks.process_pdf',
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes
    retry_jitter=True
)
def process_pdf(self, staging_id: int) -> dict:
    """
    Process a single PDF: download + extract text.

    This task:
    1. Fetches the staging item
    2. Downloads the PDF from the URL
    3. Extracts text using PyMuPDF
    4. Saves extracted text to pdf_extractions table
    5. Updates staging item status

    Args:
        staging_id: ID of staging_items record to process

    Returns:
        Dictionary with processing results
    """
    db: Session = next(get_db())

    try:
        # Fetch staging item
        stmt = select(StagingItem).where(StagingItem.id == staging_id)
        staging_item = db.execute(stmt).scalar_one_or_none()

        if not staging_item:
            logger.error(f"Staging item {staging_id} not found")
            return {'success': False, 'error': 'Staging item not found'}

        # Fetch associated convocatoria
        stmt = select(Convocatoria).where(
            Convocatoria.numero_convocatoria == staging_item.numero_convocatoria
        )
        convocatoria = db.execute(stmt).scalar_one_or_none()

        if not convocatoria:
            logger.error(
                f"Convocatoria not found for staging item {staging_id}: "
                f"{staging_item.numero_convocatoria}"
            )
            staging_item.mark_failed('Convocatoria not found')
            staging_item.last_stage = 'processor'
            db.commit()
            return {'success': False, 'error': 'Convocatoria not found'}

        # Check if PDF extraction already exists
        stmt = select(PDFExtraction).where(
            PDFExtraction.convocatoria_id == convocatoria.id
        )
        existing_extraction = db.execute(stmt).scalar_one_or_none()

        if existing_extraction:
            logger.info(
                f"PDF extraction already exists for {staging_item.numero_convocatoria}, skipping"
            )
            staging_item.mark_completed()
            staging_item.last_stage = 'processor'
            db.commit()
            return {
                'success': True,
                'skipped': True,
                'reason': 'Already processed',
                'numero_convocatoria': staging_item.numero_convocatoria
            }

        # Extract PDF URL from staging item
        pdf_url = staging_item.pdf_url

        if not pdf_url:
            logger.warning(
                f"No PDF URL for {staging_item.numero_convocatoria}, marking as no_pdf"
            )
            staging_item.mark_skipped('No PDF URL')
            staging_item.last_stage = 'processor'
            db.commit()
            return {
                'success': True,
                'skipped': True,
                'reason': 'No PDF URL',
                'numero_convocatoria': staging_item.numero_convocatoria
            }

        # Update status to processing
        staging_item.mark_processing('processor')
        db.commit()

        logger.info(f"Processing PDF for {staging_item.numero_convocatoria}")

        # Step 1: Download PDF
        try:
            file_path, pdf_hash, file_size = self.downloader.download_pdf(
                pdf_url,
                staging_item.numero_convocatoria
            )

            if not file_path:
                raise Exception("PDF download failed")

        except Exception as e:
            logger.error(
                f"Failed to download PDF for {staging_item.numero_convocatoria}: {e}"
            )
            staging_item.mark_failed(f"Download error: {str(e)}")
            staging_item.last_stage = 'processor'
            db.commit()
            raise  # Re-raise for Celery retry

        # Step 2: Extract text
        try:
            text, metadata, markdown_path = self.extractor.extract_text(
                file_path,
                save_markdown=True
            )

            if not text:
                logger.warning(
                    f"No text extracted from PDF for {staging_item.numero_convocatoria}"
                )
                # Still create a record, but mark as scanned/empty
                text = ""

        except Exception as e:
            logger.error(
                f"Failed to extract text from PDF for {staging_item.numero_convocatoria}: {e}"
            )
            staging_item.mark_failed(f"Extraction error: {str(e)}")
            staging_item.last_stage = 'processor'
            db.commit()
            raise  # Re-raise for Celery retry

        # Step 3: Create PDFExtraction record (basic version - no LLM yet)
        try:
            pdf_extraction = PDFExtraction(
                convocatoria_id=convocatoria.id,
                numero_convocatoria=staging_item.numero_convocatoria,
                markdown_path=markdown_path,
                pdf_page_count=metadata.get('page_count'),
                pdf_word_count=metadata.get('word_count'),
                extraction_model='pymupdf',  # Will be updated to gemini-2.0-flash later
                extraction_confidence=None,  # Will be set after LLM processing
                extraction_error=None if text else "No text extracted (scanned PDF?)"
            )

            db.add(pdf_extraction)
            db.commit()

            logger.success(
                f"Created PDF extraction record for {staging_item.numero_convocatoria}"
            )

        except Exception as e:
            logger.error(
                f"Failed to save PDF extraction for {staging_item.numero_convocatoria}: {e}"
            )
            db.rollback()
            staging_item.mark_failed(f"Database error: {str(e)}")
            staging_item.last_stage = 'processor'
            db.commit()
            raise

        # Step 4: Update staging item status
        staging_item.mark_completed()
        staging_item.last_stage = 'processor'
        db.commit()

        return {
            'success': True,
            'numero_convocatoria': staging_item.numero_convocatoria,
            'pdf_hash': pdf_hash,
            'file_size': file_size,
            'page_count': metadata.get('page_count'),
            'word_count': metadata.get('word_count'),
            'is_scanned': metadata.get('is_scanned', False),
            'markdown_path': markdown_path
        }

    except Exception as e:
        logger.error(f"Unexpected error processing PDF for staging_id {staging_id}: {e}")
        logger.error(traceback.format_exc())
        raise

    finally:
        db.close()


@celery_app.task(name='tasks.process_pdf_batch')
def process_pdf_batch(limit: int = 10, offset: int = 0) -> dict:
    """
    Process a batch of PDFs from the staging queue.

    This task:
    1. Fetches staging items with status='pending' or 'fetched'
    2. Creates parallel process_pdf tasks for each item
    3. Returns summary of batch processing

    Args:
        limit: Number of items to process in this batch
        offset: Offset for pagination

    Returns:
        Dictionary with batch processing summary
    """
    db: Session = next(get_db())

    try:
        # Fetch staging items ready for PDF processing
        stmt = (
            select(StagingItem)
            .where(StagingItem.status == ProcessingStatus.PENDING)
            .where(StagingItem.pdf_url.isnot(None))  # Only items with PDF URLs
            .limit(limit)
            .offset(offset)
        )

        staging_items = db.execute(stmt).scalars().all()

        if not staging_items:
            logger.info("No staging items ready for PDF processing")
            return {
                'success': True,
                'processed': 0,
                'message': 'No items to process'
            }

        logger.info(f"Processing batch of {len(staging_items)} PDFs")

        # Create parallel tasks
        task_group = group(
            process_pdf.s(item.id) for item in staging_items
        )

        # Execute tasks in parallel
        result = task_group.apply_async()

        return {
            'success': True,
            'batch_size': len(staging_items),
            'task_group_id': result.id,
            'message': f'Started processing {len(staging_items)} PDFs'
        }

    except Exception as e:
        logger.error(f"Error creating PDF batch: {e}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

    finally:
        db.close()


@celery_app.task(name='tasks.get_pdf_processing_stats')
def get_pdf_processing_stats() -> dict:
    """
    Get statistics about PDF processing progress.

    Returns:
        Dictionary with processing stats
    """
    db: Session = next(get_db())

    try:
        from sqlalchemy import func

        # Count staging items by status
        stmt = select(StagingItem.status, func.count(StagingItem.id))
        stmt = stmt.group_by(StagingItem.status)
        status_counts = dict(db.execute(stmt).all())

        # Count PDF extractions
        stmt = select(func.count(PDFExtraction.id))
        total_extractions = db.execute(stmt).scalar()

        # Count extractions with errors
        stmt = select(func.count(PDFExtraction.id)).where(
            PDFExtraction.extraction_error.isnot(None)
        )
        error_count = db.execute(stmt).scalar()

        return {
            'staging_status_counts': status_counts,
            'total_pdf_extractions': total_extractions,
            'extraction_errors': error_count,
            'success_rate': (
                (total_extractions - error_count) / total_extractions * 100
                if total_extractions > 0 else 0
            )
        }

    except Exception as e:
        logger.error(f"Error getting PDF processing stats: {e}")
        return {
            'error': str(e)
        }

    finally:
        db.close()


# Direct execution support (for testing without Celery worker)
if __name__ == "__main__":
    logger.info("Testing PDF processor task...")

    # Test with a staging item ID
    test_staging_id = 1

    try:
        result = process_pdf(test_staging_id)
        logger.info(f"Result: {result}")
    except Exception as e:
        logger.error(f"Test failed: {e}")
