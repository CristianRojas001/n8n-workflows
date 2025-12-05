"""Test Supabase connection and verify pgvector extension."""
import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from parent Ingestion folder
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

def test_connection():
    """Test database connection and pgvector availability."""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("❌ DATABASE_URL not found in .env file")
        return False

    print(f"🔗 Connecting to Supabase...")
    print(f"   Connection string: {database_url[:50]}...")

    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Test 1: Basic connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL")
        print(f"   Version: {version[:80]}...")

        # Test 2: Check pgvector extension
        cursor.execute("""
            SELECT * FROM pg_available_extensions
            WHERE name = 'vector';
        """)
        result = cursor.fetchone()

        if result:
            print(f"✅ pgvector extension available")
            print(f"   Version: {result[1] if result[1] else 'Not installed yet'}")
        else:
            print(f"❌ pgvector extension NOT available")
            return False

        # Test 3: Check if pgvector is enabled
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        is_enabled = cursor.fetchone()[0]

        if is_enabled:
            print(f"✅ pgvector extension is ENABLED")
        else:
            print(f"⚠️  pgvector extension available but NOT enabled")
            print(f"   Run this in Supabase SQL Editor:")
            print(f"   CREATE EXTENSION IF NOT EXISTS vector;")

        # Test 4: Check current database
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"✅ Current database: {db_name}")

        # Test 5: Check schema permissions
        cursor.execute("""
            SELECT has_schema_privilege('public', 'CREATE');
        """)
        can_create = cursor.fetchone()[0]

        if can_create:
            print(f"✅ Can create tables in 'public' schema")
        else:
            print(f"❌ Cannot create tables in 'public' schema")
            return False

        cursor.close()
        conn.close()

        print(f"\n✅ All connection tests passed!")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
