import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file FIRST
# Try loading from Backend folder explicitly
env_path = Path(__file__).parent / ".env"
print(f"\n[Database] Looking for .env file at: {env_path}")
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"[Database] ✓ Found and loaded .env file")
else:
    # Fallback to default location
    load_dotenv()
    print(f"[Database] ⚠ .env file NOT FOUND at: {env_path}")
    print(f"[Database]   Make sure .env file exists in Backend folder")

try:
    from databases import Database
    import sqlalchemy
    
    # Database connection URL - can be overridden with environment variable
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:Postgresql4Life!@localhost:5432/echocare_db"
    )
    
    # Debug: Show if DATABASE_URL came from .env or default
    env_db_url = os.getenv("DATABASE_URL")
    if env_db_url:
        # Hide password in output
        safe_url = env_db_url.split("@")[0].split(":")[-1] if "@" in env_db_url else "***"
        print(f"[Database] ✓ Using DATABASE_URL from .env file (password: {safe_url}...)")
    else:
        print(f"[Database] ⚠ Using DEFAULT DATABASE_URL (password: Postgresql4Life!)")
        print(f"[Database]   If your password is different, add DATABASE_URL to .env file")
    
    database = Database(DATABASE_URL)
    metadata = sqlalchemy.MetaData()
except ImportError:
    # Database packages not installed - running in mock mode
    database = None
    metadata = None
    DATABASE_URL = None
