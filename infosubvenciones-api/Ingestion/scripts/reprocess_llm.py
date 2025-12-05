"""
Reprocess a specific grant with the updated LLM extractor.

This script reprocesses grants that were processed with the old LLM code
to populate all the new fields (extracted_summary, titulo, organismo, etc.)
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from config.database import get_db
from models.pdf_extraction import PDFExtraction
from tasks.llm_processor import process_with_llm


def reprocess_grant(numero_convocatoria: str):
    """
    Reprocess a specific grant with updated LLM extractor.

    Args:
        numero_convocatoria: Grant number (e.g., "865923")
    """
    db = next(get_db())

    try:
        # Find the PDF extraction
        stmt = select(PDFExtraction).where(
            PDFExtraction.numero_convocatoria == numero_convocatoria
        )
        extraction = db.execute(stmt).scalar_one_or_none()

        if not extraction:
            print(f"❌ No PDF extraction found for grant {numero_convocatoria}")
            return False

        print(f"📄 Found extraction ID: {extraction.id}")
        print(f"   Current model: {extraction.extraction_model}")
        print(f"   Current summary: {'Yes' if extraction.extracted_summary else 'No (using old field)'}")
        print(f"   Current titulo: {extraction.titulo or 'NULL'}")
        print(f"   Current gastos_subvencionables: {extraction.gastos_subvencionables or 'NULL'}")

        # Force reprocessing by clearing the model
        print(f"\n🔄 Forcing reprocessing...")
        extraction.extraction_model = None  # This will trigger reprocessing
        db.commit()

        # Run LLM processor
        print(f"🤖 Running LLM processor...")
        result = process_with_llm.run(extraction.id)

        if result.get('success'):
            print(f"\n✅ Reprocessing successful!")
            print(f"   Summary length: {result.get('summary_length', 0)} chars")
            print(f"   Fields extracted: {result.get('fields_extracted', 0)}")
            print(f"   Confidence: {result.get('confidence', 0):.2f}")
            print(f"   Fields: {', '.join(result.get('fields', []))}")

            # Refresh to see updated data
            db.refresh(extraction)

            print(f"\n📊 Updated fields:")
            print(f"   titulo: {extraction.titulo or 'NULL'}")
            print(f"   organismo: {extraction.organismo or 'NULL'}")
            print(f"   ambito_geografico: {extraction.ambito_geografico or 'NULL'}")
            print(f"   gastos_subvencionables: {extraction.gastos_subvencionables[:100] if extraction.gastos_subvencionables else 'NULL'}...")
            print(f"   cuantia_subvencion: {extraction.cuantia_subvencion or 'NULL'}")
            print(f"   plazo_ejecucion: {extraction.plazo_ejecucion or 'NULL'}")
            print(f"   forma_pago: {extraction.forma_pago or 'NULL'}")
            print(f"   extracted_summary: {len(extraction.extracted_summary)} chars" if extraction.extracted_summary else "NULL")

            return True
        else:
            print(f"❌ Reprocessing failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/reprocess_llm.py <numero_convocatoria>")
        print("Example: python scripts/reprocess_llm.py 865923")
        sys.exit(1)

    numero = sys.argv[1]
    success = reprocess_grant(numero)
    sys.exit(0 if success else 1)
