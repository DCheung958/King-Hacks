# Database Setup Guide for Echocare

## Prerequisites

1. **PostgreSQL installed and running**
   - Download from: https://www.postgresql.org/download/
   - Default port: 5432

2. **Create database** (if not exists):
   ```sql
   CREATE DATABASE echocare_db;
   ```

## Quick Setup

### Option 1: Using SQL Migration Script (Recommended)

1. **Run the migration script:**
   ```bash
   cd Backend
   python run_migrations.py
   ```

   This script will:
   - Create the database if it doesn't exist
   - Create all tables (users, voice_samples, conversations, messages)
   - Create indexes and constraints
   - Add helpful comments

### Option 2: Using SQLAlchemy

1. **Run the table creation script:**
   ```bash
   cd Backend
   python create_tables.py
   ```

### Option 3: Manual SQL Execution

1. **Connect to PostgreSQL:**
   ```bash
   psql -U postgres -d echocare_db
   ```

2. **Run the migration file:**
   ```sql
   \i migrations/001_initial_schema.sql
   ```

   Or copy-paste the contents of `migrations/001_initial_schema.sql` into your psql prompt.

## Database Schema

### Tables Created

#### 1. `users`
- `id` (UUID, Primary Key)
- `email` (String, Unique, Indexed)
- `name` (String, Optional)
- `created_at` (Timestamp)

#### 2. `voice_samples`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to users.id, Nullable)
- `filename` (String)
- `uploaded_at` (Timestamp)
- Indexes: `user_id`, `uploaded_at`

#### 3. `conversations`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to users.id)
- `created_at` (Timestamp)
- Indexes: `user_id`, `created_at`

#### 4. `messages`
- `id` (UUID, Primary Key)
- `conversation_id` (UUID, Foreign Key to conversations.id)
- `role` (String, "user" or "assistant")
- `text` (Text)
- `emotion` (String, Nullable)
- `timestamp` (Timestamp)
- Indexes: `conversation_id`, `timestamp`, `role`
- Constraint: `role` must be "user" or "assistant"

### Constraints

- **Primary Keys**: All tables have UUID primary keys
- **Foreign Keys**: 
  - `voice_samples.user_id` → `users.id` (CASCADE delete)
  - `conversations.user_id` → `users.id` (CASCADE delete)
  - `messages.conversation_id` → `conversations.id` (CASCADE delete)
- **Unique**: `users.email` is unique with index
- **Check**: `messages.role` must be "user" or "assistant"

## Connection String

Default connection string (stored in `database.py`):
```
postgresql+asyncpg://postgres:Postgresql4Life!@localhost:5432/echocare_db
```

To override, set environment variable:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@host:port/database"
```

## Using Database Operations

The `db_operations.py` module provides CRUD functions:

### User Operations
```python
from db_operations import create_user, get_user_by_email, get_or_create_user

# Create user
user = await create_user(email="user@example.com", name="John Doe")

# Get user
user = await get_user_by_email("user@example.com")

# Get or create (useful for sessions)
user = await get_or_create_user(email="user@example.com", name="John Doe")
```

### Voice Sample Operations
```python
from db_operations import create_voice_sample, get_voice_samples_by_user

# Create voice sample
sample = await create_voice_sample(filename="recording.webm", user_id=user_id)

# Get user's voice samples
samples = await get_voice_samples_by_user(user_id)
```

### Conversation Operations
```python
from db_operations import create_conversation, get_conversations_by_user

# Create conversation
conversation = await create_conversation(user_id)

# Get user's conversations
conversations = await get_conversations_by_user(user_id, limit=50)
```

### Message Operations
```python
from db_operations import create_message, get_messages_by_conversation

# Create message
message = await create_message(
    conversation_id=conversation_id,
    role="user",
    text="Hello",
    emotion="calm"
)

# Get conversation history
messages = await get_messages_by_conversation(conversation_id)
```

### Convenience Functions
```python
from db_operations import create_conversation_with_message

# Create conversation with initial user/assistant messages
conversation = await create_conversation_with_message(
    user_id=user_id,
    user_text="I'm feeling anxious",
    assistant_text="I'm here to help you",
    emotion="anxiety"
)
```

## Verification

After setup, verify tables exist:

```sql
-- Connect to database
psql -U postgres -d echocare_db

-- List all tables
\dt

-- Describe a table
\d users
\d voice_samples
\d conversations
\d messages

-- Check indexes
\di
```

Or use the Python script:
```python
from database import database
import asyncio

async def check_tables():
    await database.connect()
    tables = await database.fetch_all(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )
    print("Tables:", [t['table_name'] for t in tables])
    await database.disconnect()

asyncio.run(check_tables())
```

## Troubleshooting

### Database Connection Error
- Ensure PostgreSQL is running: `pg_isready` or check service status
- Verify credentials in connection string
- Check if database exists: `psql -U postgres -l | grep echocare_db`

### Permission Errors
- Ensure user has CREATE DATABASE privileges
- Check PostgreSQL pg_hba.conf for authentication settings

### UUID Extension Error
- The migration script enables `uuid-ossp` extension automatically
- If manual setup, run: `CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`

### Foreign Key Errors
- Ensure parent tables exist before creating child tables
- Check that referenced IDs exist in parent tables

## Next Steps

1. **Update API endpoints** to use database operations (see `main.py`)
2. **Add user authentication** to associate requests with users
3. **Implement conversation persistence** in chat endpoints
4. **Add data validation** using Pydantic models
5. **Set up database backups** for production

## Production Considerations

- Use connection pooling for better performance
- Set up database backups and replication
- Use environment variables for sensitive credentials
- Implement database migrations system (e.g., Alembic)
- Add database monitoring and logging
- Consider using database connection health checks

