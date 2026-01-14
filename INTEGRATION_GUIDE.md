# Echocare - Frontend-Backend Integration Guide

> **📖 First time setting up?** See **[GETTING_STARTED.md](./GETTING_STARTED.md)** for complete setup instructions from scratch.

## Quick Start

### 1. Start the Backend

```bash
cd Backend
pip install -r requirements.txt
python main.py
```

The backend will run on `http://localhost:8000`

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 2. Start the Frontend

```bash
cd Frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:5173`

### 3. Configure API URL (Optional)

If your backend runs on a different port, create a `.env` file in `Frontend/`:

```env
VITE_API_URL=http://localhost:8000
```

Default is `http://localhost:8000` if not specified.

## Full Flow Testing

### Test the Complete Chat Flow

1. **Open the frontend** in your browser: `http://localhost:5173`

2. **Use Speech Input:**
   - Click "🎤 Start Listening"
   - Speak your message (e.g., "I'm feeling anxious about work")
   - The Web Speech API will transcribe your speech
   - The transcript will be sent to the backend for:
     - Emotion detection (`/api/emotion`)
     - Response generation (`/api/respond`)
     - Speech synthesis (`/api/synthesize`)
   - You'll see the assistant response and hear the synthesized audio

3. **Use Voice Recorder:**
   - Click "🎙️ Start Recording"
   - Record your message
   - Click "⏹️ Stop Recording"
   - The audio blob will be uploaded to `/api/voice-sample`
   - Currently, this stores the sample for future voice cloning
   - For transcription, use Speech Input instead

## API Endpoints

### `POST /api/emotion`
Detect emotion from text (MOCKED - keyword-based)

**Request:**
```json
{
  "text": "I'm feeling really anxious about tomorrow"
}
```

**Response:**
```json
{
  "emotion": "anxiety",
  "confidence": 0.75
}
```

### `POST /api/respond`
Generate therapeutic response (MOCKED - predefined responses)

**Request:**
```json
{
  "text": "I'm struggling with stress",
  "emotion": "anxiety"
}
```

**Response:**
```json
{
  "response_text": "I'm really glad you shared that with me. Remember to take deep breaths and take your time.",
  "emotion": "anxiety"
}
```

### `POST /api/voice-sample`
Upload voice sample for cloning (MOCKED - just stores file)

**Request:** Multipart form data with audio file

**Response:**
```json
{
  "message": "Voice sample uploaded successfully",
  "filename": "uuid-filename.webm",
  "file_size": 12345
}
```

### `POST /api/synthesize`
Synthesize speech from text (MOCKED - returns sample audio URL)

**Request:**
```json
{
  "text": "I'm here to help you",
  "voice_id": null
}
```

**Response:**
```json
{
  "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
  "duration": 2.5
}
```

## Fallback Behavior

The frontend is designed to gracefully handle backend unavailability:

- **If backend is down**: Frontend services will fall back to mock responses
- **If API calls fail**: Error messages are displayed to the user
- **If audio synthesis fails**: Falls back to local `/sample.mp3` or silent audio

## Testing Offline (Frontend Only)

If you want to test the frontend without the backend running:

1. The frontend will automatically use mock responses
2. Error messages will appear but won't block functionality
3. Voice recording still works (stores in memory)
4. Speech-to-text still works (Web Speech API)

## Next Steps for Real Integration

### 1. Replace Mock Emotion Detection
- Integrate Hugging Face emotion classification model
- Update `/api/emotion` endpoint

### 2. Replace Mock Response Generation
- Use GPT-based therapy assistant
- Update `/api/respond` endpoint

### 3. Integrate ElevenLabs API
- Add ElevenLabs API key to environment variables
- Update `/api/synthesize` to call ElevenLabs TTS
- Update `/api/voice-sample` to process with ElevenLabs for cloning

### 4. Add Audio Storage
- Store generated audio files in cloud storage (S3, Cloudinary)
- Return signed URLs for secure access

## Troubleshooting

### CORS Errors
- Ensure backend CORS middleware includes your frontend URL
- Check `allow_origins` in `Backend/main.py`

### Audio Not Playing
- Check browser autoplay policies
- Ensure audio URL is accessible
- Check browser console for errors

### Speech Recognition Not Working
- Ensure HTTPS or localhost (required by Web Speech API)
- Check browser permissions for microphone
- Try a different browser (Chrome/Edge recommended)

### Backend Not Connecting
- Verify backend is running: `curl http://localhost:8000/health`
- Check frontend console for network errors
- Verify `VITE_API_URL` matches backend URL

## File Structure

```
Echocare/
├── Backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .gitignore          # Git ignore rules
│   ├── README.md           # Backend documentation
│   └── uploads/            # Voice samples (created automatically)
│
└── Frontend/
    ├── src/
    │   ├── components/     # React components
    │   ├── services/       # API services (chat, tts, voice)
    │   ├── pages/          # Page components
    │   └── App.jsx         # Main app component
    ├── package.json        # Node dependencies
    └── vite.config.js      # Vite configuration
```

## Development Notes

- Backend uses **Python 3.8+** with FastAPI
- Frontend uses **React 19** with Vite
- All API calls are async with proper error handling
- CORS is configured for local development
- Mock responses ensure frontend works independently

