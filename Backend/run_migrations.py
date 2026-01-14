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
        # Read migration file
        migration_file = Path(__file__).parent / "migrations" / "001_initial_schema.sql"
        
        if not migration_file.exists():
            print(f"Migration file not found: {migration_file}")
            return
        
        print(f"Running migration: {migration_file}")
        migration_sql = migration_file.read_text()
        
        # Execute migration
        await conn.execute(migration_sql)
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error running migration: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    print("Running database migrations...")
    print(f"Database URL: {DATABASE_URL.replace(parse_database_url(DATABASE_URL)['password'], '***')}")
    asyncio.run(run_migrations())

