"""
Export Database Statistics

This script connects to the database and exports high-level statistics about
the data ingestion process. It reports on:
- Total convocatorias in the main table.
- Total items in the staging table.
- A breakdown of staging items by their processing status.

Usage:
    python scripts/export_stats.py
"""
import sys
import os
from collections import Counter

# Add parent directory to path to allow sibling imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import get_db
from models.convocatoria import Convocatoria
from models.staging import StagingItem, ProcessingStatus

def export_statistics():
    """
    Connects to the database and prints out ingestion statistics.
    """
    print("=" * 50)
    print("Exporting Database Statistics")
    print("=" * 50)

    db = next(get_db())

    try:
        # 1. Count total convocatorias
        total_convocatorias = db.query(Convocatoria).count()
        print(f"\n[+] Convocatorias Table:")
        print(f"  - Total records: {total_convocatorias}")

        # 2. Count total staging items
        total_staging_items = db.query(StagingItem).count()
        print(f"\n[+] Staging Items Table:")
        print(f"  - Total records: {total_staging_items}")

        # 3. Get status breakdown for staging items
        if total_staging_items > 0:
            print("\n  Status Breakdown:")
            
            # Query all statuses
            all_statuses = [item.status for item in db.query(StagingItem.status).all()]
            
            # Count occurrences of each status
            status_counts = Counter(all_statuses)

            # Get all possible enum values
            possible_statuses = [status for status in ProcessingStatus]
            
            # Print counts for each possible status
            for status in possible_statuses:
                count = status_counts.get(status, 0)
                percentage = (count / total_staging_items) * 100 if total_staging_items > 0 else 0
                print(f"  - {status.value:<15}: {count:>6} records ({percentage:.2f}%)")
        
        print("\n" + "=" * 50)
        print("Statistics export complete.")

    except Exception as e:
        print(f"\n[ERROR] An error occurred while connecting to the database.")
        print(f"  - Details: {e}")
        print("  - Please ensure the DATABASE_URL in your .env file is correct and PostgreSQL is running.")
    finally:
        db.close()

if __name__ == "__main__":
    export_statistics()
