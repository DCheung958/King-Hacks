# How to Run Echocare Application

## Prerequisites

1. **Python 3.8+** installed
2. **Node.js and npm** installed
3. **PostgreSQL** installed and running (optional - app works with mocks if DB not set up)

## Quick Start (3 Steps)

### Step 1: Start the Backend

Open Terminal 1:

```bash
cd Backend

# Install Python dependencies
pip install -r requirements.txt

# (Optional) Set up database - Skip if you just want to test with mocks
python run_migrations.py

# Start the FastAPI server
python main.py
```

The backend will start at: **http://localhost:8000**

You can verify it's running by visiting:
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Step 2: Start the Frontend

Open Terminal 2 (new terminal window):

```bash
cd Frontend

# Install Node dependencies (only needed first time)
npm install

# Start the development server
npm run dev
```

The frontend will start at: **http://localhost:5173**

### Step 3: Open in Browser

Open your browser and go to: **http://localhost:5173**

You should see the Echocare chat interface!

## Detailed Setup

### Backend Setup (Detailed)

#### Option A: With Database (Full Features)

1. **Install PostgreSQL** (if not already installed)
   - Download from: https://www.postgresql.org/download/
   - Default port: 5432

2. **Create database** (optional - migration script can create it):
   ```bash
   psql -U postgres
   CREATE DATABASE echocare_db;
   \q
   ```

3. **Install Python dependencies:**
   ```bash
   cd Backend
   pip install -r requirements.txt
   ```

4. **Run database migrations:**
   ```bash
   python run_migrations.py
   ```
   This creates all tables (users, conversations, messages, voice_samples)

5. **Update database connection** (if needed):
   - Edit `Backend/database.py` if your PostgreSQL credentials differ
   - Default: `postgresql+asyncpg://postgres:Postgresql4Life!@localhost:5432/echocare_db`

6. **Start backend:**
   ```bash
   python main.py
   ```
   
   Or with auto-reload:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

#### Option B: Without Database (Mock Mode)

1. **Install Python dependencies:**
   ```bash
   cd Backend
   pip install -r requirements.txt
   ```

2. **Start backend:**
   ```bash
   python main.py
   ```
   
   The app will work with mock responses even without a database connection.

### Frontend Setup (Detailed)

1. **Navigate to frontend directory:**
   ```bash
   cd Frontend
   ```

2. **Install dependencies** (first time only):
   ```bash
   npm install
   ```

3. **Configure API URL** (optional):
   - Create `.env` file in `Frontend/` directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```
   - Default is `http://localhost:8000` if not specified

4. **Start development server:**
   ```bash
   npm run dev
   ```

5. **Open in browser:**
   - The terminal will show the local URL (usually http://localhost:5173)
   - Open this URL in your browser

## Testing the Application

### Test Voice Input:
1. Click "🎤 Start Listening"
2. Speak: "I'm feeling anxious about work"
3. Watch it transcribe and generate a response
4. Listen to the audio playback

### Test Voice Recording:
1. Click "🎙️ Start Recording"
2. Record your voice
3. Click "⏹️ Stop Recording"
4. The audio will be uploaded to the backend

### Test Chat Flow:
1. Use speech input or type manually
2. Messages appear in the chat window
3. Assistant responds with therapeutic messages
4. Audio plays automatically

## Troubleshooting

### Backend Issues

**"Module not found: databases"**
```bash
pip install -r requirements.txt
```

**"Connection refused" (Database)**
- Skip database setup - app works with mocks
- Or ensure PostgreSQL is running: `pg_isready`
- Check connection string in `Backend/database.py`

**"Port 8000 already in use"**
```bash
# Kill process on port 8000 (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
uvicorn main:app --port 8001
```

### Frontend Issues

**"Module not found" errors**
```bash
cd Frontend
rm -rf node_modules package-lock.json
npm install
```

**"Port 5173 already in use"**
- Vite will automatically use the next available port
- Check terminal output for the actual URL

**"Failed to fetch" (Backend Connection)**
- Ensure backend is running on port 8000
- Check CORS settings in `Backend/main.py`
- Verify `VITE_API_URL` in `.env` file matches backend URL

**Speech Recognition Not Working:**
- Ensure you're on HTTPS or localhost (Web Speech API requirement)
- Grant microphone permissions in browser
- Try Chrome or Edge (best support for Web Speech API)

### Database Issues

**"Database does not exist"**
```bash
# Create manually
psql -U postgres
CREATE DATABASE echocare_db;
\q

# Or let migration script create it (requires superuser)
python run_migrations.py
```

**"Permission denied"**
- Ensure PostgreSQL user has CREATE DATABASE privileges
- Check `pg_hba.conf` for authentication settings

## Running in Production Mode

### Backend:
```bash
cd Backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend:
```bash
cd Frontend
npm run build
npm run preview
```

## Environment Variables

### Backend (`Backend/.env` or environment):
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database
```

### Frontend (`Frontend/.env`):
```env
VITE_API_URL=http://localhost:8000
```

## Common Commands

### Backend:
```bash
# Run server
python main.py

# Run with auto-reload
uvicorn main:app --reload

# Run migrations
python run_migrations.py

# Create tables (alternative)
python create_tables.py
```

### Frontend:
```bash
# Development
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## What to Expect

When running successfully:

✅ **Backend** shows:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

✅ **Frontend** shows:
```
  VITE v7.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

✅ **Browser** shows:
- Echocare chat interface
- Speech input button
- Voice recorder button
- Chat window ready for messages

## Next Steps After Running

1. **Test the full flow** - Speak a message and see the response
2. **Set up database** - If you want to persist conversations
3. **Integrate ElevenLabs** - Replace mock TTS with real voice synthesis
4. **Add authentication** - Implement user login/signup
5. **Deploy** - Deploy to cloud (Vercel, Railway, etc.)

## Need Help?

- Check API docs: http://localhost:8000/docs
- Check backend logs in terminal
- Check browser console (F12) for frontend errors
- Verify both servers are running
- Ensure ports aren't blocked by firewall




