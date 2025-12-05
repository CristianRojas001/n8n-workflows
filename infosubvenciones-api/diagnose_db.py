from dotenv import load_dotenv
import os
import socket

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print("Database Connection Diagnostics")
print("=" * 50)
print(f"\nDATABASE_URL loaded: {DATABASE_URL[:50]}..." if DATABASE_URL else "DATABASE_URL not found!")

if DATABASE_URL:
    # Parse the connection string
    parts = DATABASE_URL.replace("postgresql://", "").split("@")
    if len(parts) == 2:
        credentials = parts[0]
        host_part = parts[1]

        username = credentials.split(":")[0]
        host = host_part.split(":")[0]
        port = host_part.split(":")[1].split("/")[0] if ":" in host_part else "5432"
        database = host_part.split("/")[1] if "/" in host_part else "postgres"

        print(f"\nParsed connection details:")
        print(f"  Host: {host}")
        print(f"  Port: {port}")
        print(f"  Database: {database}")
        print(f"  Username: {username}")

        # Test DNS resolution
        print(f"\nTesting DNS resolution for {host}...")
        try:
            ip_address = socket.gethostbyname(host)
            print(f"  SUCCESS: Resolved to {ip_address}")
        except socket.gaierror as e:
            print(f"  FAILED: {e}")
            print("\n  Possible issues:")
            print("    - The hostname might be incorrect")
            print("    - DNS server issue")
            print("    - Network connectivity problem")
            print("\n  Please verify the connection string in your Supabase dashboard:")
            print("    1. Go to Supabase project settings")
            print("    2. Click on 'Database'")
            print("    3. Copy the connection string from 'Connection string' section")
            exit(1)

        # Test port connectivity
        print(f"\nTesting port connectivity to {host}:{port}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, int(port)))
            sock.close()

            if result == 0:
                print(f"  SUCCESS: Port {port} is reachable")
            else:
                print(f"  FAILED: Cannot connect to port {port}")
                print("  Possible issues:")
                print("    - Firewall blocking the connection")
                print("    - Supabase IP restrictions")
                print("    - Wrong port number")
        except Exception as e:
            print(f"  ERROR: {e}")

        # Try database connection
        print("\nTesting database connection...")
        try:
            import psycopg

            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()[0]
                    print(f"  SUCCESS: Connected to database!")
                    print(f"  PostgreSQL version: {version[:80]}...")

                    # Check for existing tables
                    cur.execute("""
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname='public'
                        ORDER BY tablename;
                    """)
                    tables = [r[0] for r in cur.fetchall()]
                    print(f"\n  Tables in 'public' schema: {len(tables)}")
                    if tables:
                        for table in tables:
                            print(f"    - {table}")
                    else:
                        print("    (no tables yet - database is empty)")

                    print("\n" + "=" * 50)
                    print("Database connection is working perfectly!")
                    print("=" * 50)

        except ImportError:
            print("  ERROR: psycopg not installed")
            print("  Run: pip install 'psycopg[binary]'")
        except Exception as e:
            print(f"  FAILED: {e}")
            print("\n  This might be due to:")
            print("    - Incorrect password")
            print("    - IP not whitelisted in Supabase")
            print("    - Database credentials expired")
