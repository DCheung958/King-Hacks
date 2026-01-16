"""
Additional API routes for database operations
Endpoints for managing users, conversations, and retrieving history
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from db_operations import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    get_or_create_user,
    create_conversation,
    get_conversations_by_user,
    get_conversation_by_id,
    get_messages_by_conversation,
    get_voice_samples_by_user,
    get_voice_profiles_by_user,
    get_active_voice_profile,
    set_active_voice_profile,
    delete_voice_profile,
)

router = APIRouter(prefix="/api", tags=["database"])


# Request/Response Models
class UserCreate(BaseModel):
    email: str
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    created_at: str

class ConversationResponse(BaseModel):
    id: str
    user_id: str
    created_at: str

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    text: str
    emotion: Optional[str] = None
    timestamp: str

class ConversationHistoryResponse(BaseModel):
    conversation: ConversationResponse
    messages: List[MessageResponse]


# User endpoints
@router.post("/users", response_model=UserResponse)
async def create_user_endpoint(user: UserCreate):
    """Create a new user"""
    try:
        result = await create_user(email=user.email, name=user.name)
        return UserResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating user: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user_endpoint(user_id: str):
    """Get user by ID"""
    try:
        user_uuid = UUID(user_id)
        user = await get_user_by_id(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(**user)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@router.get("/users/email/{email}", response_model=UserResponse)
async def get_user_by_email_endpoint(email: str):
    """Get user by email"""
    try:
        user = await get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(**user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


# Conversation endpoints
@router.post("/users/{user_id}/conversations", response_model=ConversationResponse)
async def create_user_conversation(user_id: str):
    """Create a new conversation for a user"""
    try:
        user_uuid = UUID(user_id)
        # Verify user exists
        user = await get_user_by_id(user_uuid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create conversation
        conv = await create_conversation(user_uuid)
        return ConversationResponse(**conv)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

@router.get("/users/{user_id}/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(user_id: str, limit: int = 50):
    """Get all conversations for a user"""
    try:
        user_uuid = UUID(user_id)
        convs = await get_conversations_by_user(user_uuid, limit=limit)
        return [ConversationResponse(**conv) for conv in convs]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_endpoint(conversation_id: str):
    """Get conversation by ID"""
    try:
        conv_uuid = UUID(conversation_id)
        conv = await get_conversation_by_id(conv_uuid)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return ConversationResponse(**conv)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversation: {str(e)}")


# Message endpoints
@router.get("/conversations/{conversation_id}/messages", response_model=ConversationHistoryResponse)
async def get_conversation_messages(conversation_id: str, limit: int = 100):
    """Get all messages for a conversation (conversation history)"""
    try:
        conv_uuid = UUID(conversation_id)
        
        # Get conversation
        conv = await get_conversation_by_id(conv_uuid)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        msgs = await get_messages_by_conversation(conv_uuid, limit=limit)
        
        return ConversationHistoryResponse(
            conversation=ConversationResponse(**conv),
            messages=[MessageResponse(**msg) for msg in msgs]
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation_id format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")


# Voice sample endpoints
@router.get("/users/{user_id}/voice-samples")
async def get_user_voice_samples(user_id: str):
    """Get all voice samples for a user"""
    try:
        user_uuid = UUID(user_id)
        samples = await get_voice_samples_by_user(user_uuid)
        return {"samples": samples, "count": len(samples)}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching voice samples: {str(e)}")


# Voice profile endpoints
class VoiceProfileResponse(BaseModel):
    id: str
    user_id: str
    voice_id: str
    voice_name: str
    is_active: bool
    created_at: str

@router.get("/users/{user_id}/voice-profiles", response_model=List[VoiceProfileResponse])
async def get_user_voice_profiles(user_id: str):
    """Get all voice profiles for a user"""
    try:
        user_uuid = UUID(user_id)
        profiles = await get_voice_profiles_by_user(user_uuid)
        return [VoiceProfileResponse(**profile) for profile in profiles]
    except ValueError as ve:
        print(f"ERROR: Invalid user_id format '{user_id}': {ve}")
        raise HTTPException(status_code=400, detail=f"Invalid user_id format: {str(ve)}")
    except Exception as e:
        print(f"ERROR: Failed to fetch voice profiles for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching voice profiles: {str(e)}")

@router.get("/users/{user_id}/voice-profiles/active", response_model=VoiceProfileResponse)
async def get_active_user_voice_profile(user_id: str):
    """Get the active voice profile for a user"""
    try:
        user_uuid = UUID(user_id)
        profile = await get_active_voice_profile(user_uuid)
        if not profile:
            raise HTTPException(status_code=404, detail="No active voice profile found")
        return VoiceProfileResponse(**profile)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching active voice profile: {str(e)}")

@router.post("/users/{user_id}/voice-profiles/{profile_id}/activate", response_model=VoiceProfileResponse)
async def activate_voice_profile(user_id: str, profile_id: str):
    """Set a voice profile as active for a user"""
    try:
        user_uuid = UUID(user_id)
        profile_uuid = UUID(profile_id)
        profile = await set_active_voice_profile(user_uuid, profile_uuid)
        # Ensure UUID fields are strings for Pydantic model
        if isinstance(profile.get('id'), UUID):
            profile['id'] = str(profile['id'])
        if isinstance(profile.get('user_id'), UUID):
            profile['user_id'] = str(profile['user_id'])
        if 'created_at' in profile and hasattr(profile['created_at'], 'isoformat'):
            profile['created_at'] = profile['created_at'].isoformat()
        return VoiceProfileResponse(**profile)
    except ValueError as ve:
        print(f"ERROR: Invalid UUID format - user_id: '{user_id}', profile_id: '{profile_id}': {ve}")
        raise HTTPException(status_code=400, detail=f"Invalid user_id or profile_id format: {str(ve)}")
    except Exception as e:
        print(f"ERROR: Failed to activate voice profile {profile_id} for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error activating voice profile: {str(e)}")

@router.delete("/users/{user_id}/voice-profiles/{profile_id}")
async def delete_user_voice_profile(user_id: str, profile_id: str):
    """Delete a voice profile for a user"""
    try:
        user_uuid = UUID(user_id)
        profile_uuid = UUID(profile_id)
        deleted = await delete_voice_profile(user_uuid, profile_uuid)
        if not deleted:
            raise HTTPException(status_code=404, detail="Voice profile not found")
        return {"message": "Voice profile deleted successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id or profile_id format")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting voice profile: {str(e)}")

