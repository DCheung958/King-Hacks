# Verify Database Connection - Step by Step

> **📖 First time setting up?** See **[GETTING_STARTED.md](../GETTING_STARTED.md)** for complete setup instructions.

## Step 1: Verify .env File is Created

Make sure you have a `.env` file in the `Backend` folder with:

```env
DATABASE_URL=postgresql+asyncpg://postgres:mypassword123@localhost:5432/echocare_db
```

**Important:** Replace `mypassword123` with your actual PostgreSQL password.

## Step 2: Verify Database Exists in pgAdmin4

1. Open pgAdmin4
2. Connect to your PostgreSQL server
3. Expand "Databases"
4. You should see `echocare_db` listed
5. If it doesn't exist, right-click "Databases" → "Create" → "Database"
   - Name: `echocare_db`
   - Click "Save"

## Step 3: Create Database Tables (Run Migrations)

The database exists, but it needs tables. Run this command:

```bash
cd Backend
python run_migrations.py
```

**Expected output:**
```
Running database migrations...
Database URL: postgresql+asyncpg://postgres:***@localhost:5432/echocare_db
Running migration: Backend\migrations\001_initial_schema.sql
Migration completed successfully!
```

**If you see errors:**
- "password authentication failed" → Check your password in `.env` file
- "database does not exist" → Create it in pgAdmin4 first (Step 2)
- "connection refused" → Make sure PostgreSQL is running

## Step 4: Verify Tables Were Created

In pgAdmin4:
1. Expand `echocare_db` database
2. Expand "Schemas" → "public" → "Tables"
3. You should see these tables:
   - `users`
   - `voice_samples`
   - `conversations`
   - `messages`

If tables are missing, run `python run_migrations.py` again.

## Step 5: Test Backend Connection

1. **Start the backend:**
   ```bash
   cd Backend
   python main.py
   ```

2. **Look for these messages:**
   - ✅ **Good:** No database errors, or "Connected to database"
   - ❌ **Bad:** "password authentication failed" or "Could not connect to database"

3. **Test the connection:**
   - Open browser: `http://localhost:8000/health`
   - Should see: `{"status":"healthy","upload_dir_exists":true}`

## Step 6: Test Authentication Endpoint

1. **Keep backend running**
2. **Test signup endpoint** (using curl, Postman, or browser):
   ```
   POST http://localhost:8000/api/auth/signup
   Content-Type: application/json
   
   {
     "email": "test@example.com",
     "password": "test123",
     "name": "Test User"
   }
   ```

   **Expected response:**
   ```json
   {
     "access_token": "...",
     "token_type": "bearer",
     "user_id": "...",
     "email": "test@example.com",
     "name": "Test User"
   }
   ```

   **If you get error 503:**
   - Database is not connected
   - Check `.env` file exists and has correct password
   - Restart the backend after creating `.env` file

## Troubleshooting

### "password authentication failed"

**Solution:**
1. Check your PostgreSQL password in pgAdmin4
2. Update `.env` file with correct password
3. Restart backend

### "Database does not exist"

**Solution:**
1. Create database in pgAdmin4 (see Step 2)
2. Or run: `python run_migrations.py` (it will create it automatically)

### "Could not connect to database"

**Check:**
1. PostgreSQL service is running (Windows Services or `pg_isready`)
2. Port 5432 is correct
3. Host is `localhost` (not `127.0.0.1` if that matters)

### Backend shows "Running in mock mode without database"

**This means:**
- Database connection failed
- Check `.env` file exists in `Backend` folder
- Check password is correct
- Restart backend after fixing

### Tables don't exist after migration

**Solution:**
1. Check pgAdmin4 to see if tables exist
2. If not, run: `python run_migrations.py` again
3. Check for error messages

## Quick Verification Checklist

- [ ] `.env` file exists in `Backend` folder
- [ ] `.env` file has correct password
- [ ] `echocare_db` database exists in pgAdmin4
- [ ] Ran `python run_migrations.py` successfully
- [ ] Tables exist in pgAdmin4 (users, voice_samples, conversations, messages)
- [ ] Backend starts without database errors
- [ ] Can access `http://localhost:8000/health`
- [ ] Can create account via `/api/auth/signup`

## Still Having Issues?

1. **Check backend terminal output** - it will show connection errors
2. **Check pgAdmin4** - verify database and tables exist
3. **Verify `.env` file** - make sure it's in the `Backend` folder (not root folder)
4. **Restart backend** after creating/updating `.env` file

