"""
End-to-end pipeline test: Fetcher → PDF Processor → LLM → Embedder

Tests the complete ingestion pipeline with a configurable number of items.
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func
from config.database import get_db
from models.staging import StagingItem, ProcessingStatus
from models.convocatoria import Convocatoria
from models.pdf_extraction import PDFExtraction
from models.embedding import Embedding

# Import tasks
from tasks.fetcher import fetch_convocatorias
from tasks.pdf_processor import process_pdf_batch, get_pdf_processing_stats
from tasks.llm_processor import process_llm_batch, get_llm_processing_stats
from tasks.embedder import generate_batch_embeddings, get_embedding_stats


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_stats(stats: dict, title: str):
    """Print statistics in a formatted way."""
    print(f"\n{title}:")
    print("-" * 60)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print("-" * 60)


def get_pipeline_stats(db):
    """Get overall pipeline statistics."""
    total_staging = db.query(func.count(StagingItem.id)).scalar() or 0
    total_convocatorias = db.query(func.count(Convocatoria.id)).scalar() or 0
    total_extractions = db.query(func.count(PDFExtraction.id)).scalar() or 0
    total_embeddings = db.query(func.count(Embedding.id)).scalar() or 0

    # Status breakdown
    status_counts = {}
    for status in ProcessingStatus:
        count = db.query(func.count(StagingItem.id)).filter(
            StagingItem.status == status
        ).scalar() or 0
        status_counts[status.value] = count

    return {
        "total_staging_items": total_staging,
        "total_convocatorias": total_convocatorias,
        "total_pdf_extractions": total_extractions,
        "total_embeddings": total_embeddings,
        "staging_status": status_counts,
    }


def test_full_pipeline(num_items: int = 10, finalidad: str = "11", page: int = 0):
    """
    Test the full pipeline end-to-end.

    Args:
        num_items: Number of items to process
        finalidad: Finalidad code (default "11" for culture)
    """
    print_section(f"FULL PIPELINE TEST - {num_items} ITEMS")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finalidad: {finalidad} (Culture grants)")

    db = next(get_db())
    start_time = time.time()

    try:
        # STAGE 0: Get baseline stats
        print_section("STAGE 0: Baseline Statistics")
        baseline_stats = get_pipeline_stats(db)
        print_stats(baseline_stats, "Pipeline State (Before)")

        # STAGE 1: Fetch grants from API
        print_section("STAGE 1: Fetching Grants from API")
        print(f"Fetching {num_items} OPEN grants with finalidad={finalidad}, page={page}...")

        batch_id = f"test_full_pipeline_{int(time.time())}"
        fetch_size = min(max(num_items, 1), 100)
        result = fetch_convocatorias.run(
            finalidad=finalidad,
            batch_id=batch_id,
            page=page,
            size=fetch_size,
            max_items=num_items,
            abierto=True  # Only fetch open grants
        )

        print(f"✅ Fetch complete!")
        print(f"   Status: {result.get('status')}")
        print(f"   Fetched: {result.get('items_fetched', 0)} items")
        print(f"   Duplicates: {result.get('duplicates_skipped', 0)}")
        print(f"   Batch ID: {batch_id}")

        time.sleep(2)  # Brief pause

        # STAGE 2: Process PDFs
        print_section("STAGE 2: Processing PDFs")
        print(f"Processing PDFs for batch {batch_id}...")

        # Get pending staging items from this batch
        pending_items = db.query(StagingItem).filter(
            StagingItem.batch_id == batch_id,
            StagingItem.status == ProcessingStatus.PENDING,
            StagingItem.pdf_url.isnot(None)
        ).all()

        print(f"Found {len(pending_items)} items with PDFs to process")

        if pending_items:
            # Process PDFs directly (for testing, not via Celery)
            from tasks.pdf_processor import process_pdf

            pdf_results = []
            for item in pending_items:
                print(f"  Processing PDF for staging_id={item.id}...")
                result = process_pdf(item.id)
                pdf_results.append(result)

                if result.get('status') == 'success':
                    print(f"    ✅ Success")
                else:
                    print(f"    ⚠️ {result.get('status')}: {result.get('reason', 'N/A')}")

            # Get PDF processing stats
            pdf_stats = get_pdf_processing_stats()
            print_stats(pdf_stats, "PDF Processing Statistics")
        else:
            print("⚠️ No items with PDFs found in this batch")

        time.sleep(2)

        # STAGE 3: LLM Processing
        print_section("STAGE 3: LLM Processing (Gemini)")
        print("Processing PDFs with LLM to extract structured data...")

        # Get extractions without LLM processing
        extractions_to_process = db.query(PDFExtraction).filter(
            PDFExtraction.staging_id.in_([item.id for item in pending_items]),
            PDFExtraction.extracted_summary.is_(None)  # Not yet processed by LLM
        ).all()

        print(f"Found {len(extractions_to_process)} extractions to process with LLM")

        if extractions_to_process:
            from tasks.llm_processor import process_with_llm

            llm_results = []
            for extraction in extractions_to_process:
                print(f"  Processing extraction_id={extraction.id} with LLM...")
                result = process_with_llm(extraction.id)
                llm_results.append(result)

                if result.get('status') == 'success':
                    print(f"    ✅ Success (confidence: {result.get('confidence', 0):.2f})")
                else:
                    print(f"    ⚠️ {result.get('status')}")

            # Get LLM processing stats
            llm_stats = get_llm_processing_stats()
            print_stats(llm_stats, "LLM Processing Statistics")
        else:
            print("⚠️ No extractions found for LLM processing")

        time.sleep(2)

        # STAGE 4: Generate Embeddings
        print_section("STAGE 4: Generating Embeddings")
        print("Generating vector embeddings for semantic search...")

        # Get extractions without embeddings
        extractions_without_embeddings = db.query(PDFExtraction).outerjoin(
            Embedding
        ).filter(
            PDFExtraction.staging_id.in_([item.id for item in pending_items]),
            Embedding.id.is_(None),
            PDFExtraction.extracted_text.isnot(None)
        ).all()

        print(f"Found {len(extractions_without_embeddings)} extractions without embeddings")

        if extractions_without_embeddings:
            from tasks.embedder import generate_embedding

            embedding_results = []
            for extraction in extractions_without_embeddings:
                print(f"  Generating embedding for extraction_id={extraction.id}...")
                result = generate_embedding(extraction.id)
                embedding_results.append(result)

                if result.get('status') == 'success':
                    print(f"    ✅ Success (dimensions: {result.get('dimensions', 0)})")
                elif result.get('status') == 'skipped':
                    print(f"    ⏭️ Skipped: {result.get('reason', 'N/A')}")
                else:
                    print(f"    ⚠️ Failed: {result.get('error', 'Unknown')}")

                # Rate limiting: 4 seconds between embeddings
                if extraction != extractions_without_embeddings[-1]:
                    time.sleep(4)

            # Get embedding stats
            embedding_stats = get_embedding_stats()
            print_stats(embedding_stats, "Embedding Statistics")
        else:
            print("⚠️ No extractions found for embedding generation")

        # STAGE 5: Final Statistics
        print_section("STAGE 5: Final Pipeline Statistics")
        final_stats = get_pipeline_stats(db)
        print_stats(final_stats, "Pipeline State (After)")

        # Calculate deltas
        print("\n📊 Changes During Test:")
        print("-" * 60)
        print(f"  New staging items: +{final_stats['total_staging_items'] - baseline_stats['total_staging_items']}")
        print(f"  New convocatorias: +{final_stats['total_convocatorias'] - baseline_stats['total_convocatorias']}")
        print(f"  New PDF extractions: +{final_stats['total_pdf_extractions'] - baseline_stats['total_pdf_extractions']}")
        print(f"  New embeddings: +{final_stats['total_embeddings'] - baseline_stats['total_embeddings']}")

        # Test vector search
        print_section("STAGE 6: Testing Vector Search")
        test_vector_search(db)

        # Summary
        elapsed = time.time() - start_time
        print_section("TEST SUMMARY")
        print(f"✅ Pipeline test completed successfully!")
        print(f"   Total time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        print(f"   Items processed: {num_items}")
        print(f"   Average time per item: {elapsed/num_items:.2f} seconds")

        return True

    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


def test_vector_search(db):
    """Test vector search functionality."""
    print("Testing semantic search with query: 'proyectos culturales'")

    try:
        from services.vector_search import VectorSearcher

        searcher = VectorSearcher(db_session=db)

        # Get search stats
        stats = searcher.get_search_stats()
        print(f"\n  Search system ready: {stats.get('search_ready', False)}")
        print(f"  Total embeddings: {stats.get('total_embeddings', 0)}")
        print(f"  HNSW index: {stats.get('hnsw_index_exists', False)}")

        if stats.get('search_ready'):
            results = searcher.search(
                query="proyectos culturales en Madrid",
                limit=3,
                min_similarity=0.0
            )

            print(f"\n  Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                titulo = result.get('titulo') or 'N/A'
                organismo = result.get('organismo') or 'N/A'
                print(f"\n  {i}. {titulo[:60]}...")
                print(f"     Similarity: {result.get('similarity', 0):.4f}")
                print(f"     Organismo: {organismo[:50]}")
        else:
            print("\n  ⚠️ Search not ready yet (need embeddings and HNSW index)")

    except Exception as e:
        print(f"\n  ⚠️ Vector search test failed: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test full ingestion pipeline")
    parser.add_argument(
        "--items",
        type=int,
        default=10,
        help="Number of items to process (default: 10)"
    )
    parser.add_argument(
        "--finalidad",
        type=str,
        default="11",
        help="Finalidad code (default: 11 for culture)"
    )
    parser.add_argument(
        "--page",
        type=int,
        default=0,
        help="Starting page for fetcher pagination (default: 0)"
    )

    args = parser.parse_args()

    success = test_full_pipeline(
        num_items=args.items,
        finalidad=args.finalidad,
        page=args.page
    )

    sys.exit(0 if success else 1)
