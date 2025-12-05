"""Test database schema and basic CRUD operations."""
import os
import sys
from pathlib import Path
from datetime import datetime, date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import text
from config.database import engine, get_db_session
from models import StagingItem, Convocatoria, PDFExtraction, Embedding


def test_staging_item():
    """Test StagingItem model."""
    print("\n🧪 Testing StagingItem model...")

    with get_db_session() as session:
        # Create test item
        item = StagingItem(
            numero_convocatoria="TEST001",
            batch_id="test_batch_1"
        )
        session.add(item)
        session.commit()
        print(f"✅ Created: {item}")

        # Query item
        retrieved = session.query(StagingItem).filter_by(numero_convocatoria="TEST001").first()
        print(f"✅ Retrieved: {retrieved}")

        # Update item
        retrieved.mark_processing("fetcher")
        session.commit()
        print(f"✅ Updated status to: {retrieved.status.value}")

        # Delete item
        session.delete(retrieved)
        session.commit()
        print("✅ Deleted test item")


def test_convocatoria():
    """Test Convocatoria model."""
    print("\n🧪 Testing Convocatoria model...")

    with get_db_session() as session:
        # Create test convocatoria
        conv = Convocatoria(
            numero_convocatoria="TEST002",
            titulo="Test Grant for Culture",
            descripcion="This is a test grant",
            organismo="Ministerio de Cultura",
            finalidad="11",
            sectores=["cultura", "patrimonio"],
            regiones=["madrid", "barcelona"],
            abierto=True,
            fecha_publicacion=date(2025, 1, 1),
            fecha_fin_solicitud=date(2025, 12, 31),
            importe_total="100000 EUR",
            documentos=[{"id": "1", "nombre": "test.pdf"}],
            tiene_pdf=True
        )
        session.add(conv)
        session.commit()
        print(f"✅ Created: {conv}")

        # Query convocatoria
        retrieved = session.query(Convocatoria).filter_by(numero_convocatoria="TEST002").first()
        print(f"✅ Retrieved: {retrieved}")
        print(f"   Sectors: {retrieved.sectores}")
        print(f"   Regions: {retrieved.regiones}")
        print(f"   Open: {retrieved.is_open}")

        # Delete test data
        session.delete(retrieved)
        session.commit()
        print("✅ Deleted test convocatoria")


def test_pdf_extraction():
    """Test PDFExtraction model."""
    print("\n🧪 Testing PDFExtraction model...")

    with get_db_session() as session:
        # First create a convocatoria
        conv = Convocatoria(
            numero_convocatoria="TEST003",
            titulo="Test Grant for PDF Extraction"
        )
        session.add(conv)
        session.commit()

        # Create PDF extraction
        pdf_ext = PDFExtraction(
            convocatoria_id=conv.id,
            numero_convocatoria=conv.numero_convocatoria,
            gastos_subvencionables="Personnel costs, equipment",
            cuantia_subvencion="50000 EUR",
            plazo_ejecucion="12 months",
            forma_justificacion="Audit report required",
            extraction_model="gemini-2.0-flash"
        )
        session.add(pdf_ext)
        session.commit()
        print(f"✅ Created: {pdf_ext}")

        # Query PDF extraction
        retrieved = session.query(PDFExtraction).filter_by(numero_convocatoria="TEST003").first()
        print(f"✅ Retrieved: {retrieved}")
        print(f"   Has financial details: {retrieved.has_financial_details}")
        print(f"   Has deadlines: {retrieved.has_deadlines}")

        # Cleanup
        session.delete(pdf_ext)
        session.delete(conv)
        session.commit()
        print("✅ Deleted test data")


def test_embedding():
    """Test Embedding model with pgvector."""
    print("\n🧪 Testing Embedding model (with pgvector)...")

    with get_db_session() as session:
        # First create a convocatoria
        conv = Convocatoria(
            numero_convocatoria="TEST004",
            titulo="Test Grant for Embeddings"
        )
        session.add(conv)
        session.commit()

        # Create embedding with test vector
        # Note: In production, this would be a real 1536-dim vector from OpenAI
        test_vector = [0.1] * 1536  # Simple test vector

        emb = Embedding(
            convocatoria_id=conv.id,
            numero_convocatoria=conv.numero_convocatoria,
            summary_text="This is a test summary of about 200 words. " * 20,
            summary_word_count=200,
            embedding=test_vector,
            embedding_model="text-embedding-3-small",
            search_metadata={"sector": "cultura", "finalidad": "11"}
        )
        session.add(emb)
        session.commit()
        print(f"✅ Created: {emb}")

        # Query embedding
        retrieved = session.query(Embedding).filter_by(numero_convocatoria="TEST004").first()
        print(f"✅ Retrieved: {retrieved}")
        print(f"   Summary preview: {retrieved.summary_preview}")
        print(f"   Is valid summary: {retrieved.is_valid_summary}")
        print(f"   Embedding dimensions: {len(retrieved.embedding) if retrieved.embedding is not None else 0}")

        # Test vector similarity search
        print("\n🔍 Testing vector similarity search...")
        query_vector = [0.1] * 1536  # Same as test vector
        vector_str = "[" + ",".join(map(str, query_vector)) + "]"
        result = session.execute(text(f"""
            SELECT numero_convocatoria,
                   1 - (embedding <=> '{vector_str}'::vector) as similarity
            FROM embeddings
            WHERE numero_convocatoria = 'TEST004'
            ORDER BY embedding <=> '{vector_str}'::vector
            LIMIT 1;
        """))

        for row in result:
            print(f"✅ Similarity search works! Similarity: {row[1]:.4f}")

        # Cleanup
        session.delete(emb)
        session.delete(conv)
        session.commit()
        print("✅ Deleted test data")


def test_relationships():
    """Test relationships between tables."""
    print("\n🧪 Testing table relationships...")

    with get_db_session() as session:
        # Create convocatoria
        conv = Convocatoria(
            numero_convocatoria="TEST005",
            titulo="Test Grant for Relationships"
        )
        session.add(conv)
        session.flush()  # Get ID without committing

        # Create related PDF extraction and embedding
        pdf_ext = PDFExtraction(
            convocatoria_id=conv.id,
            numero_convocatoria=conv.numero_convocatoria,
            gastos_subvencionables="Test expenses"
        )

        emb = Embedding(
            convocatoria_id=conv.id,
            numero_convocatoria=conv.numero_convocatoria,
            summary_text="Test summary " * 30,
            summary_word_count=200,
            embedding=[0.1] * 1536
        )

        session.add_all([pdf_ext, emb])
        session.commit()

        print(f"✅ Created convocatoria with ID: {conv.id}")
        print(f"✅ Created related PDF extraction with ID: {pdf_ext.id}")
        print(f"✅ Created related embedding with ID: {emb.id}")

        # Test cascade delete
        session.delete(conv)
        session.commit()

        # Verify cascade worked
        pdf_count = session.query(PDFExtraction).filter_by(numero_convocatoria="TEST005").count()
        emb_count = session.query(Embedding).filter_by(numero_convocatoria="TEST005").count()

        if pdf_count == 0 and emb_count == 0:
            print("✅ Cascade delete works! Related records deleted automatically")
        else:
            print(f"❌ Cascade delete failed. PDF count: {pdf_count}, Embedding count: {emb_count}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Schema Tests")
    print("=" * 60)

    try:
        test_staging_item()
        test_convocatoria()
        test_pdf_extraction()
        test_embedding()
        test_relationships()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
