# How to Run Echocare

> **📖 New to the project?** See **[GETTING_STARTED.md](./GETTING_STARTED.md)** for complete setup instructions from scratch.

## ⚠️ Important: You Need BOTH Backend and Frontend Running

The frontend **requires** the backend to be running. If you see "failed to fetch" errors, it means the backend isn't running.

---

## Step 1: Set Up the Backend

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
   
   ⚠️ **Note:** This may take a few minutes as it installs packages like PyTorch and transformers.

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

   **Keep this terminal window open!** The backend must stay running.

---

## Step 2: Set Up the Frontend

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
   
   ⚠️ **Note:** This may take a few minutes the first time.

4. **Start the frontend development server:**
   ```bash
   npm run dev
   ```

5. **Verify the frontend is running:**
   - You should see: `Local: http://localhost:5173`
   - Open your browser and visit: `http://localhost:5173`

---

## Step 3: Test the Application

1. **Backend should be running on:** `http://localhost:8000`
2. **Frontend should be running on:** `http://localhost:5173`

3. **Try signing in:**
   - Go to `http://localhost:5173`
   - Enter an email and password
   - Click "Sign In / Create Account"
   - If you see "failed to fetch", check that the backend is running!

---

## Troubleshooting

### "Failed to fetch" Error

**This means the backend isn't running or isn't accessible.**

✅ **Solutions:**
1. Check that the backend terminal shows: `Uvicorn running on http://0.0.0.0:8000`
2. Visit `http://localhost:8000/health` in your browser - you should see `{"status":"healthy"}`
3. Make sure you didn't close the backend terminal window
4. Check that port 8000 isn't being used by another application

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

### Database Connection Errors

If you see database-related errors like "password authentication failed":

1. **Check `Backend/DATABASE_CONNECTION.md`** - This has step-by-step instructions
2. **Create a `.env` file** in the `Backend` folder with your database credentials:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db
   ```
3. **Or edit `Backend/database.py`** directly (line 10) to change the default connection string

The backend can still run in "mock mode" without a database, but authentication (sign in/sign up) won't work. See `Backend/DATABASE_CONNECTION.md` for full details.

---

## Quick Reference

**Backend:**
- URL: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

**Frontend:**
- URL: `http://localhost:5173`
- Default API URL: `http://localhost:8000` (configured in code)

---

## Using the Batch Files (Windows)

If you're on Windows, you can use the provided batch files:

1. **Run `RUN.bat`** - This should start both backend and frontend (if configured)
2. Or run them separately in different terminals

---

## Need Help?

- Check `Backend/README.md` for backend-specific issues
- Check `INTEGRATION_GUIDE.md` for integration details
- Check `Backend/DATABASE_SETUP.md` if you need database setup
