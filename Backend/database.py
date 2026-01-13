import os

try:
    from databases import Database
    import sqlalchemy
    
    # Database connection URL - can be overridden with environment variable
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:Postgresql4Life!@localhost:5432/echocare_db"
    )
    
    database = Database(DATABASE_URL)
    metadata = sqlalchemy.MetaData()
except ImportError:
    # Database packages not installed - running in mock mode
    database = None
    metadata = None
    DATABASE_URL = None
