# Database Connection Setup

> **📖 First time setting up?** See **[GETTING_STARTED.md](../GETTING_STARTED.md)** for complete setup instructions.

## Where to Change Database Connection

The database connection is configured in **`Backend/database.py`** (line 8-10).

The code checks for an environment variable first, then falls back to a default.

## Option 1: Use .env File (Recommended - Best Practice)

Create a file called **`.env`** in the `Backend` folder:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db
```

**Replace with your actual values:**
- `postgres` = your PostgreSQL username
- `YOUR_PASSWORD` = your PostgreSQL password  
- `localhost` = database host (usually localhost)
- `5432` = database port (default PostgreSQL port)
- `echocare_db` = database name

**Example:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:mypassword123@localhost:5432/echocare_db
```

The `.env` file is automatically loaded by the backend (using `python-dotenv`).

## Option 2: Edit database.py Directly

If you prefer, you can edit `Backend/database.py` directly:

1. Open `Backend/database.py`
2. Find line 10 (the default connection string)
3. Change it to your database credentials:

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/echocare_db"
)
```

⚠️ **Note:** Editing `database.py` directly means your password will be in the code. Using `.env` is safer.

## Default Connection (What the Backend Tries First)

The backend tries to connect with these default credentials:
- **User:** `postgres`
- **Password:** `Postgresql4Life!`
- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `echocare_db`

## Option 2: Change PostgreSQL Password to Match Default

If you want to use the default password:

1. **Open PostgreSQL command line:**
   ```bash
   psql -U postgres
   ```

2. **Change the password:**
   ```sql
   ALTER USER postgres WITH PASSWORD 'Postgresql4Life!';
   ```

3. **Exit:**
   ```sql
   \q
   ```

## Option 3: Create the Database

If the database doesn't exist yet:

1. **Connect to PostgreSQL:**
   ```bash
   psql -U postgres
   ```

2. **Create the database:**
   ```sql
   CREATE DATABASE echocare_db;
   ```

3. **Exit:**
   ```sql
   \q
   ```

4. **Run migrations:**
   ```bash
   cd Backend
   python run_migrations.py
   ```

## Option 4: Run Without Database (Limited Functionality)

The backend can run without a database, but authentication (sign in/sign up) won't work. Other features like emotion detection and response generation will still work.

To run without database:
- Just start the backend: `python main.py`
- The backend will show: "Running in mock mode without database"
- You can use the chat features, but not authentication

## Verify Database Connection

After setting up, restart the backend and check the terminal output:

✅ **Good:** No database errors, or "Connected to database"

❌ **Bad:** "password authentication failed" or "Could not connect to database"

## Troubleshooting

### "password authentication failed"
- Check your PostgreSQL password
- Update `DATABASE_URL` in `.env` file or `database.py`
- Make sure PostgreSQL is running

### "Database does not exist"
- Create the database: `CREATE DATABASE echocare_db;`
- Or run: `python run_migrations.py` (it will create it automatically)

### "Connection refused"
- Make sure PostgreSQL is running
- Check if PostgreSQL is on port 5432
- Try: `pg_isready` (Linux/Mac) or check Windows Services

### PostgreSQL Not Installed
- Download from: https://www.postgresql.org/download/
- Or use Docker: `docker run -e POSTGRES_PASSWORD=Postgresql4Life! -p 5432:5432 postgres`

## Connection String Format

The connection string format is:
```
postgresql+asyncpg://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

**Examples:**
```env
# Default PostgreSQL setup
DATABASE_URL=postgresql+asyncpg://postgres:mypassword@localhost:5432/echocare_db

# Different username
DATABASE_URL=postgresql+asyncpg://myuser:mypass@localhost:5432/echocare_db

# Different host/port
DATABASE_URL=postgresql+asyncpg://postgres:password@127.0.0.1:5432/echocare_db

# Remote database
DATABASE_URL=postgresql+asyncpg://user:pass@example.com:5432/echocare_db
```

## Other Environment Variables

You can also set these in the `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db
ELEVENLABS_API_KEY=your_key_here  # Optional, for voice features
```

