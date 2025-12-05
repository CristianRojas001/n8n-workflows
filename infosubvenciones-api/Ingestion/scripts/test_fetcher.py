"""
Test script for the fetcher task.

This script tests the Celery fetcher task by:
1. Starting a test fetch with 10-100 items
2. Monitoring task progress
3. Verifying data was inserted into staging_items and convocatorias tables

Usage:
    # Test with 10 items (quick test)
    python scripts/test_fetcher.py --items 10

    # Test with 100 items (full test)
    python scripts/test_fetcher.py --items 100

    # Test without Celery worker (direct call)
    python scripts/test_fetcher.py --items 10 --direct
"""

import sys
import os
import argparse
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import get_db
from models.staging import StagingItem
from models.convocatoria import Convocatoria
from tasks.fetcher import fetch_convocatorias


def check_database_tables():
    """Check if database tables exist and are accessible."""
    print("\n=== Checking Database Tables ===")
    db = next(get_db())

    try:
        # Check staging_items table
        staging_count = db.query(StagingItem).count()
        print(f"✓ staging_items table exists ({staging_count} rows)")

        # Check convocatorias table
        conv_count = db.query(Convocatoria).count()
        print(f"✓ convocatorias table exists ({conv_count} rows)")

        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False
    finally:
        db.close()


def test_direct_fetch(num_items: int, finalidad: str = "11"):
    """
    Test fetcher by calling it directly (without Celery worker).

    This is useful for debugging and quick testing.
    """
    print(f"\n=== Testing Direct Fetch ({num_items} items) ===")

    batch_id = f"test_direct_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Batch ID: {batch_id}")
    print(f"Finalidad: {finalidad} (culture grants)")

    # Call task directly (not through Celery)
    result = fetch_convocatorias(
        finalidad=finalidad,
        batch_id=batch_id,
        page=0,
        size=num_items,
        max_items=num_items
    )

    print("\n=== Results ===")
    print(f"Fetched: {result['fetched']}")
    print(f"Inserted: {result['inserted']}")
    print(f"Duplicates: {result['duplicates']}")
    print(f"Errors: {result['errors']}")

    return result


def test_celery_task(num_items: int, finalidad: str = "11"):
    """
    Test fetcher through Celery worker.

    This requires a Celery worker to be running:
        celery -A config.celery_app worker --loglevel=info -Q fetcher
    """
    print(f"\n=== Testing Celery Task ({num_items} items) ===")

    batch_id = f"test_celery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Batch ID: {batch_id}")
    print(f"Finalidad: {finalidad} (culture grants)")

    # Trigger Celery task
    print("\nTriggering Celery task...")
    task = fetch_convocatorias.delay(
        finalidad=finalidad,
        batch_id=batch_id,
        page=0,
        size=num_items,
        max_items=num_items
    )

    print(f"Task ID: {task.id}")
    print("Waiting for task to complete...")

    # Wait for task with timeout
    timeout = 120  # 2 minutes
    start_time = time.time()

    while not task.ready():
        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"\n✗ Task timed out after {timeout} seconds")
            print("  Check if Celery worker is running:")
            print("  celery -A config.celery_app worker --loglevel=info -Q fetcher")
            return None

        print(f"  Waiting... ({int(elapsed)}s)", end='\r')
        time.sleep(2)

    # Get result
    print("\n\nTask completed!")
    result = task.result

    print("\n=== Results ===")
    print(f"Fetched: {result['fetched']}")
    print(f"Inserted: {result['inserted']}")
    print(f"Duplicates: {result['duplicates']}")
    print(f"Errors: {result['errors']}")

    return result


def verify_database(batch_id: str):
    """Verify data was inserted into database tables."""
    print("\n=== Verifying Database ===")
    db = next(get_db())

    try:
        # Check staging_items for this batch
        staging_items = db.query(StagingItem).filter_by(batch_id=batch_id).all()
        print(f"\nStaging Items (batch={batch_id}):")
        print(f"  Total: {len(staging_items)}")

        status_counts = {}
        for item in staging_items:
            status = item.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            print(f"  {status}: {count}")

        # Show sample items
        print("\nSample staging items:")
        for item in staging_items[:3]:
            print(f"  - {item.numero_convocatoria} | {item.status.value}")

        # Check convocatorias table
        print("\nConvocatorias:")
        total_conv = db.query(Convocatoria).count()
        print(f"  Total in database: {total_conv}")

        # Get convocatorias for staging items in this batch
        numeros = [item.numero_convocatoria for item in staging_items]
        batch_conv = db.query(Convocatoria).filter(
            Convocatoria.numero_convocatoria.in_(numeros)
        ).all()

        print(f"  From this batch: {len(batch_conv)}")

        # Show sample convocatorias
        print("\nSample convocatorias:")
        for conv in batch_conv[:3]:
            title = conv.titulo[:60] if conv.titulo else 'N/A'
            pdf_status = "✓ PDF" if conv.tiene_pdf else "✗ No PDF"
            print(f"  - {conv.numero_convocatoria}")
            print(f"    {title}")
            print(f"    {pdf_status} | {conv.organismo}")

        return len(staging_items), len(batch_conv)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Test the fetcher task')
    parser.add_argument('--items', type=int, default=10, help='Number of items to fetch (default: 10)')
    parser.add_argument('--finalidad', type=str, default='11', help='Finalidad code (default: 11 for culture)')
    parser.add_argument('--direct', action='store_true', help='Call task directly without Celery worker')

    args = parser.parse_args()

    print("=" * 70)
    print("FETCHER TASK TEST")
    print("=" * 70)

    # Check database
    if not check_database_tables():
        print("\n✗ Database check failed. Make sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database is initialized (run scripts/init_db.py)")
        print("  3. .env file has correct DATABASE_URL")
        return

    # Run test
    try:
        if args.direct:
            result = test_direct_fetch(args.items, args.finalidad)
            if result:
                batch_id = result['batch_id']
        else:
            result = test_celery_task(args.items, args.finalidad)
            if result:
                batch_id = result['batch_id']
            else:
                return

        # Verify database
        if result:
            staging_count, conv_count = verify_database(batch_id)

            print("\n" + "=" * 70)
            print("TEST SUMMARY")
            print("=" * 70)
            print(f"✓ Fetched {result['fetched']} items from API")
            print(f"✓ Inserted {result['inserted']} new items")
            print(f"✓ Found {result['duplicates']} duplicates")
            if result['errors'] > 0:
                print(f"✗ Encountered {result['errors']} errors")
            print(f"✓ Verified {staging_count} staging items in database")
            print(f"✓ Verified {conv_count} convocatorias in database")
            print("\nTest completed successfully!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
