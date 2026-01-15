"""
Create database tables using SQLAlchemy
Alternative method using SQLAlchemy metadata.create_all()
"""

import asyncio
from sqlalchemy import create_engine, text
from database import database, DATABASE_URL, metadata
from models import users, voice_samples, conversations, messages

# Remove asyncpg driver from URL for SQLAlchemy engine
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


async def create_tables():
    """Create all tables using SQLAlchemy metadata"""
    # Create engine for synchronous operations
    engine = create_engine(SYNC_DATABASE_URL, echo=True)
    
    try:
        # Create all tables
        print("Creating database tables...")
        metadata.create_all(engine)
        print("Tables created successfully!")
        
        # Verify tables exist
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result]
            print(f"Created tables: {', '.join(tables)}")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    print(f"Creating tables using: {SYNC_DATABASE_URL.replace('DCheung6', '***')}")
    asyncio.run(create_tables())

