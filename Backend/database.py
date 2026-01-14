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
    
    # Debug: Check what's actually in the .env file
    with open(env_path, 'r') as f:
        content = f.read()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]
        print(f"[Database] Found {len(lines)} non-empty lines in .env file")
        for i, line in enumerate(lines, 1):
            if 'DATABASE_URL' in line:
                # Hide password in output
                if '@' in line:
                    safe_line = line.split('@')[0].rsplit(':', 1)[0] + ':***@' + line.split('@')[1]
                else:
                    safe_line = line
                print(f"[Database]   Line {i}: {safe_line}")
            elif 'PASSWORD' in line.upper() or 'PASS' in line.upper():
                print(f"[Database]   Line {i}: (contains password - hidden)")
            else:
                print(f"[Database]   Line {i}: {line[:50]}...")
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
        if "@" in env_db_url:
            safe_url = env_db_url.split("@")[0].rsplit(":", 1)[0] + ":***"
        else:
            safe_url = "***"
        print(f"[Database] ✓ Using DATABASE_URL from .env file")
        print(f"[Database]   Connection: {safe_url}@...")
    else:
        print(f"[Database] ⚠ DATABASE_URL NOT FOUND in environment variables!")
        print(f"[Database]   Check .env file - make sure it contains:")
        print(f"[Database]   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db")
        print(f"[Database]   Using DEFAULT DATABASE_URL (password: Postgresql4Life!)")
    
    database = Database(DATABASE_URL)
    metadata = sqlalchemy.MetaData()
    # Track connection status
    DATABASE_CONNECTED = False
except ImportError:
    # Database packages not installed - running in mock mode
    database = None
    metadata = None
    DATABASE_URL = None
    DATABASE_CONNECTED = False
