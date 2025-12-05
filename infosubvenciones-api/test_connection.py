from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Original DATABASE_URL: {DATABASE_URL}")

# If you need to encode the password, uncomment this section:
# password = "E:wyKn!W!xjht48"
# encoded_password = quote_plus(password)
# DATABASE_URL = f"postgresql://postgres:{encoded_password}@db.vtbvcabetythqrdedgee.supabase.co:5432/postgres"
# print(f"Encoded DATABASE_URL: {DATABASE_URL}")

try:
    import psycopg
    print("\nAttempting to connect to database...")

    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            # Test 1: Check PostgreSQL version
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"\n✓ Connected successfully!")
            print(f"PostgreSQL version: {version}")

            # Test 2: List existing tables
            cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname='public'
                ORDER BY tablename;
            """)
            tables = [r[0] for r in cur.fetchall()]
            print(f"\nExisting tables in 'public' schema: {tables if tables else '(none yet)'}")

            # Test 3: Check schemas
            cur.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                ORDER BY schema_name;
            """)
            schemas = [r[0] for r in cur.fetchall()]
            print(f"Available schemas: {schemas}")

            print("\n✓ All tests passed! Database is ready to use.")

except psycopg.OperationalError as e:
    print(f"\n✗ Connection failed: {e}")
    print("\nTroubleshooting tips:")
    print("1. Check if your Supabase URL is correct")
    print("2. Verify your password and ensure special characters are properly encoded")
    print("3. Make sure your IP is allowed in Supabase network settings")
    print("4. Check your internet connection")
except ImportError:
    print("✗ psycopg not installed. Run: pip install 'psycopg[binary]'")
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
