"""
Run migration to add password field to users table
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:Postgresql4Life!@localhost:5432/echocare_db"
)


def parse_database_url(url: str):
    """Parse database URL"""
    # Remove postgresql+asyncpg:// prefix
    url = url.replace("postgresql+asyncpg://", "")
    
    # Split at @
    if "@" in url:
        auth_part, host_part = url.split("@", 1)
        if ":" in auth_part:
            user, password = auth_part.split(":", 1)
        else:
            user, password = None, None
    else:
        host_part = url
        user, password = None, None
    
    # Split host part
    if "/" in host_part:
        host_port, database = host_part.split("/", 1)
        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host = host_port
            port = 5432
    else:
        host, port = host_part.split(":") if ":" in host_part else (host_part, 5432)
        port = int(port)
        database = None
    
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database
    }


async def run_password_migration():
    """Add password field to users table"""
    conn_params = parse_database_url(DATABASE_URL)
    
    conn = await asyncpg.connect(
        host=conn_params["host"],
        port=conn_params["port"],
        user=conn_params["user"],
        password=conn_params["password"],
        database=conn_params["database"]
    )
    
    try:
        # Check if password_hash column already exists
        column_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='users' 
                AND column_name='password_hash'
            )
        """)
        
        if column_exists:
            print("✓ password_hash column already exists")
        else:
            # Add password_hash column
            await conn.execute("""
                ALTER TABLE users 
                ADD COLUMN password_hash VARCHAR(255)
            """)
            print("✓ Added password_hash column")
        
        # Check if username column exists
        username_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='users' 
                AND column_name='username'
            )
        """)
        
        if username_exists:
            print("✓ username column already exists")
        else:
            # Add username column
            await conn.execute("""
                ALTER TABLE users 
                ADD COLUMN username VARCHAR(255) UNIQUE
            """)
            print("✓ Added username column")
            
            # Create index on username
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username) 
                WHERE username IS NOT NULL
            """)
            print("✓ Created index on username")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_password_migration())

