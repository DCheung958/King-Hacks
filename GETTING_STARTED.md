# Getting Started - Complete Setup Guide

This guide will walk you through setting up the entire Echocare project from scratch.

---

## 📋 Prerequisites - What You Need to Install First

### 1. Python (for Backend)
- **Download:** https://www.python.org/downloads/
- **Version:** Python 3.8 or higher
- **During installation:** ✅ Check "Add Python to PATH"
- **Verify:** Open terminal/command prompt and type:
  ```bash
  python --version
  ```
  Should show: `Python 3.x.x`

### 2. Node.js and npm (for Frontend)
- **Download:** https://nodejs.org/
- **Version:** Node.js 18 or higher (LTS version recommended)
- **This installs both Node.js and npm**
- **Verify:** Open terminal and type:
  ```bash
  node --version
  npm --version
  ```
  Should show version numbers

### 3. PostgreSQL (for Database)
- **Download:** https://www.postgresql.org/download/
- **During installation:**
  - Remember the password you set for the `postgres` user
  - Default port is 5432 (keep this)
- **Verify:** PostgreSQL should be running (check Windows Services or use pgAdmin4)

### 4. pgAdmin4 (Optional but Recommended)
- **Download:** https://www.pgadmin.org/download/
- **This helps you manage your database visually**
- Not required, but makes database setup easier

---

## 🗄️ Step 1: Set Up Database

### Option A: Using pgAdmin4 (Easier)

1. **Open pgAdmin4**
2. **Connect to PostgreSQL server** (use the password you set during installation)
3. **Create the database:**
   - Right-click "Databases" → "Create" → "Database"
   - Name: `echocare_db`
   - Click "Save"

### Option B: Using Command Line

1. **Open Command Prompt or PowerShell**
2. **Connect to PostgreSQL:**
   ```bash
   psql -U postgres
   ```
   (Enter your PostgreSQL password when prompted)

3. **Create the database:**
   ```sql
   CREATE DATABASE echocare_db;
   ```

4. **Exit:**
   ```sql
   \q
   ```

---

## 🔧 Step 2: Set Up Backend

### 2.1 Navigate to Backend Folder
```bash
cd Backend
```

### 2.2 Install Python Dependencies
```bash
pip install -r requirements.txt
```

**⏱️ This may take 5-10 minutes** (installs packages like PyTorch, transformers, etc.)

### 2.3 Create .env File

1. **Create a new file** in the `Backend` folder named `.env`
   - In Notepad: File → Save As → Name: `.env` → Save as type: "All Files (*.*)"
   - Or use any text editor

2. **Add this line** (replace `YOUR_PASSWORD` with your PostgreSQL password):
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/echocare_db
   ```

   **Example:** If your password is `mypass123`:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:mypass123@localhost:5432/echocare_db
   ```

3. **Save the file** in the `Backend` folder

### 2.4 Create Database Tables

Run this command to create all required tables:
```bash
python run_migrations.py
```

**Expected output:**
```
Running database migrations...
Migration completed successfully!
```

**If you see errors:**
- "password authentication failed" → Check your password in `.env` file
- "database does not exist" → Create it first (see Step 1)

### 2.5 Verify Database Tables (Optional)

In pgAdmin4:
- Expand `echocare_db` → `Schemas` → `public` → `Tables`
- You should see: `users`, `voice_samples`, `conversations`, `messages`

---

## 🎨 Step 3: Set Up Frontend

### 3.1 Navigate to Frontend Folder
```bash
cd Frontend
```
(Or open a new terminal window)

### 3.2 Install Node.js Dependencies
```bash
npm install
```

**⏱️ This may take 2-5 minutes**

---

## 🚀 Step 4: Run the Application

### You Need TWO Terminal Windows Open

### Terminal 1: Backend Server

1. **Navigate to Backend folder:**
   ```bash
   cd Backend
   ```

2. **Start the backend:**
   ```bash
   python main.py
   ```

3. **You should see:**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

4. **✅ Keep this terminal open!** The backend must stay running.

5. **Test it:** Open browser → `http://localhost:8000/health`
   - Should show: `{"status":"healthy","upload_dir_exists":true}`

### Terminal 2: Frontend Server

1. **Navigate to Frontend folder:**
   ```bash
   cd Frontend
   ```

2. **Start the frontend:**
   ```bash
   npm run dev
   ```

3. **You should see:**
   ```
   Local:   http://localhost:5173
   ```

4. **✅ Keep this terminal open too!**

5. **Open in browser:** `http://localhost:5173`

---

## ✅ Step 5: Test Everything

1. **Backend is running:** `http://localhost:8000/health` shows healthy status
2. **Frontend is running:** `http://localhost:5173` opens the app
3. **Try signing up:**
   - Enter an email and password
   - Click "Sign In / Create Account"
   - Should create account and redirect to chat

---

## 🐛 Troubleshooting

### "Failed to fetch" Error

**Problem:** Frontend can't connect to backend

**Solutions:**
1. ✅ Make sure backend is running (Terminal 1)
2. ✅ Check `http://localhost:8000/health` works
3. ✅ Restart both backend and frontend

### "password authentication failed"

**Problem:** Database password is wrong

**Solutions:**
1. ✅ Check `.env` file exists in `Backend` folder
2. ✅ Verify password in `.env` matches your PostgreSQL password
3. ✅ Restart backend after changing `.env`

### "Database is not available" Error

**Problem:** Database connection failed

**Solutions:**
1. ✅ Make sure PostgreSQL is running (check Windows Services)
2. ✅ Verify database `echocare_db` exists (use pgAdmin4)
3. ✅ Check `.env` file has correct password
4. ✅ Run `python run_migrations.py` to create tables

### "Module not found" or "Package not installed"

**Problem:** Dependencies not installed

**Solutions:**
1. ✅ Backend: Run `pip install -r requirements.txt` again
2. ✅ Frontend: Run `npm install` again
3. ✅ Make sure you're in the correct folder

### Backend Shows "Running in mock mode"

**Problem:** Database not connected

**Solutions:**
1. ✅ Check `.env` file exists and has correct password
2. ✅ Verify PostgreSQL is running
3. ✅ Restart backend after fixing `.env`

### Port Already in Use

**Problem:** Port 8000 or 5173 is already taken

**Solutions:**
1. ✅ Close other applications using those ports
2. ✅ Or change ports in `main.py` (backend) or `vite.config.js` (frontend)

---

## 📁 Project Structure

```
Echocare/
├── Backend/
│   ├── .env                    ← Create this file (database password)
│   ├── main.py                 ← Backend server
│   ├── requirements.txt        ← Python dependencies
│   ├── database.py            ← Database connection
│   └── run_migrations.py      ← Creates database tables
│
└── Frontend/
    ├── package.json            ← Node.js dependencies
    ├── src/                    ← React app code
    └── vite.config.js         ← Frontend configuration
```

---

## 🔄 Quick Start (After Initial Setup)

Once everything is set up, to run the project:

1. **Terminal 1 - Backend:**
   ```bash
   cd Backend
   python main.py
   ```

2. **Terminal 2 - Frontend:**
   ```bash
   cd Frontend
   npm run dev
   ```

3. **Open browser:** `http://localhost:5173`

---

## 📝 Important Files

- **`.env`** (Backend folder) - Contains database password (create this!)
- **`requirements.txt`** (Backend) - Python packages needed
- **`package.json`** (Frontend) - Node.js packages needed

---

## 🆘 Still Having Issues?

1. **Check all prerequisites are installed:**
   - Python: `python --version`
   - Node.js: `node --version`
   - PostgreSQL: Check Windows Services

2. **Verify database exists:**
   - Use pgAdmin4 to check `echocare_db` exists

3. **Check `.env` file:**
   - Must be in `Backend` folder
   - Must have correct password
   - No extra spaces

4. **Restart everything:**
   - Stop backend (Ctrl+C)
   - Stop frontend (Ctrl+C)
   - Start backend again
   - Start frontend again

---

## ✅ Setup Checklist

- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed
- [ ] PostgreSQL installed and running
- [ ] Database `echocare_db` created
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created in Backend folder with correct password
- [ ] Database tables created (`python run_migrations.py`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Backend running (`python main.py`)
- [ ] Frontend running (`npm run dev`)
- [ ] Can access `http://localhost:5173`
- [ ] Can sign up/create account

---

**That's it! You should now have the full project running.** 🎉

