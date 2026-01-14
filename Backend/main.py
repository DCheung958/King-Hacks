from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import shutil
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get ElevenLabs API key from environment
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Initialize ElevenLabs client (only if API key is available)
try:
    from elevenlabs import ElevenLabs
    if ELEVENLABS_API_KEY:
        elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        ELEVENLABS_AVAILABLE = True
    else:
        elevenlabs = None
        ELEVENLABS_AVAILABLE = False
        print("Warning: ELEVENLABS_API_KEY not found in environment. ElevenLabs features will be disabled.")
except ImportError:
    elevenlabs = None
    ELEVENLABS_AVAILABLE = False
    print("Warning: elevenlabs package not installed. Install with: pip install elevenlabs")

# Database imports (optional - gracefully handle if not available)
try:
    from database import database
    from models import users, voice_samples, conversations, messages
    from api_routes import router as api_router
    DB_AVAILABLE = True
except ImportError:
    print("Warning: Database packages not installed. Running in mock mode without database.")
    DB_AVAILABLE = False
    database = None
    api_router = None

app = FastAPI(title="Echocare Backend API", version="1.0.0")

# Include additional API routes if available
if DB_AVAILABLE and api_router:
    app.include_router(api_router)

@app.on_event("startup")
async def startup():
    if DB_AVAILABLE and database:
        try:
            await database.connect()
        except Exception as e:
            print(f"Warning: Could not connect to database: {e}")
            print("Running in mock mode without database.")

@app.on_event("shutdown")
async def shutdown():
    if DB_AVAILABLE and database:
        try:
            await database.disconnect()
        except Exception:
            pass

# Allow CORS for frontend (Vite dev server + production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to temporarily store uploaded voice samples
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Request and Response Models
class EmotionRequest(BaseModel):
    text: str

class EmotionResponse(BaseModel):
    emotion: str
    confidence: float = 0.0

class ResponseRequest(BaseModel):
    text: str
    emotion: Optional[str] = None

class ResponseResponse(BaseModel):
    response_text: str
    emotion: str = "calm"

class SynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None  # For future ElevenLabs integration

class SynthesizeResponse(BaseModel):
    audio_url: str
    duration: Optional[float] = None

class VoiceSampleResponse(BaseModel):
    message: str
    filename: str
    file_size: int
    voice_id: Optional[str] = None  # ElevenLabs voice ID after cloning

# Mock therapeutic responses
THERAPEUTIC_RESPONSES = [
    "I'm really glad you shared that with me. Remember to take deep breaths and take your time.",
    "Thank you for trusting me with this. How are you feeling right now?",
    "That sounds difficult. Remember, you're not alone in this. Let's work through it together.",
    "It's okay to feel this way. Emotions are valid, and we can explore them safely here.",
    "I hear you. Would you like to tell me more about what's on your mind?",
    "Thank you for opening up. Let's take a moment to process this together.",
    "Your feelings are important and valid. We can navigate this step by step.",
]

# Try to import emotion detection model
try:
    from emotion_model import detect_emotion, EMOTION_MODEL_AVAILABLE
    HF_MODEL_AVAILABLE = EMOTION_MODEL_AVAILABLE
except ImportError:
    HF_MODEL_AVAILABLE = False
    print("Warning: emotion_model not available. Using mock emotion detection.")

# Try to import response generation model
try:
    from response_model import generate_therapeutic_response, RESPONSE_MODEL_AVAILABLE
    AI_RESPONSE_AVAILABLE = RESPONSE_MODEL_AVAILABLE
except ImportError:
    AI_RESPONSE_AVAILABLE = False
    print("Warning: response_model not available. Using mock response generation.")

# Mock emotion detection (fallback if Hugging Face model not available)
def mock_detect_emotion(text: str) -> tuple[str, float]:
    """
    Mock emotion detection - fallback when Hugging Face model is not available.
    Returns (emotion, confidence)
    """
    text_lower = text.lower()
    
    # Simple keyword-based detection
    if any(word in text_lower for word in ["sad", "unhappy", "depressed", "down", "upset"]):
        return ("sadness", 0.75)
    elif any(word in text_lower for word in ["anxious", "worried", "nervous", "stress", "afraid"]):
        return ("anxiety", 0.75)
    elif any(word in text_lower for word in ["angry", "mad", "frustrated", "annoyed", "irritated"]):
        return ("anger", 0.75)
    elif any(word in text_lower for word in ["happy", "joy", "excited", "great", "wonderful"]):
        return ("joy", 0.75)
    else:
        return ("calm", 0.65)

@app.get("/")
def root():
    return {
        "message": "Echocare Backend API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "emotion": "/api/emotion",
            "respond": "/api/respond",
            "voice-sample": "/api/voice-sample",
            "synthesize": "/api/synthesize"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "upload_dir_exists": UPLOAD_DIR.exists()}

@app.post("/api/emotion", response_model=EmotionResponse)
async def detect_emotion_endpoint(req: EmotionRequest):
    """
    Detect emotion from user text using Hugging Face model (with fallback to mock)
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Use Hugging Face model if available, otherwise fall back to mock
    try:
        if HF_MODEL_AVAILABLE:
            from emotion_model import detect_emotion
            emotion, confidence = detect_emotion(req.text.strip())
        else:
            emotion, confidence = mock_detect_emotion(req.text.strip())
    except Exception as e:
        # If model fails, fall back to mock
        print(f"Warning: Emotion detection model failed: {e}. Using mock detection.")
        emotion, confidence = mock_detect_emotion(req.text.strip())
    
    return EmotionResponse(
        emotion=emotion,
        confidence=confidence
    )

@app.post("/api/respond", response_model=ResponseResponse)
async def generate_response(
    req: ResponseRequest,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None
):
    """
    Generate empathetic therapeutic response using AI model (with fallback to mock)
    Optionally saves to database if user_id and conversation_id provided
    """
    from db_operations import (
        create_conversation,
        get_conversation_by_id,
        create_message,
    )
    from uuid import UUID
    
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Detect emotion if not provided
    if not req.emotion:
        try:
            if HF_MODEL_AVAILABLE:
                from emotion_model import detect_emotion
                emotion, _ = detect_emotion(req.text.strip())
            else:
                emotion, _ = mock_detect_emotion(req.text.strip())
        except Exception as e:
            print(f"Warning: Emotion detection failed: {e}. Using mock detection.")
            emotion, _ = mock_detect_emotion(req.text.strip())
    else:
        emotion = req.emotion
    
    # Generate response using AI model if available, otherwise use mock
    try:
        if AI_RESPONSE_AVAILABLE:
            from response_model import generate_therapeutic_response
            response_text = generate_therapeutic_response(req.text.strip(), emotion)
        else:
            # Fallback to mock responses
            response_index = len(req.text) % len(THERAPEUTIC_RESPONSES)
            response_text = THERAPEUTIC_RESPONSES[response_index]
    except Exception as e:
        # If AI model fails, fall back to mock
        print(f"Warning: Response generation model failed: {e}. Using mock responses.")
        response_index = len(req.text) % len(THERAPEUTIC_RESPONSES)
        response_text = THERAPEUTIC_RESPONSES[response_index]
    
    # Save to database if user_id provided
    if user_id:
        try:
            user_uuid = UUID(user_id)
            conv_uuid = None
            
            # Get or create conversation
            if conversation_id:
                try:
                    conv_uuid = UUID(conversation_id)
                    # Verify conversation exists
                    conv = await get_conversation_by_id(conv_uuid)
                    if not conv:
                        raise HTTPException(status_code=404, detail="Conversation not found")
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid conversation_id format")
            else:
                # Create new conversation
                conv = await create_conversation(user_uuid)
                conv_uuid = UUID(conv["id"])
            
            # Save user message
            await create_message(
                conversation_id=conv_uuid,
                role="user",
                text=req.text,
                emotion=emotion
            )
            
            # Save assistant response
            await create_message(
                conversation_id=conv_uuid,
                role="assistant",
                text=response_text
            )
        except HTTPException:
            raise
        except Exception as e:
            # Don't fail the request if DB save fails, just log it
            print(f"Warning: Failed to save to database: {e}")
    
    return ResponseResponse(
        response_text=response_text,
        emotion=emotion
    )

@app.post("/api/voice-sample", response_model=VoiceSampleResponse)
async def upload_voice_sample(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Accept uploaded voice sample for voice cloning (MOCKED - will process with ElevenLabs later)
    Supported formats: webm, mp3, wav, ogg
    Optional: user_id to associate with a user
    """
    from db_operations import create_voice_sample
    
    # Validate file type
    allowed_extensions = {".webm", ".mp3", ".wav", ".ogg", ".m4a"}
    
    # Handle case where filename might be None or empty
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File must have a filename"
        )
    
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Generate unique filename
    filename = f"{uuid.uuid4()}{file_extension}"
    filepath = UPLOAD_DIR / filename
    
    # Save uploaded file
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = filepath.stat().st_size
        
        # Clone voice with ElevenLabs if available
        voice_id = None
        if ELEVENLABS_AVAILABLE and elevenlabs:
            try:
                from elevenlabs import Voice, VoiceSettings
                voice = elevenlabs.voices.add(
                    name=f"Echocare Voice {uuid.uuid4()}",
                    files=[str(filepath)]
                )
                voice_id = voice.voice_id
                print(f"Voice cloned successfully. Voice ID: {voice_id}")
            except Exception as e:
                print(f"Warning: Failed to clone voice with ElevenLabs: {e}")
                # Continue without voice_id - file is still saved
        
        # Store record in database if available
        if DB_AVAILABLE:
            try:
                user_uuid = None
                if user_id:
                    try:
                        user_uuid = uuid.UUID(user_id)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid user_id format")
                
                await create_voice_sample(filename=filename, user_id=user_uuid)
            except Exception as e:
                print(f"Warning: Failed to save to database: {e}")
        
        response_message = "Voice sample uploaded and cloned" if voice_id else "Voice sample uploaded successfully"
        
        return VoiceSampleResponse(
            message=response_message,
            filename=filename,
            file_size=file_size,
            voice_id=voice_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.post("/api/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(req: SynthesizeRequest):
    """
    Synthesize speech from text using ElevenLabs TTS
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    if not ELEVENLABS_AVAILABLE or not elevenlabs:
        raise HTTPException(
            status_code=503,
            detail="ElevenLabs API is not configured. Please set ELEVENLABS_API_KEY in environment variables."
        )
    
    if not req.voice_id:
        raise HTTPException(
            status_code=400,
            detail="voice_id is required for speech synthesis"
        )
    
    try:
        # Generate speech using ElevenLabs
        audio = elevenlabs.text_to_speech.convert(
            text=req.text,
            voice_id=req.voice_id,
            model_id="eleven_multilingual_v2"
        )
        
        # Save audio to file
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = UPLOAD_DIR / audio_filename
        
        with open(audio_path, "wb") as f:
            f.write(audio)
        
        # Return URL to the audio file
        audio_url = f"http://localhost:8000/audio/{audio_filename}"
        
        return SynthesizeResponse(
            audio_url=audio_url,
            duration=None  # ElevenLabs doesn't return duration directly
        )
    except Exception as e:
        print(f"Error synthesizing speech: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to synthesize speech: {str(e)}"
        )

@app.get("/api/voice-samples")
async def list_voice_samples():
    """
    List all uploaded voice samples (for debugging/admin)
    """
    samples = []
    if UPLOAD_DIR.exists():
        for filepath in UPLOAD_DIR.iterdir():
            if filepath.is_file():
                samples.append({
                    "filename": filepath.name,
                    "size": filepath.stat().st_size,
                    "created": filepath.stat().st_mtime
                })
    return {"samples": samples, "count": len(samples)}

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """
    Serve generated audio files
    """
    file_path = UPLOAD_DIR / filename
    
    # Security: prevent directory traversal
    if not file_path.resolve().is_relative_to(UPLOAD_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio not found")
    
    # Determine media type based on file extension
    media_type = "audio/mpeg"  # Default to mp3
    if filename.endswith(".wav"):
        media_type = "audio/wav"
    elif filename.endswith(".ogg"):
        media_type = "audio/ogg"
    elif filename.endswith(".webm"):
        media_type = "audio/webm"
    
    return FileResponse(file_path, media_type=media_type)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)