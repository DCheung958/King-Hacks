"""
Database Migration Runner
Run this script to create/update database schema
"""

import asyncio
import asyncpg
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:Postgresql4Life!@localhost:5432/echocare_db"
)

# Parse connection string to get connection details
# Format: postgresql+asyncpg://user:password@host:port/database
def parse_database_url(url: str):
    """Parse database URL to extract connection parameters"""
    # Remove postgresql+asyncpg:// prefix
    url = url.replace("postgresql+asyncpg://", "")
    
    # Split user:password@host:port/database
    if "@" in url:
        auth, rest = url.split("@", 1)
        user, password = auth.split(":", 1)
    else:
        user, password = None, None
        rest = url
    
    if "/" in rest:
        host_port, database = rest.split("/", 1)
    else:
        host_port = rest
        database = None
    
    if ":" in host_port:
        host, port = host_port.split(":", 1)
        port = int(port)
    else:
        host = host_port
        port = 5432
    
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "database": database
    }


async def run_migrations():
    """Execute SQL migration file"""
    conn_params = parse_database_url(DATABASE_URL)
    
    # Connect to postgres database to create echocare_db if it doesn't exist
    postgres_db = conn_params["database"]
    try:
        conn = await asyncpg.connect(
            host=conn_params["host"],
            port=conn_params["port"],
            user=conn_params["user"],
            password=conn_params["password"],
            database="postgres"  # Connect to default postgres DB first
        )
        
        # Check if database exists
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            postgres_db
        )
        
        if not db_exists:
            print(f"Creating database '{postgres_db}'...")
            await conn.execute(f'CREATE DATABASE {postgres_db}')
            print(f"Database '{postgres_db}' created successfully!")
        
        await conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        print("Assuming database already exists, continuing...")
    
    # Now connect to the actual database
    conn = await asyncpg.connect(
        host=conn_params["host"],
        port=conn_params["port"],
        user=conn_params["user"],
        password=conn_params["password"],
        database=postgres_db
    )
    
    try:
        # Get all migration files in order
        migrations_dir = Path(__file__).parent / "migrations"
        if not migrations_dir.exists():
            print(f"Migrations directory not found: {migrations_dir}")
            return
        
        # Get all .sql files and sort them by filename (which should have numeric prefixes)
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        if not migration_files:
            print("No migration files found!")
            return
        
        print(f"Found {len(migration_files)} migration file(s)")
        
        # Run each migration in order
        for migration_file in migration_files:
            print(f"\nRunning migration: {migration_file.name}")
            migration_sql = migration_file.read_text()
            
            # Execute migration
            await conn.execute(migration_sql)
            print(f"✓ {migration_file.name} completed successfully!")
        
        print("\nAll migrations completed successfully!")
        
    except Exception as e:
        print(f"Error running migration: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    print("Running database migrations...")
    print(f"Database URL: {DATABASE_URL.replace(parse_database_url(DATABASE_URL)['password'], '***')}")
    asyncio.run(run_migrations())

