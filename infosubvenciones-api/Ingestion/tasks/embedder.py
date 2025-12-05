"""
Celery tasks for generating embeddings from PDF extractions.

Tasks:
- generate_embedding: Generate embedding for a single PDF extraction
- generate_batch_embeddings: Batch coordinator for multiple items
- get_embedding_stats: Get embedding generation statistics
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from config.celery_app import app as celery_app
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from models.embedding import Embedding
from services.embedding_generator import EmbeddingGenerator

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="embedder.generate_embedding",
)
def generate_embedding(self, extraction_id: int) -> Dict[str, Any]:
    """
    Generate embedding for a single PDF extraction.

    Args:
        extraction_id: ID of the PDFExtraction record

    Returns:
        Dict with status, extraction_id, and embedding_id

    Raises:
        Exception: If embedding generation fails after retries
    """
    logger.info(f"Starting embedding generation for extraction_id={extraction_id}")

    db: Session = next(get_db())

    try:
        # 1. Get the PDF extraction
        extraction = db.query(PDFExtraction).filter(
            PDFExtraction.id == extraction_id
        ).first()

        if not extraction:
            logger.error(f"PDFExtraction {extraction_id} not found")
            return {
                "status": "error",
                "extraction_id": extraction_id,
                "error": "Extraction not found"
            }

        # 2. Check if embedding already exists
        existing = db.query(Embedding).filter(
            Embedding.extraction_id == extraction_id
        ).first()

        if existing:
            logger.info(f"Embedding already exists for extraction_id={extraction_id}")
            return {
                "status": "skipped",
                "extraction_id": extraction_id,
                "embedding_id": existing.id,
                "reason": "Embedding already exists"
            }

        # 3. Prepare text for embedding
        generator = EmbeddingGenerator()

        # Get metadata from related convocatoria (if available)
        metadata = {}
        if extraction.staging_item and extraction.staging_item.convocatoria:
            conv = extraction.staging_item.convocatoria
            metadata = {
                "titulo": conv.titulo,
                "organismo": conv.organismo,
                "ambito": conv.ambito,
            }

        # Combine summary + full text + metadata
        text = generator.prepare_text_for_embedding(
            summary=extraction.summary_preview or extraction.extracted_summary,
            full_text=extraction.markdown_path,  # Will load from file if needed
            metadata=metadata
        )

        if len(text) < 50:
            logger.warning(f"Text too short for embedding: {len(text)} chars")
            return {
                "status": "skipped",
                "extraction_id": extraction_id,
                "reason": "Text too short (< 50 chars)"
            }

        # 4. Generate embedding
        logger.info(f"Generating embedding (text_len={len(text)})")

        # Use title from convocatoria if available
        title = metadata.get("titulo")

        embedding_vector = generator.generate_embedding(
            text=text,
            task_type="SEMANTIC_SIMILARITY",
            title=title
        )

        # 5. Store in database
        embedding = Embedding(
            extraction_id=extraction_id,
            embedding_vector=embedding_vector,
            model_name=generator.model_name,
            embedding_dimensions=len(embedding_vector),
            text_length=len(text),
            created_at=datetime.utcnow()
        )

        db.add(embedding)
        db.commit()
        db.refresh(embedding)

        logger.info(
            f"✅ Embedding generated: extraction_id={extraction_id}, "
            f"embedding_id={embedding.id}, dimensions={len(embedding_vector)}"
        )

        return {
            "status": "success",
            "extraction_id": extraction_id,
            "embedding_id": embedding.id,
            "dimensions": len(embedding_vector),
            "text_length": len(text)
        }

    except Exception as e:
        logger.error(
            f"Failed to generate embedding for extraction_id={extraction_id}: {e}",
            exc_info=True
        )

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        return {
            "status": "failed",
            "extraction_id": extraction_id,
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(name="embedder.generate_batch_embeddings")
def generate_batch_embeddings(
    limit: int = 100,
    offset: int = 0,
    reprocess: bool = False
) -> Dict[str, Any]:
    """
    Batch coordinator for generating embeddings.

    Queries PDFExtractions without embeddings and queues individual tasks.

    Args:
        limit: Maximum number of items to process
        offset: Offset for pagination
        reprocess: If True, regenerate embeddings even if they exist

    Returns:
        Dict with statistics about the batch job
    """
    logger.info(
        f"Starting batch embedding generation: limit={limit}, offset={offset}, "
        f"reprocess={reprocess}"
    )

    db: Session = next(get_db())

    try:
        # Build query
        query = db.query(PDFExtraction).filter(
            PDFExtraction.extracted_text.isnot(None),  # Must have text
            PDFExtraction.extracted_text != ""
        )

        # Exclude items with embeddings (unless reprocessing)
        if not reprocess:
            # Use LEFT JOIN to find extractions without embeddings
            query = query.outerjoin(Embedding).filter(
                Embedding.id.is_(None)
            )

        # Apply pagination
        extractions = query.order_by(
            PDFExtraction.created_at.desc()
        ).limit(limit).offset(offset).all()

        if not extractions:
            logger.info("No extractions found for embedding generation")
            return {
                "status": "success",
                "queued": 0,
                "message": "No items to process"
            }

        # Queue individual tasks
        queued = 0
        for extraction in extractions:
            try:
                generate_embedding.delay(extraction.id)
                queued += 1
            except Exception as e:
                logger.error(
                    f"Failed to queue embedding task for extraction_id={extraction.id}: {e}"
                )

        logger.info(f"✅ Queued {queued} embedding tasks")

        return {
            "status": "success",
            "queued": queued,
            "limit": limit,
            "offset": offset,
            "reprocess": reprocess
        }

    except Exception as e:
        logger.error(f"Failed to generate batch embeddings: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e)
        }

    finally:
        db.close()


def get_embedding_stats() -> Dict[str, Any]:
    """
    Get embedding generation statistics.

    Returns:
        Dict with counts and statistics
    """
    db: Session = next(get_db())

    try:
        # Total extractions
        total_extractions = db.query(func.count(PDFExtraction.id)).scalar() or 0

        # Total embeddings
        total_embeddings = db.query(func.count(Embedding.id)).scalar() or 0

        # Extractions without embeddings
        without_embeddings = db.query(func.count(PDFExtraction.id)).outerjoin(
            Embedding
        ).filter(
            Embedding.id.is_(None),
            PDFExtraction.extracted_text.isnot(None)
        ).scalar() or 0

        # Average embedding dimensions
        avg_dimensions = db.query(
            func.avg(Embedding.embedding_dimensions)
        ).scalar() or 0

        # Most recent embedding
        latest_embedding = db.query(Embedding).order_by(
            Embedding.created_at.desc()
        ).first()

        # Model usage
        model_counts = db.query(
            Embedding.model_name,
            func.count(Embedding.id)
        ).group_by(Embedding.model_name).all()

        stats = {
            "total_extractions": total_extractions,
            "total_embeddings": total_embeddings,
            "without_embeddings": without_embeddings,
            "completion_rate": (
                f"{(total_embeddings / total_extractions * 100):.1f}%"
                if total_extractions > 0 else "0%"
            ),
            "avg_dimensions": round(avg_dimensions, 0),
            "latest_embedding": (
                latest_embedding.created_at.isoformat()
                if latest_embedding else None
            ),
            "models_used": {
                model: count for model, count in model_counts
            }
        }

        logger.info(f"Embedding stats: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get embedding stats: {e}", exc_info=True)
        return {"error": str(e)}

    finally:
        db.close()


def mark_embedding_outdated(extraction_id: int) -> bool:
    """
    Mark an embedding as outdated (delete it).

    Useful when PDF extraction is reprocessed and embedding needs regeneration.

    Args:
        extraction_id: ID of the PDFExtraction

    Returns:
        True if embedding was deleted, False if not found
    """
    db: Session = next(get_db())

    try:
        embedding = db.query(Embedding).filter(
            Embedding.extraction_id == extraction_id
        ).first()

        if not embedding:
            return False

        db.delete(embedding)
        db.commit()

        logger.info(f"Deleted embedding for extraction_id={extraction_id}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to delete embedding for extraction_id={extraction_id}: {e}"
        )
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    # Test the embedder functions
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        # Get stats
        stats = get_embedding_stats()
        print("\n" + "=" * 60)
        print("EMBEDDING STATISTICS")
        print("=" * 60)
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
