# Echocare Backend API

FastAPI backend for the Echocare therapeutic conversation application. Currently uses mocked endpoints for emotion detection, response generation, and speech synthesis (ready for ElevenLabs integration).

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the development server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or simply:
   ```bash
   python main.py
   ```

3. **Access the API:**
   - API Base: `http://localhost:8000`
   - Interactive Docs (Swagger): `http://localhost:8000/docs`
   - Alternative Docs (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### `GET /`
Health check and API information.

### `GET /health`
Detailed health check.

### `POST /api/emotion`
Detect emotion from user text (MOCKED - will use Hugging Face model later).

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
Generate empathetic therapeutic response (MOCKED - will use AI model later).

**Request:**
```json
{
  "text": "I'm struggling with work stress",
  "emotion": "anxiety"  // optional
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
Upload voice sample for voice cloning (MOCKED - will process with ElevenLabs later).

**Request:** Multipart form data with audio file (webm, mp3, wav, ogg, m4a)

**Response:**
```json
{
  "message": "Voice sample uploaded successfully",
  "filename": "uuid-filename.webm",
  "file_size": 12345
}
```

### `POST /api/synthesize`
Synthesize speech from text (MOCKED - will call ElevenLabs API later).

**Request:**
```json
{
  "text": "I'm here to help you",
  "voice_id": "optional-voice-id"  // for future ElevenLabs integration
}
```

**Response:**
```json
{
  "audio_url": "https://example.com/audio.mp3",
  "duration": 2.5
}
```

### `GET /api/voice-samples`
List all uploaded voice samples (for debugging/admin).

## Mock Implementation Notes

- **Emotion Detection**: Currently uses simple keyword-based detection. Will be replaced with Hugging Face emotion classification model.
- **Response Generation**: Uses predefined therapeutic responses rotated based on input. Will be replaced with AI model (e.g., GPT-based therapy assistant).
- **Voice Synthesis**: Returns a static sample audio URL. Will be replaced with ElevenLabs API integration.
- **Voice Cloning**: Accepts and stores uploaded samples. Will be processed with ElevenLabs for voice cloning.

## File Structure

```
Backend/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore rules
├── README.md           # This file
└── uploads/            # Voice sample uploads (created automatically, gitignored)
```

## CORS Configuration

The backend is configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative dev port)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

Update the `allow_origins` list in `main.py` to add production frontend URLs.

## Future Integration Points

1. **ElevenLabs API**: 
   - Replace `/api/synthesize` with actual ElevenLabs TTS call
   - Process uploaded voice samples for cloning
   - Store voice IDs and audio URLs

2. **Hugging Face Model**:
   - Integrate emotion classification model in `/api/emotion`
   - Use transformers library for inference

3. **AI Response Generation**:
   - Replace mock responses with GPT-based therapy assistant
   - Use OpenAI API or local LLM

4. **Audio Storage**:
   - Store generated audio files
   - Use cloud storage (S3, Cloudinary) or CDN
   - Implement signed URLs for secure access

