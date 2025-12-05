"""Backfill pdf_url and pdf_hash in staging_items from convocatorias."""
import sys
from pathlib import Path
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from loguru import logger

from config.database import get_db
from models.staging import StagingItem
from models.convocatoria import Convocatoria


def extract_pdf_url_from_documentos(documentos):
    """Extract PDF URL from documentos JSONB field."""
    if not documentos or not isinstance(documentos, list):
        return None

    for doc in documentos:
        if not isinstance(doc, dict):
            continue

        url = doc.get('urlDocumento') or doc.get('url_documento')
        if url and ('.pdf' in url.lower() or 'pdf' in url.lower()):
            return url

    return None


def hash_url(url):
    """Generate SHA256 hash of URL."""
    if not url:
        return None
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def backfill():
    """Backfill pdf_url and pdf_hash in staging_items."""
    logger.info("Starting backfill: Add PDF URLs to staging_items")

    db = next(get_db())

    try:
        # Get all staging items
        stmt = select(StagingItem)
        staging_items = db.execute(stmt).scalars().all()

        logger.info(f"Found {len(staging_items)} staging items")

        updated_count = 0
        no_pdf_count = 0

        for staging_item in staging_items:
            # Get corresponding convocatoria
            stmt = select(Convocatoria).where(
                Convocatoria.numero_convocatoria == staging_item.numero_convocatoria
            )
            convocatoria = db.execute(stmt).scalar_one_or_none()

            if not convocatoria:
                logger.warning(
                    f"No convocatoria found for staging item: {staging_item.numero_convocatoria}"
                )
                continue

            # Extract PDF URL from documentos
            pdf_url = extract_pdf_url_from_documentos(convocatoria.documentos)

            if pdf_url:
                pdf_hash = hash_url(pdf_url)
                staging_item.pdf_url = pdf_url
                staging_item.pdf_hash = pdf_hash
                updated_count += 1

                if updated_count % 10 == 0:
                    logger.info(f"Updated {updated_count} items...")
            else:
                no_pdf_count += 1

        # Commit changes
        db.commit()

        logger.success(f"Backfill completed!")
        logger.info(f"Updated {updated_count} staging items with PDF URLs")
        logger.info(f"{no_pdf_count} items have no PDF")

    except Exception as e:
        logger.error(f"Backfill failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    backfill()