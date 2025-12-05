"""
Backfill titulo and pdf_url in convocatorias table from pdf_extractions and staging_items.

This script:
1. Updates convocatorias.titulo from pdf_extractions.titulo
2. Updates convocatorias.pdf_url from staging_items.pdf_url
3. Logs all updates for verification

Run with: python scripts/backfill_titulo_and_pdf_url.py
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from sqlalchemy.orm import Session
from loguru import logger
from config.database import get_db
from models.convocatoria import Convocatoria
from models.pdf_extraction import PDFExtraction
from models.staging import StagingItem

def backfill_titulo_and_pdf_url():
    """Backfill missing titulo and pdf_url fields in convocatorias table."""
    db: Session = next(get_db())

    try:
        # Get all convocatorias
        stmt = select(Convocatoria)
        convocatorias = db.execute(stmt).scalars().all()

        total = len(convocatorias)
        updated_titulo = 0
        updated_pdf_url = 0
        skipped = 0

        logger.info(f"Processing {total} convocatorias...")

        for conv in convocatorias:
            updated_this_record = False

            # Update titulo from pdf_extractions
            if not conv.titulo:
                stmt = select(PDFExtraction).where(
                    PDFExtraction.numero_convocatoria == conv.numero_convocatoria
                )
                extraction = db.execute(stmt).scalar_one_or_none()

                if extraction and extraction.titulo:
                    conv.titulo = extraction.titulo
                    updated_titulo += 1
                    updated_this_record = True
                    logger.info(f"Updated titulo for {conv.numero_convocatoria}: {extraction.titulo[:50]}...")

            # Update pdf_url from staging_items
            if not conv.pdf_url:
                stmt = select(StagingItem).where(
                    StagingItem.numero_convocatoria == conv.numero_convocatoria
                )
                staging = db.execute(stmt).scalar_one_or_none()

                if staging and staging.pdf_url:
                    conv.pdf_url = staging.pdf_url
                    updated_pdf_url += 1
                    updated_this_record = True
                    logger.info(f"Updated pdf_url for {conv.numero_convocatoria}")

            if not updated_this_record:
                skipped += 1

        # Commit all changes
        db.commit()

        logger.success(f"""
Backfill complete!
Total convocatorias: {total}
Updated titulo: {updated_titulo}
Updated pdf_url: {updated_pdf_url}
Skipped (already had data): {skipped}
        """)

        return {
            'success': True,
            'total': total,
            'updated_titulo': updated_titulo,
            'updated_pdf_url': updated_pdf_url,
            'skipped': skipped
        }

    except Exception as e:
        logger.error(f"Error during backfill: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting titulo and pdf_url backfill...")
    result = backfill_titulo_and_pdf_url()

    if result['success']:
        print(f"\n✅ Backfill successful!")
        print(f"   - {result['updated_titulo']} titulos updated")
        print(f"   - {result['updated_pdf_url']} pdf_urls updated")
        print(f"   - {result['skipped']} records skipped (already had data)")
    else:
        print(f"\n❌ Backfill failed")
