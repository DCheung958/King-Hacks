# How to Run Echocare

> **📖 New to the project?** See **[GETTING_STARTED.md](./GETTING_STARTED.md)** for complete setup instructions from scratch.

## ⚠️ Important: You Need BOTH Backend and Frontend Running

The frontend **requires** the backend to be running. If you see "failed to fetch" errors, it means the backend isn't running.

---

## Step 1: Set Up Database

### 1.1 Install PostgreSQL

- **Download:** https://www.postgresql.org/download/
- **During installation:** Remember the password you set for the `postgres` user
- **Default port:** 5432

### 1.2 Create Database

**Option A: Using pgAdmin4 (Easier)**
1. Open pgAdmin4
2. Connect to PostgreSQL server
3. Right-click "Databases" → "Create" → "Database"
4. Name: `echocare_db`
5. Click "Save"

**Option B: Using Command Line**
```bash
psql -U postgres
CREATE DATABASE echocare_db;
\q
```

### 1.3 Create .env File (Optional if password matches default)

**Note:** If your PostgreSQL password is `DCheung6`, you can skip this step. The backend will use the default connection string.

**If your password is different**, create a file named `.env` in the `Backend` folder:

**Using Notepad (Windows):**
1. Open Notepad
2. Type this line (replace `YOUR_PASSWORD` with your PostgreSQL password):
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db
   ```
3. Click "File" → "Save As"
4. Navigate to `Backend` folder
5. File name: `.env` (with the dot!)
6. Save as type: "All Files (*.*)"
7. Click "Save"

**Using PowerShell:**
```powershell
cd Backend
echo "DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db" > .env
```
Then edit the file to replace `YOUR_PASSWORD` with your actual password.

**Example:** If your password is `mypass123`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:mypass123@localhost:5432/echocare_db
```

**Your .env file can also include other variables:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db
ELEVENLABS_API_KEY=your_api_key_here
```

### 1.4 Create Database Tables

Run migrations to create all required tables:

```bash
cd Backend
python run_migrations.py
```

**Expected output:**
```
Running database migrations...
Migration completed successfully!
```

**Verify tables in pgAdmin4:**
- Expand `echocare_db` → `Schemas` → `public` → `Tables`
- Should see: `users`, `voice_samples`, `conversations`, `messages`

---

## Step 2: Set Up the Backend

### Prerequisites
- Python 3.8 or higher installed
- pip (Python package manager)

### Installation Steps

1. **Navigate to the Backend folder:**
   ```bash
   cd Backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   
   ⚠️ **Note:** This may take 5-10 minutes (installs PyTorch, transformers, etc.)

3. **Start the backend server:**
   ```bash
   python main.py
   ```
   
   Or alternatively:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Verify the backend is running:**
   - You should see: `INFO:     Uvicorn running on http://0.0.0.0:8000`
   - Open your browser and visit: `http://localhost:8000/docs`
   - You should see the API documentation page
   - Visit: `http://localhost:8000/health` - should show `{"status":"healthy"}`

   **Keep this terminal window open!** The backend must stay running.

---

## Step 3: Set Up the Frontend

### Prerequisites
- Node.js and npm installed (download from https://nodejs.org/)

### Installation Steps

1. **Open a NEW terminal window** (keep the backend running in the first terminal)

2. **Navigate to the Frontend folder:**
   ```bash
   cd Frontend
   ```

3. **Install Node.js dependencies:**
   ```bash
   npm install
   ```
   
   ⚠️ **Note:** This may take 2-5 minutes the first time.

4. **Start the frontend development server:**
   ```bash
   npm run dev
   ```

5. **Verify the frontend is running:**
   - You should see: `Local: http://localhost:5173`
   - Open your browser and visit: `http://localhost:5173`

---

## Step 4: Test the Application

1. **Backend should be running on:** `http://localhost:8000`
2. **Frontend should be running on:** `http://localhost:5173`

3. **Try signing in:**
   - Go to `http://localhost:5173`
   - Enter an email and password
   - Click "Sign In / Create Account"
   - Should create account and redirect to chat

---

## Troubleshooting

### "Failed to fetch" Error

**This means the backend isn't running or isn't accessible.**

✅ **Solutions:**
1. Check that the backend terminal shows: `Uvicorn running on http://0.0.0.0:8000`
2. Visit `http://localhost:8000/health` in your browser - you should see `{"status":"healthy"}`
3. Make sure you didn't close the backend terminal window
4. Check that port 8000 isn't being used by another application

### "password authentication failed"

**Problem:** Database password is wrong

✅ **Solutions:**
1. Check `.env` file exists in `Backend` folder
2. Verify password in `.env` matches your PostgreSQL password exactly
3. No extra spaces before or after the password
4. Restart backend after changing `.env` file

### "Database is not available" Error

**Problem:** Database connection failed

✅ **Solutions:**
1. Make sure PostgreSQL is running (check Windows Services)
2. Verify database `echocare_db` exists (use pgAdmin4)
3. Check `.env` file has correct password
4. Run `python run_migrations.py` to create tables
5. Restart backend after fixing

### Backend Shows "Running in mock mode without database"

**Problem:** Database not connected

✅ **Solutions:**
1. Check `.env` file exists in `Backend` folder
2. Verify password is correct
3. Make sure PostgreSQL is running
4. Restart backend after fixing `.env`

### "Database does not exist"

**Problem:** Database hasn't been created

✅ **Solutions:**
1. Create database in pgAdmin4 (see Step 1.2)
2. Or run: `python run_migrations.py` (it will create it automatically)

### "I can't see the .env file"

**Problem:** File is hidden (Windows)

✅ **Solutions:**
1. In File Explorer, click "View" tab
2. Check "Hidden items" checkbox
3. The `.env` file should now be visible

### "File saves as .env.txt"

**Problem:** Notepad added .txt extension

✅ **Solutions:**
1. In "Save As" dialog, change "Save as type" to "All Files (*.*)"
2. Type `.env` in filename (including the dot)
3. Or rename file after saving: remove `.txt` extension

### Backend Won't Start

**Common issues:**
- **Missing dependencies:** Run `pip install -r requirements.txt` again
- **Port already in use:** Close other applications using port 8000, or change the port in `main.py`
- **Python not found:** Make sure Python is installed and in your PATH

### Frontend Won't Start

**Common issues:**
- **Missing dependencies:** Run `npm install` again
- **Port already in use:** Close other applications using port 5173
- **Node.js not found:** Make sure Node.js is installed

### "Connection refused"

**Problem:** PostgreSQL not running

✅ **Solutions:**
1. Check Windows Services - PostgreSQL should be running
2. Start PostgreSQL service if it's stopped
3. Verify port 5432 is correct

---

## Quick Reference

**Backend:**
- URL: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

**Frontend:**
- URL: `http://localhost:5173`
- Default API URL: `http://localhost:8000` (configured in code)

**Database:**
- Host: `localhost`
- Port: `5432`
- Database: `echocare_db`
- Connection: Set in `.env` file

---

## Connection String Format

The database connection string format is:
```
postgresql+asyncpg://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

**Examples:**
```env
# Default setup
DATABASE_URL=postgresql+asyncpg://postgres:mypassword@localhost:5432/echocare_db

# Different username
DATABASE_URL=postgresql+asyncpg://myuser:mypass@localhost:5432/echocare_db

# Different host/port
DATABASE_URL=postgresql+asyncpg://postgres:password@127.0.0.1:5432/echocare_db
```

---

## Optional: Run Without Database

The backend can run without a database, but authentication (sign in/sign up) won't work. Other features like emotion detection and response generation will still work.

To run without database:
- Just start the backend: `python main.py`
- The backend will show: "Running in mock mode without database"
- You can use the chat features, but not authentication

---

## Using the Batch Files (Windows)

If you're on Windows, you can use the provided batch files:

1. **Run `RUN.bat`** - This should start both backend and frontend (if configured)
2. Or run them separately in different terminals

---

## Setup Checklist

- [ ] PostgreSQL installed and running
- [ ] Database `echocare_db` created
- [ ] `.env` file created in `Backend` folder with correct password
- [ ] Database tables created (`python run_migrations.py`)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend running (`python main.py`)
- [ ] Frontend running (`npm run dev`)
- [ ] Can access `http://localhost:8000/health`
- [ ] Can access `http://localhost:5173`
- [ ] Can sign up/create account

---

## Need More Help?

- Check **[GETTING_STARTED.md](./GETTING_STARTED.md)** for complete setup from scratch
- Check `Backend/README.md` for backend API documentation
- Check `INTEGRATION_GUIDE.md` for integration details
