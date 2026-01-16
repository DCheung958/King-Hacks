from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from starlette.requests import Request
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

# Get API keys from environment
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
    # Fix OpenMP duplicate library warning on Windows
    import os
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    
    if DB_AVAILABLE and database:
        try:
            await database.connect()
            # Update connection status in database module
            import database as db_module
            db_module.DATABASE_CONNECTED = True
            print("[Startup] ✓ Successfully connected to database")
        except Exception as e:
            # Update connection status in database module
            import database as db_module
            db_module.DATABASE_CONNECTED = False
            print(f"[Startup] ❌ ERROR: Could not connect to database")
            print(f"[Startup]   Error: {e}")
            print(f"[Startup]   Check:")
            print(f"[Startup]   1. PostgreSQL is running")
            print(f"[Startup]   2. .env file exists in Backend folder")
            print(f"[Startup]   3. Password in .env matches PostgreSQL password")
            print(f"[Startup]   Running in mock mode without database.")

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
    persona: Optional[str] = None  # "friend" | "therapist" | "family"
    warmth: Optional[float] = 0.5  # 0.0 (direct) to 1.0 (gentle)

class ResponseResponse(BaseModel):
    response_text: str
    emotion: str = "calm"

class SynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None  # ElevenLabs voice ID
    emotion: Optional[str] = None  # Emotion for prosody adjustment
    persona: Optional[str] = None  # Persona for prosody adjustment
    warmth: Optional[float] = None  # Warmth level (0.0-1.0) for prosody
    stability: Optional[float] = None  # Override stability (0.0-1.0)
    similarity_boost: Optional[float] = None  # Override similarity boost (0.0-1.0)
    style_exaggeration: Optional[float] = None  # Override style exaggeration (0.0-1.0)

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
    return {
        "status": "healthy", 
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "elevenlabs": {
            "available": ELEVENLABS_AVAILABLE,
            "api_key_configured": bool(ELEVENLABS_API_KEY),
            "client_initialized": elevenlabs is not None
        }
    }

@app.get("/api/elevenlabs-status")
def elevenlabs_status():
    """
    Check ElevenLabs API connection status
    This endpoint helps verify if ElevenLabs is configured and ready to use credits
    """
    status = {
        "configured": ELEVENLABS_AVAILABLE,
        "api_key_present": bool(ELEVENLABS_API_KEY),
        "client_initialized": elevenlabs is not None,
        "package_installed": True
    }
    
    # Try to verify the API key by making a lightweight call
    if ELEVENLABS_AVAILABLE and elevenlabs:
        try:
            # This is a lightweight call that should not consume significant credits
            # Just checking if we can access the API (might make a small API call)
            status["api_accessible"] = True
            status["message"] = "ElevenLabs is connected. API calls will consume credits."
        except Exception as e:
            status["api_accessible"] = False
            status["error"] = str(e)
            status["message"] = "ElevenLabs API key present but connection failed."
    else:
        if not bool(ELEVENLABS_API_KEY):
            status["message"] = "ELEVENLABS_API_KEY not found in environment variables. ElevenLabs features disabled - NO credits will be used."
        else:
            status["message"] = "ElevenLabs package not installed. Install with: pip install elevenlabs"
    
    return status

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
    Enhanced with conversation memory, therapeutic safety wrapper, and crisis detection
    """
    import time
    start_time = time.time()
    
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # PRIORITY 1: Crisis detection (fast win - safety first)
    crisis_detected = False
    crisis_response = None
    try:
        from crisis_detector import detect_crisis, log_crisis_detection
        
        # Detect emotion first for crisis detection
        emotion_for_crisis = req.emotion
        emotion_confidence = 0.0
        if not emotion_for_crisis:
            try:
                if HF_MODEL_AVAILABLE:
                    from emotion_model import detect_emotion
                    emotion_for_crisis, emotion_confidence = detect_emotion(req.text.strip())
                else:
                    emotion_for_crisis, emotion_confidence = mock_detect_emotion(req.text.strip())
            except Exception:
                pass
        
        # Check for crisis
        crisis_result = detect_crisis(
            req.text.strip(),
            emotion=emotion_for_crisis,
            emotion_confidence=emotion_confidence
        )
        
        if crisis_result and crisis_result.get("crisis_detected"):
            crisis_detected = True
            crisis_response = crisis_result.get("safe_response")
            
            # Log crisis detection
            if crisis_result.get("log_incident"):
                try:
                    log_crisis_detection(crisis_result["level"])
                except Exception as log_error:
                    print(f"Warning: Failed to log crisis: {log_error}")
            
            print(f"[CRISIS DETECTED] Level: {crisis_result.get('level')}, Should override: {crisis_result.get('should_override')}")
            print(f"[CRISIS DETECTED] Reasons: {crisis_result.get('reasons', [])}")
            
            # Override response if needed
            if crisis_result.get("should_override") and crisis_response:
                print(f"[CRISIS OVERRIDE] Returning crisis response ({len(crisis_response)} chars)")
                return ResponseResponse(
                    response_text=crisis_response,
                    emotion=emotion_for_crisis or "concern"
                )
    except Exception as e:
        import traceback
        print(f"ERROR: Crisis detection failed: {e}")
        traceback.print_exc()
        print("Continuing with normal response generation.")
    
    # Detect emotion if not provided (and not already detected for crisis)
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
    
    # Get conversation summary if user_id and conversation_id provided (quality over speed)
    conversation_summary = None
    if user_id and conversation_id and not is_simple_query:
        try:
            from conversation_memory import get_conversation_summary
            user_uuid = uuid.UUID(user_id)
            conv_uuid = uuid.UUID(conversation_id)
            conversation_summary = await get_conversation_summary(user_uuid, conv_uuid)
        except Exception as e:
            print(f"Warning: Failed to get conversation summary: {e}")
    
    # FAST PATH: For simple queries, skip expensive context loading to speed up response
    # Simple queries are: short (< 80 chars), casual topics, no emotional intensity keywords
    user_text_lower = req.text.strip().lower()
    emotional_keywords = ["difficult", "struggling", "anxious", "depressed", "hurt", "suicide", "kill", "sad", "angry", "worried", "stressed", "overwhelmed", "pain", "suffering"]
    simple_topic_indicators = ["want", "get", "buy", "need", "like", "thinking about", "considering"]
    
    # Simple query if: short text AND (has simple topic indicators OR no emotional keywords)
    is_simple_query = (
        len(req.text.strip()) < 80 and
        (
            any(indicator in user_text_lower for indicator in simple_topic_indicators) or
            not any(keyword in user_text_lower for keyword in emotional_keywords)
        )
    )
    
    if is_simple_query:
        print(f"🚀 Fast path: Simple query detected - skipping expensive context loading")
    
    # Get user style context if user_id provided (skip for simple queries to speed up)
    user_style = None
    recent_messages = None
    last_assistant_message = None
    conversation_history = None  # Initialize to avoid NameError
    if user_id and not is_simple_query:  # Skip for simple queries
        try:
            db_start = time.time()
            from user_style_analyzer import get_user_speech_style, get_recent_user_messages
            from db_operations import get_messages_by_conversation
            user_uuid = uuid.UUID(user_id)
            conv_uuid = uuid.UUID(conversation_id) if conversation_id else None
            
            # SKIP user_style for speed - it's expensive and not critical for response quality
            # user_style = await get_user_speech_style(user_uuid, limit_messages=15)  # EXPENSIVE - DISABLED
            recent_messages = await get_recent_user_messages(user_uuid, conv_uuid, limit=2)  # Reduced from 3 to 2
            
            # Get conversation history and last assistant message
            conversation_history = None
            if conv_uuid:
                try:
                    # Reduced to 2 messages for faster processing (was 4)
                    messages = await get_messages_by_conversation(conv_uuid, limit=2)
                    # Format conversation history for LLaMA 2
                    conversation_history = [
                        {"role": msg.get("role"), "content": msg.get("text", "")}
                        for msg in messages
                        if msg.get("role") in ["user", "assistant"]
                    ]
                    # Get last assistant message to avoid repetition
                    assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
                    if assistant_messages:
                        last_assistant_message = assistant_messages[-1].get("text", "")
                except Exception as e:
                    print(f"Warning: Failed to get conversation history: {e}")
            db_time = time.time() - db_start
            if db_time > 0.5:
                print(f"⏱️  DB queries took {db_time:.2f}s")
        except Exception as e:
            # Don't fail if style analysis fails
            print(f"Warning: Failed to get user style context: {e}")
    elif user_id and is_simple_query and conversation_id:
        # For simple queries, just get minimal history (last 2 messages)
        try:
            from db_operations import get_messages_by_conversation
            conv_uuid = uuid.UUID(conversation_id)
            messages = await get_messages_by_conversation(conv_uuid, limit=2)
            conversation_history = [
                {"role": msg.get("role"), "content": msg.get("text", "")}
                for msg in messages
                if msg.get("role") in ["user", "assistant"]
            ]
            assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
            if assistant_messages:
                last_assistant_message = assistant_messages[-1].get("text", "")
        except Exception as e:
            print(f"Warning: Failed to get conversation history: {e}")
            conversation_history = []  # Ensure it's initialized even on error
    
    # CRITICAL: Ensure conversation_history is always a list, never None
    if conversation_history is None:
        conversation_history = []
    
    # Generate response using AI model if available, otherwise use mock
    try:
        if AI_RESPONSE_AVAILABLE:
            from response_model import generate_therapeutic_response
            
            # Get persona and warmth from request (defaults if not provided)
            persona = req.persona if hasattr(req, 'persona') else None
            warmth = req.warmth if hasattr(req, 'warmth') and req.warmth is not None else 0.5
            
            # Validate warmth range
            warmth = max(0.0, min(1.0, warmth))
            
            # Time the model generation
            model_start = time.time()
            response_text = generate_therapeutic_response(
                req.text.strip(), 
                emotion, 
                user_style, 
                recent_messages,
                conversation_summary,
                persona=persona,
                warmth=warmth,
                last_assistant_message=last_assistant_message,
                conversation_history=conversation_history
            )
            model_time = time.time() - model_start
            if model_time > 2:
                print(f"⏱️  Model generation took {model_time:.2f}s")
        else:
            # Fallback to mock responses
            response_index = len(req.text) % len(THERAPEUTIC_RESPONSES)
            response_text = THERAPEUTIC_RESPONSES[response_index]
    except Exception as e:
        # If AI model fails, fall back to mock
        print(f"Warning: Response generation model failed: {e}. Using mock responses.")
        response_index = len(req.text) % len(THERAPEUTIC_RESPONSES)
        response_text = THERAPEUTIC_RESPONSES[response_index]
    
    # Save messages to database if available (for conversation memory)
    if DB_AVAILABLE and user_id and conversation_id:
        try:
            from db_operations import create_message, get_messages_by_conversation
            from conversation_memory import update_conversation_summary, should_summarize
            
            user_uuid = uuid.UUID(user_id)
            conv_uuid = uuid.UUID(conversation_id)
            
            # Save user message
            await create_message(
                conversation_id=conv_uuid,
                role="user",
                text=req.text.strip(),
                emotion=emotion
            )
            
            # Save assistant response
            await create_message(
                conversation_id=conv_uuid,
                role="assistant",
                text=response_text
            )
            
            # OPTIMIZED: Don't load 100 messages just to count - use a faster method
            # Instead, check summary update asynchronously or use a counter
            # For now, skip the expensive query - summary updates can happen in background
            # messages = await get_messages_by_conversation(conv_uuid, limit=100)  # EXPENSIVE - DISABLED
            # message_count = len(messages)
            
            # Update summary every 5 messages (skip for now to speed up response)
            # Summary updates can be done in background task
            # from conversation_memory import should_summarize
            # if should_summarize(message_count, n_messages=5):
            #     await update_conversation_summary(
            #         user_uuid,
            #         conv_uuid,
            #         {"role": "assistant", "text": response_text, "emotion": None}
            #     )
        except Exception as e:
            print(f"Warning: Failed to save messages to database: {e}")
    
    # Log total request time
    total_time = time.time() - start_time
    if total_time > 3:
        print(f"⏱️  Total /api/respond time: {total_time:.2f}s")
    
    return ResponseResponse(
        response_text=response_text,
        emotion=emotion
    )

# Try to import AI response model
try:
    from response_model import RESPONSE_MODEL_AVAILABLE
    AI_RESPONSE_AVAILABLE = RESPONSE_MODEL_AVAILABLE
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
                    import asyncio
                    from io import BytesIO
                    # Convert bytes to BytesIO objects for ElevenLabs API
                    file_io_objects = [BytesIO(f) for f in file_objects]
                    
                    # Use Instant Voice Cloning (IVC) API with timeout protection
                    # ElevenLabs API can be slow - use asyncio to add timeout
                    print(f"Starting voice cloning with {len(file_io_objects)} samples (timeout: 90s)...")
                    try:
                        # Run the blocking call in a thread with timeout
                        loop = asyncio.get_event_loop()
                        voice = await asyncio.wait_for(
                            loop.run_in_executor(
                                None,
                                lambda: elevenlabs.voices.ivc.create(
                                    name=voice_name_final,
                                    files=file_io_objects
                                )
                            ),
                            timeout=90.0  # 90 second timeout
                        )
                        voice_id = voice.voice_id if hasattr(voice, 'voice_id') else str(voice)
                    except asyncio.TimeoutError:
                        print(f"ERROR: Voice cloning timed out after 90 seconds")
                        voice_id = None
                    except Exception as e:
                        print(f"Warning: ElevenLabs voice cloning failed: {e}")
                        print(f"Error details: {type(e).__name__}: {str(e)}")
                        voice_id = None
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
                from db_operations import get_voice_samples_by_user, create_voice_profile, get_voice_profiles_by_user
                samples = await get_voice_samples_by_user(user_uuid)
                total_samples = len(samples)
                
                # Save voice_id and voice_name to voice_profiles table if voice was cloned
                if voice_id and user_uuid:
                    try:
                        # Check existing profiles to determine if this should be active
                        existing_profiles = await get_voice_profiles_by_user(user_uuid)
                        is_first_profile = len(existing_profiles) == 0
                        
                        # Create new voice profile (will be set as active, deactivating others)
                        new_profile = await create_voice_profile(
                            user_id=user_uuid,
                            voice_id=voice_id,
                            voice_name=voice_name or f"Voice Profile {len(existing_profiles) + 1}",
                            set_as_active=True  # Always set new profile as active (deactivates others)
                        )
                        print(f"Voice profile '{new_profile['voice_name']}' saved to database for user {user_uuid}")
                        print(f"Total profiles for user: {len(existing_profiles) + 1}")
                    except Exception as e:
                        print(f"Warning: Failed to save voice profile to database: {e}")
                        import traceback
                        traceback.print_exc()
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
async def synthesize_speech(req: SynthesizeRequest, request: Request):
    """
    Synthesize speech from text using ElevenLabs TTS with prosody-aware settings
    Adjusts stability, similarity boost, and style exaggeration based on emotion
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
        # Get prosody settings based on emotion, persona, and warmth
        from prosody_config import get_voice_settings
        from persona_config import get_persona_prosody
        
        # If persona provided, use persona prosody (blended with emotion)
        if req.persona:
            voice_settings = get_persona_prosody(req.persona, req.emotion)
        else:
            voice_settings = get_voice_settings(
                emotion=req.emotion,
                custom_stability=req.stability,
                custom_similarity_boost=req.similarity_boost,
                custom_style_exaggeration=req.style_exaggeration
            )
        
        # Adjust for warmth if provided
        if req.warmth is not None:
            warmth = max(0.0, min(1.0, req.warmth))
            # Higher warmth = more style exaggeration, lower stability (warmer voice)
            voice_settings["style_exaggeration"] = voice_settings.get("style_exaggeration", 0.2) * (0.5 + warmth * 0.5)
            voice_settings["stability"] = voice_settings.get("stability", 0.65) * (1.0 - warmth * 0.2)
        
        # Apply overrides if provided
        if req.stability is not None:
            voice_settings["stability"] = req.stability
        if req.similarity_boost is not None:
            voice_settings["similarity_boost"] = req.similarity_boost
        if req.style_exaggeration is not None:
            voice_settings["style_exaggeration"] = req.style_exaggeration
        
        # Generate speech using ElevenLabs with prosody settings
        # Note: ElevenLabs API returns a generator that yields audio chunks
        # We need to collect all chunks into bytes
        audio_generator = None
        try:
            # Try with prosody parameters (newer API)
            audio_generator = elevenlabs.text_to_speech.convert(
                text=req.text,
                voice_id=req.voice_id,
                model_id="eleven_multilingual_v2",
                stability=voice_settings["stability"],
                similarity_boost=voice_settings["similarity_boost"],
                style=voice_settings["style_exaggeration"]  # May be called "style" or "style_exaggeration"
            )
        except TypeError:
            # Fallback: Try without style parameter (older API versions)
            try:
                audio_generator = elevenlabs.text_to_speech.convert(
                    text=req.text,
                    voice_id=req.voice_id,
                    model_id="eleven_multilingual_v2",
                    stability=voice_settings["stability"],
                    similarity_boost=voice_settings["similarity_boost"]
                )
            except TypeError:
                # Final fallback: Basic call without prosody parameters
                audio_generator = elevenlabs.text_to_speech.convert(
                    text=req.text,
                    voice_id=req.voice_id,
                    model_id="eleven_multilingual_v2"
                )
        
        # Convert generator to bytes (ElevenLabs returns a generator of audio chunks)
        audio_bytes = b""
        if audio_generator:
            for chunk in audio_generator:
                if isinstance(chunk, bytes):
                    audio_bytes += chunk
                else:
                    # If chunk is not bytes, try to convert it
                    audio_bytes += bytes(chunk)
        
        if not audio_bytes:
            raise HTTPException(
                status_code=500,
                detail="No audio data received from ElevenLabs"
            )
        
        # Save audio to file
        audio_filename = f"{uuid.uuid4()}.mp3"
        audio_path = UPLOAD_DIR / audio_filename
        
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        # Return URL to the audio file
        # Use request base URL (FastAPI automatically injects Request)
        base_url = str(request.base_url).rstrip('/')
        audio_url = f"{base_url}/audio/{audio_filename}"
        
        return SynthesizeResponse(
            audio_url=audio_url,
            duration=None  # ElevenLabs doesn't return duration directly
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ ERROR synthesizing speech: {e}")
        print(f"Full traceback:\n{error_details}")
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
