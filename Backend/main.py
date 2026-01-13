from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import uuid
import shutil
import os
from pathlib import Path
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

# Mock emotion detection (simple keyword-based for now)
def mock_detect_emotion(text: str) -> tuple[str, float]:
    """
    Mock emotion detection - will be replaced with Hugging Face model later.
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
async def detect_emotion(req: EmotionRequest):
    """
    Detect emotion from user text (MOCKED - will use Hugging Face model later)
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    emotion, confidence = mock_detect_emotion(req.text)
    
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
    Generate empathetic therapeutic response (MOCKED - will use AI model later)
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
    emotion, _ = mock_detect_emotion(req.text) if not req.emotion else (req.emotion, 0.7)
    
    # Select response based on text length (simple mock)
    response_index = len(req.text) % len(THERAPEUTIC_RESPONSES)
    response_text = THERAPEUTIC_RESPONSES[response_index]
    
    # Save to database if user_id provided and DB is available
    if user_id and DB_AVAILABLE:
        try:
            from db_operations import (
                create_conversation,
                get_conversation_by_id,
                create_message,
            )
            from uuid import UUID
            
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
    # Validate file type
    allowed_extensions = {".webm", ".mp3", ".wav", ".ogg", ".m4a"}
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
        if DB_AVAILABLE:
            try:
                from db_operations import create_voice_sample
                user_uuid = None
                if user_id:
                    try:
                        user_uuid = uuid.UUID(user_id)
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid user_id format")
                
                await create_voice_sample(filename=filename, user_id=user_uuid)
            except Exception as e:
                print(f"Warning: Failed to save to database: {e}")
        
        # In real implementation, this file would be sent to ElevenLabs for voice cloning
        # For now, we just store it and acknowledge
        
        return VoiceSampleResponse(
            message="Voice sample uploaded successfully",
            filename=filename,
            file_size=file_size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.post("/api/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(req: SynthesizeRequest):
    """
    Synthesize speech from text (MOCKED - will call ElevenLabs API later)
    Returns a mock audio URL for now
    """
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # MOCKED: Return a sample audio URL
    # In production, this will:
    # 1. Call ElevenLabs API with the text and voice_id
    # 2. Receive the generated audio
    # 3. Store it or return a signed URL
    # 4. Return the audio_url and duration
    
    # Using a free sample audio URL for testing
    # In production, this would be your own hosted audio or ElevenLabs CDN URL
    audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    
    # Mock duration based on text length (average speaking rate: ~150 words/min)
    word_count = len(req.text.split())
    estimated_duration = (word_count / 150) * 60  # in seconds
    
    return SynthesizeResponse(
        audio_url=audio_url,
        duration=estimated_duration
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)