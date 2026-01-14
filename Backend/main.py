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

# Include authentication routes if available
try:
    from auth_routes import router as auth_router
    if DB_AVAILABLE:
        app.include_router(auth_router)
except ImportError:
    print("Warning: auth_routes not available. Authentication endpoints will be disabled.")

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
        except Exception as e:
            print(f"Warning: Error disconnecting from database: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
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
    confidence: float

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
    total_samples: Optional[int] = None  # Total samples for this user
    suggestion: Optional[str] = None  # Suggestion for better voice capture

class BatchVoiceCloneRequest(BaseModel):
    user_id: Optional[str] = None
    voice_name: Optional[str] = None

class BatchVoiceCloneResponse(BaseModel):
    message: str
    voice_id: Optional[str] = None
    filenames: List[str]
    total_samples: int

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
            "voice-clone-batch": "/api/voice-clone-batch",
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

def mock_detect_emotion(text: str) -> tuple[str, float]:
    """
    Mock emotion detection (fallback when model is not available)
    """
    text_lower = text.lower()
    
    # Simple keyword-based emotion detection
    if any(word in text_lower for word in ['anxious', 'anxiety', 'worried', 'worry', 'stress', 'stressed', 'nervous']):
        return ("anxiety", 0.75)
    elif any(word in text_lower for word in ['sad', 'depressed', 'depression', 'down', 'unhappy', 'hopeless']):
        return ("sadness", 0.70)
    elif any(word in text_lower for word in ['angry', 'anger', 'mad', 'furious', 'irritated', 'frustrated']):
        return ("anger", 0.72)
    elif any(word in text_lower for word in ['happy', 'joy', 'excited', 'great', 'wonderful', 'awesome', 'good']):
        return ("joy", 0.68)
    elif any(word in text_lower for word in ['afraid', 'fear', 'scared', 'frightened', 'terrified']):
        return ("fear", 0.73)
    else:
        return ("calm", 0.65)

@app.post("/api/respond", response_model=ResponseResponse)
async def generate_response(
    req: ResponseRequest,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None
):
    """
    Generate empathetic therapeutic response (uses AI model if available, otherwise mock)
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Detect emotion if not provided
    emotion = req.emotion
    if not emotion:
        try:
            if HF_MODEL_AVAILABLE:
                from emotion_model import detect_emotion
                emotion, _ = detect_emotion(req.text.strip())
            else:
                emotion, _ = mock_detect_emotion(req.text.strip())
        except Exception as e:
            print(f"Warning: Emotion detection failed: {e}. Using default emotion.")
            emotion = "calm"
    
    # Get user style context if user_id provided
    user_style = None
    recent_messages = None
    if user_id:
        try:
            from user_style_analyzer import get_user_speech_style, get_recent_user_messages
            user_uuid = uuid.UUID(user_id)
            conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
            user_style = await get_user_speech_style(user_uuid, limit_messages=30)
            recent_messages = await get_recent_user_messages(user_uuid, conv_uuid, limit=3)
        except Exception as e:
            # Don't fail if style analysis fails
            print(f"Warning: Failed to get user style context: {e}")
    
    # Generate response using AI model if available, otherwise use mock
    try:
        if AI_RESPONSE_AVAILABLE:
            from response_model import generate_therapeutic_response
            response_text = generate_therapeutic_response(req.text.strip(), emotion, user_style, recent_messages)
        else:
            # Fallback to mock responses
            response_index = len(req.text) % len(THERAPEUTIC_RESPONSES)
            response_text = THERAPEUTIC_RESPONSES[response_index]
    except Exception as e:
        # If AI model fails, fall back to mock
        print(f"Warning: Response generation model failed: {e}. Using mock responses.")
        response_index = len(req.text) % len(THERAPEUTIC_RESPONSES)
        response_text = THERAPEUTIC_RESPONSES[response_index]
    
    return ResponseResponse(
        response_text=response_text,
        emotion=emotion
    )

# Try to import AI response model
try:
    from response_model import AI_RESPONSE_AVAILABLE
except ImportError:
    AI_RESPONSE_AVAILABLE = False

@app.post("/api/voice-sample", response_model=VoiceSampleResponse)
async def upload_voice_sample(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Accept uploaded voice sample (stores locally, no cloning)
    Cloning is done separately via /api/voice-clone-batch endpoint
    Supports multiple samples to better capture voice style
    Supported formats: webm, mp3, wav, ogg, m4a
    Optional: user_id to associate with a user
    """
    from db_operations import create_voice_sample, get_voice_samples_by_user
    
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
        
        # Store record in database if available
        total_samples = 1
        suggestion = None
        if DB_AVAILABLE:
            try:
                user_uuid = None
                if user_id:
                    try:
                        user_uuid = uuid.UUID(user_id)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid user_id format")
                
                await create_voice_sample(filename=filename, user_id=user_uuid)
                
                # Get total samples count for user feedback
                if user_uuid:
                    try:
                        from db_operations import get_voice_samples_by_user
                        samples = await get_voice_samples_by_user(user_uuid)
                        total_samples = len(samples)
                        
                        # Provide suggestions based on sample count
                        if total_samples == 1:
                            suggestion = "Great start! Upload 2-3 more varied samples (different emotions, topics) for better voice capture."
                        elif total_samples == 2:
                            suggestion = "Good progress! One more sample with varied tone would help capture your full voice style."
                        elif total_samples < 5:
                            suggestion = f"Excellent! You have {total_samples} samples. Add a few more with different emotions for best results."
                        else:
                            suggestion = "Perfect! You have enough samples for great voice emulation."
                    except Exception as e:
                        print(f"Warning: Failed to get sample count: {e}")
            except Exception as e:
                print(f"Warning: Failed to save to database: {e}")
        
        response_message = "Voice sample uploaded successfully"
        if total_samples > 1:
            response_message += f" ({total_samples} total samples)"
        
        return VoiceSampleResponse(
            message=response_message,
            filename=filename,
            file_size=file_size,
            voice_id=None,  # No cloning on individual upload
            total_samples=total_samples,
            suggestion=suggestion
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.post("/api/voice-clone-batch", response_model=BatchVoiceCloneResponse)
async def batch_clone_voice(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Form(None),
    voice_name: Optional[str] = Form(None)
):
    """
    Batch upload and clone voice samples with ElevenLabs (saves credits by cloning once)
    Accepts multiple files and clones them together into a single voice
    Supported formats: webm, mp3, wav, ogg, m4a
    """
    from db_operations import create_voice_sample, get_voice_samples_by_user
    
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file is required")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per batch")
    
    # Validate file types and save files
    allowed_extensions = {".webm", ".mp3", ".wav", ".ogg", ".m4a"}
    saved_files = []
    saved_filenames = []
    
    try:
        user_uuid = None
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid user_id format")
        
        # Save all files first
        for file in files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="All files must have filenames")
            
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_extension}. Allowed: {', '.join(allowed_extensions)}"
                )
            
            filename = f"{uuid.uuid4()}{file_extension}"
            filepath = UPLOAD_DIR / filename
            
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_files.append(filepath)
            saved_filenames.append(filename)
            
            # Store record in database if available
            if DB_AVAILABLE:
                try:
                    await create_voice_sample(filename=filename, user_id=user_uuid)
                except Exception as e:
                    print(f"Warning: Failed to save sample to database: {e}")
        
        # Clone voice with ElevenLabs if available (single clone operation with all files)
        voice_id = None
        if ELEVENLABS_AVAILABLE and elevenlabs:
            try:
                # Use the correct ElevenLabs API method for voice cloning
                # The correct method is voices.clone() with files parameter
                voice_name_final = voice_name or f"Echocare Voice {uuid.uuid4()}"
                
                # Convert file paths to file objects for ElevenLabs API
                file_objects = []
                for filepath in saved_files:
                    with open(filepath, 'rb') as f:
                        file_objects.append(f.read())
                
                # Clone voice using ElevenLabs API (Instant Voice Cloning)
                # The correct method is voices.ivc.create() for Instant Voice Cloning
                try:
                    from io import BytesIO
                    # Convert bytes to BytesIO objects for ElevenLabs API
                    file_io_objects = [BytesIO(f) for f in file_objects]
                    
                    # Use Instant Voice Cloning (IVC) API
                    voice = elevenlabs.voices.ivc.create(
                        name=voice_name_final,
                        files=file_io_objects
                    )
                    voice_id = voice.voice_id if hasattr(voice, 'voice_id') else str(voice)
                except AttributeError:
                    # Fallback: Try alternative API methods if IVC doesn't exist
                    try:
                        # Try voices.clone() as fallback
                        voice = elevenlabs.voices.clone(
                            name=voice_name_final,
                            files=file_objects
                        )
                        voice_id = voice.voice_id if hasattr(voice, 'voice_id') else str(voice)
                    except (AttributeError, TypeError) as e:
                        print(f"Warning: ElevenLabs voice cloning API method not found: {e}")
                        print(f"Note: Please check ElevenLabs SDK documentation for correct cloning method")
                        voice_id = None
                except Exception as e:
                    print(f"Warning: ElevenLabs voice cloning failed: {e}")
                    print(f"Error details: {type(e).__name__}: {str(e)}")
                    voice_id = None
                
                if voice_id:
                    print(f"Voice cloned successfully with {len(saved_files)} samples. Voice ID: {voice_id}")
            except Exception as e:
                print(f"Warning: Failed to clone voice with ElevenLabs: {e}")
                print(f"Error details: {type(e).__name__}: {str(e)}")
                # Continue without voice_id - files are still saved
        
        # Get total samples count for user feedback
        total_samples = len(saved_filenames)
        if DB_AVAILABLE and user_uuid:
            try:
                from db_operations import get_voice_samples_by_user
                samples = await get_voice_samples_by_user(user_uuid)
                total_samples = len(samples)
            except Exception as e:
                print(f"Warning: Failed to get sample count: {e}")
        
        message = f"Successfully uploaded {len(saved_filenames)} voice sample(s)"
        if voice_id:
            message += f" and cloned voice (ID: {voice_id})"
        
        return BatchVoiceCloneResponse(
            message=message,
            voice_id=voice_id,
            filenames=saved_filenames,
            total_samples=total_samples
        )
    
    except HTTPException:
        # Clean up saved files on error
        for filepath in saved_files:
            try:
                if filepath.exists():
                    filepath.unlink()
            except Exception:
                pass
        raise
    except Exception as e:
        # Clean up saved files on error
        for filepath in saved_files:
            try:
                if filepath.exists():
                    filepath.unlink()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Error processing batch upload: {str(e)}")

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
    if filename.endswith(".webm"):
        media_type = "audio/webm"
    elif filename.endswith(".wav"):
        media_type = "audio/wav"
    elif filename.endswith(".ogg"):
        media_type = "audio/ogg"
    elif filename.endswith(".m4a"):
        media_type = "audio/mp4"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
