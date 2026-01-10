# Quick Start Guide - Database Setup

## 1. Install Dependencies

```bash
cd Backend
pip install -r requirements.txt
```

This installs:
- FastAPI
- databases (with PostgreSQL support)
- asyncpg (PostgreSQL async driver)
- SQLAlchemy (for schema definitions)

## 2. Create Database

**Option A: Using PostgreSQL command line**
```bash
psql -U postgres
CREATE DATABASE echocare_db;
\q
```

**Option B: Database will be created automatically** by `run_migrations.py` if it doesn't exist.

## 3. Run Migrations

**Choose one method:**

### Method 1: SQL Script (Recommended)
```bash
cd Backend
python run_migrations.py
```

This will:
- Create the database if it doesn't exist
- Create all tables
- Set up indexes and constraints

### Method 2: SQLAlchemy
```bash
cd Backend
python create_tables.py
```

### Method 3: Manual SQL
```bash
psql -U postgres -d echocare_db -f migrations/001_initial_schema.sql
```

## 4. Verify Setup

**Check tables:**
```bash
psql -U postgres -d echocare_db
\dt
\q
```

Should show: `users`, `voice_samples`, `conversations`, `messages`

## 5. Start the Backend

```bash
python main.py
```

Or:
```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` to see all endpoints.

## 6. Test the Database

**Using curl:**
```bash
# Create a user
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'

# Get user
curl "http://localhost:8000/api/users/email/test@example.com"
```

**Using the API docs:**
Visit `http://localhost:8000/docs` and use the interactive interface.

## Troubleshooting

### "Database does not exist"
- Run `CREATE DATABASE echocare_db;` manually
- Or ensure `run_migrations.py` can create it (requires superuser privileges)

### "Connection refused"
- Ensure PostgreSQL is running: `pg_isready`
- Check connection string in `database.py`
- Verify credentials

### "Module not found: databases"
- Run `pip install -r requirements.txt` again
- Ensure you're in the correct virtual environment

### "Permission denied"
- Ensure PostgreSQL user has CREATE DATABASE privileges
- Check `pg_hba.conf` for authentication settings

## Next Steps

1. **Update Frontend** to pass `user_id` and `conversation_id` to API endpoints
2. **Implement user authentication** to associate requests with users
3. **Add conversation persistence** - conversations are now saved automatically
4. **Test full flow**: Create user → Start conversation → Send messages → View history

## Connection String

Default: `postgresql+asyncpg://postgres:Postgresql4Life!@localhost:5432/echocare_db`

To override, set environment variable:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@host:port/database"
```

## Schema Overview

- **users**: User accounts
- **voice_samples**: Uploaded voice recordings
- **conversations**: Chat sessions
- **messages**: Individual messages in conversations

All relationships use CASCADE delete for data integrity.

