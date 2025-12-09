"""
End-to-end pipeline test for local PDF files.

This script tests the complete ingestion pipeline for a list of local PDFs.
"""

import sys
import os
import time
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func
from config.database import get_db
from models.staging import StagingItem, ProcessingStatus
from models.convocatoria import Convocatoria
from models.pdf_extraction import PDFExtraction
from models.embedding import Embedding

# Import tasks

from tasks.pdf_processor import process_pdf
from tasks.llm_processor import process_with_llm
from tasks.embedder import generate_embedding


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

def test_local_pipeline(pdf_files: list[str]):
    """
    Test the full pipeline end-to-end with local PDF files.

    Args:
        pdf_files: A list of absolute paths to PDF files.
    """
    print_section(f"LOCAL PIPELINE TEST - {len(pdf_files)} FILES")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    db = next(get_db())
    start_time = time.time()
    batch_id = f"test_local_pipeline_{int(time.time())}"

    try:
        # STAGE 0: Get baseline stats
        print_section("STAGE 0: Baseline Statistics")
        baseline_stats = get_pipeline_stats(db)
        print_stats(baseline_stats, "Pipeline State (Before)")

        # STAGE 1: Create StagingItems for local PDFs
        print_section("STAGE 1: Creating Staging Items for Local PDFs")
        staging_items = []
        for pdf_path in pdf_files:
            file_name = os.path.basename(pdf_path)
            numero_convocatoria = file_name.split('_')[0]
            
            # Check if a StagingItem for this numero_convocatoria already exists
            existing_item = db.query(StagingItem).filter(StagingItem.pdf_url == pdf_path).first()
            if existing_item:
                print(f"  - Skipping, staging item for {file_name} already exists.")
                staging_items.append(existing_item)
                continue

            item = StagingItem(
                batch_id=batch_id,
                numero_convocatoria=numero_convocatoria,
                link=f"local-file://{pdf_path}",
                pdf_url=pdf_path,
                titulo=f"Local Test: {file_name}",
                organismo="Local Test",
                fecha_publicacion=datetime.now(),
                status=ProcessingStatus.PENDING,
                notes=f"Local file: {file_name}"
            )
            staging_items.append(item)
            db.add(item)
        
        db.commit()
        print(f"  - Created {len(staging_items)} new staging items with batch_id: {batch_id}")

        time.sleep(2)  # Brief pause

        # STAGE 2: Process PDFs
        print_section("STAGE 2: Processing PDFs")
        pdf_results = []
        for item in staging_items:
            print(f"  Processing PDF for staging_id={item.id}...")
            result = process_pdf(item.id)
            pdf_results.append(result)

            if result.get('status') == 'success':
                print(f"    ✅ Success")
            else:
                print(f"    ⚠️ {result.get('status')}: {result.get('reason', 'N/A')}")

        time.sleep(2)

        # STAGE 3: LLM Processing
        print_section("STAGE 3: LLM Processing (Gemini)")
        llm_results = []
        extractions_to_process = db.query(PDFExtraction).filter(
            PDFExtraction.staging_id.in_([item.id for item in staging_items]),
        ).all()
        for extraction in extractions_to_process:
            print(f"  Processing extraction_id={extraction.id} with LLM...")
            result = process_with_llm(extraction.id)
            llm_results.append(result)

            if result.get('status') == 'success':
                print(f"    ✅ Success (confidence: {result.get('confidence', 0):.2f})")
            else:
                print(f"    ⚠️ {result.get('status')}")

        time.sleep(2)

        # STAGE 4: Generate Embeddings
        print_section("STAGE 4: Generating Embeddings")
        embedding_results = []
        extractions_without_embeddings = db.query(PDFExtraction).outerjoin(
            Embedding
        ).filter(
            PDFExtraction.staging_id.in_([item.id for item in staging_items]),
            Embedding.id.is_(None),
            PDFExtraction.extracted_text.isnot(None)
        ).all()

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

        # Summary
        elapsed = time.time() - start_time
        print_section("TEST SUMMARY")
        print(f"✅ Pipeline test completed successfully!")
        print(f"   Total time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        print(f"   Items processed: {len(pdf_files)}")
        print(f"   Average time per item: {elapsed/len(pdf_files):.2f} seconds")

        return True

    except Exception as e:
        print(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

def read_pdf_selection(file_path: str) -> list[str]:
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Extract file names, which are wrapped in backticks
    pdf_files = [line.strip().replace('`', '') for line in lines if line.strip().startswith('`')]
    
    # Construct absolute paths
    base_path = 'd:\\IT workspace\\relevant_pdfs'
    return [os.path.join(base_path, fname) for fname in pdf_files]

if __name__ == "__main__":
    
    selection_file = 'd:\\IT workspace\\infosubvenciones-api\\docs\\holistic_testing\\ground_truth\\selection.md'
    pdf_files = read_pdf_selection(selection_file)
    
    success = test_local_pipeline(pdf_files)

    sys.exit(0 if success else 1)
