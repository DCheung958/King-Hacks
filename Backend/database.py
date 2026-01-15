import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file FIRST
# Try loading from Backend folder explicitly
env_path = Path(__file__).parent / ".env"
print(f"\n[Database] Looking for .env file at: {env_path}")
if env_path.exists():
    # Debug: Show ALL lines in file first
    with open(env_path, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        print(f"[Database] ✓ Found .env file with {len(all_lines)} total lines")
        for i, line in enumerate(all_lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                print(f"[Database]   Line {i}: (empty or comment)")
            elif 'DATABASE_URL' in stripped:
                # Hide password in output
                if '@' in stripped:
                    safe_line = stripped.split('@')[0].rsplit(':', 1)[0] + ':***@' + stripped.split('@')[1]
                else:
                    safe_line = stripped
                print(f"[Database]   Line {i}: {safe_line}")
            elif 'ELEVENLABS' in stripped.upper():
                # Show first part of API key
                if '=' in stripped:
                    key_part = stripped.split('=')[0]
                    print(f"[Database]   Line {i}: {key_part}=***...")
                else:
                    print(f"[Database]   Line {i}: (ElevenLabs key - hidden)")
            else:
                print(f"[Database]   Line {i}: {stripped[:60]}...")
    
    # Now load the .env file
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"[Database] ✓ Loaded .env file")
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
        "postgresql+asyncpg://postgres:DCheung6@localhost:5432/echocare_db"
    )
    
    # Debug: Show if DATABASE_URL came from .env or default
    env_db_url = os.getenv("DATABASE_URL")
    print(f"[Database] Checking environment for DATABASE_URL...")
    print(f"[Database]   os.getenv('DATABASE_URL') = {'Found' if env_db_url else 'None'}")
    
    if env_db_url:
        # Hide password in output
        if "@" in env_db_url:
            safe_url = env_db_url.split("@")[0].rsplit(":", 1)[0] + ":***"
        else:
            safe_url = "***"
        print(f"[Database] ✓ Using DATABASE_URL from environment")
        print(f"[Database]   Connection: {safe_url}@...")
    else:
        print(f"[Database] ⚠ DATABASE_URL NOT FOUND in environment variables!")
        print(f"[Database]   This means load_dotenv() didn't load it from .env file")
        print(f"[Database]   Possible issues:")
        print(f"[Database]   - Line has spaces around = sign")
        print(f"[Database]   - Line has quotes around value")
        print(f"[Database]   - Line is commented out with #")
        print(f"[Database]   - File encoding issue")
        print(f"[Database]   Using DEFAULT DATABASE_URL (password: DCheung6)")
    
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
