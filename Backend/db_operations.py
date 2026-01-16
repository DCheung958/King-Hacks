"""
Database CRUD Operations for Echocare
Provides functions to interact with the database tables
"""

from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from database import database
from models import users, voice_samples, voice_profiles, conversations, messages


# ========== USER OPERATIONS ==========

async def create_user(email: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Create a new user"""
    user_id = uuid4()
    query = users.insert().values(
        id=user_id,
        email=email,
        name=name,
        created_at=datetime.utcnow()
    )
    await database.execute(query)
    return {"id": str(user_id), "email": email, "name": name}


async def create_user_with_password(
    email: str, 
    password_hash: str, 
    name: Optional[str] = None,
    username: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new user with password"""
    user_id = uuid4()
    query = users.insert().values(
        id=user_id,
        email=email,
        username=username,
        name=name,
        password_hash=password_hash,
        created_at=datetime.utcnow()
    )
    await database.execute(query)
    return {
        "id": str(user_id), 
        "email": email, 
        "name": name,
        "username": username
    }


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    query = users.select().where(users.c.email == email)
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    return None


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    query = users.select().where(users.c.username == username)
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    return None


async def get_user_by_id(user_id: UUID) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    query = users.select().where(users.c.id == user_id)
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    return None


async def update_user_voice_profile(
    user_id: UUID,
    voice_id: Optional[str] = None,
    voice_name: Optional[str] = None
) -> Dict[str, Any]:
    """Update user's voice profile (voice_id and voice_name)"""
    update_values = {}
    if voice_id is not None:
        update_values["voice_id"] = voice_id
    if voice_name is not None:
        update_values["voice_name"] = voice_name
    
    if not update_values:
        # No updates to make, just return current user
        user = await get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        return user
    
    query = users.update().where(users.c.id == user_id).values(**update_values)
    await database.execute(query)
    
    # Return updated user
    updated_user = await get_user_by_id(user_id)
    if not updated_user:
        raise ValueError(f"User with id {user_id} not found after update")
    return updated_user


# ========== VOICE SAMPLE OPERATIONS ==========

async def create_voice_sample(
    filename: str,
    user_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """Create a new voice sample record"""
    sample_id = uuid4()
    query = voice_samples.insert().values(
        id=sample_id,
        user_id=user_id,
        filename=filename,
        uploaded_at=datetime.utcnow()
    )
    await database.execute(query)
    return {
        "id": str(sample_id),
        "user_id": str(user_id) if user_id else None,
        "filename": filename,
        "uploaded_at": datetime.utcnow().isoformat()
    }


async def get_voice_samples_by_user(user_id: UUID) -> List[Dict[str, Any]]:
    """Get all voice samples for a user"""
    query = voice_samples.select().where(
        voice_samples.c.user_id == user_id
    ).order_by(voice_samples.c.uploaded_at.desc())
    results = await database.fetch_all(query)
    return [dict(row) for row in results]


async def get_voice_sample_by_id(sample_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a voice sample by ID"""
    query = voice_samples.select().where(voice_samples.c.id == sample_id)
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    return None


# ========== VOICE PROFILE OPERATIONS ==========

async def create_voice_profile(
    user_id: UUID,
    voice_id: str,
    voice_name: str,
    set_as_active: bool = False
) -> Dict[str, Any]:
    """Create a new voice profile for a user"""
    # If setting as active, deactivate all other profiles for this user
    if set_as_active:
        await deactivate_all_voice_profiles(user_id)
    
    profile_id = uuid4()
    query = voice_profiles.insert().values(
        id=profile_id,
        user_id=user_id,
        voice_id=voice_id,
        voice_name=voice_name,
        is_active=set_as_active,
        created_at=datetime.utcnow()
    )
    await database.execute(query)
    
    return {
        "id": str(profile_id),
        "user_id": str(user_id),
        "voice_id": voice_id,
        "voice_name": voice_name,
        "is_active": set_as_active,
        "created_at": datetime.utcnow().isoformat()
    }


async def get_voice_profiles_by_user(user_id: UUID) -> List[Dict[str, Any]]:
    """Get all voice profiles for a user, ordered by created_at (newest first)"""
    try:
        if voice_profiles is None:
            raise ValueError("voice_profiles table is not available")
        query = voice_profiles.select().where(
            voice_profiles.c.user_id == user_id
        ).order_by(voice_profiles.c.created_at.desc())
        results = await database.fetch_all(query)
        # Convert UUID objects to strings for JSON serialization
        profiles = []
        for row in results:
            profile_dict = dict(row)
            # Convert UUID fields to strings
            if 'id' in profile_dict and profile_dict['id']:
                profile_dict['id'] = str(profile_dict['id'])
            if 'user_id' in profile_dict and profile_dict['user_id']:
                profile_dict['user_id'] = str(profile_dict['user_id'])
            # Convert datetime to ISO string
            if 'created_at' in profile_dict and profile_dict['created_at']:
                if hasattr(profile_dict['created_at'], 'isoformat'):
                    profile_dict['created_at'] = profile_dict['created_at'].isoformat()
            profiles.append(profile_dict)
        return profiles
    except Exception as e:
        print(f"ERROR in get_voice_profiles_by_user for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def get_active_voice_profile(user_id: UUID) -> Optional[Dict[str, Any]]:
    """Get the active voice profile for a user"""
    query = voice_profiles.select().where(
        (voice_profiles.c.user_id == user_id) & (voice_profiles.c.is_active == True)
    ).order_by(voice_profiles.c.created_at.desc())
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    return None


async def set_active_voice_profile(user_id: UUID, profile_id: UUID) -> Dict[str, Any]:
    """Set a voice profile as active (deactivates all others for this user)"""
    try:
        if voice_profiles is None:
            raise ValueError("voice_profiles table is not available")
        
        # First, deactivate all profiles for this user
        await deactivate_all_voice_profiles(user_id)
        
        # Then activate the specified profile
        query = voice_profiles.update().where(
            (voice_profiles.c.id == profile_id) & (voice_profiles.c.user_id == user_id)
        ).values(is_active=True)
        await database.execute(query)
        
        # Return the updated profile
        query = voice_profiles.select().where(voice_profiles.c.id == profile_id)
        result = await database.fetch_one(query)
        if result:
            profile_dict = dict(result)
            # Convert UUID fields to strings
            if 'id' in profile_dict and profile_dict['id']:
                profile_dict['id'] = str(profile_dict['id'])
            if 'user_id' in profile_dict and profile_dict['user_id']:
                profile_dict['user_id'] = str(profile_dict['user_id'])
            # Convert datetime to ISO string
            if 'created_at' in profile_dict and profile_dict['created_at']:
                if hasattr(profile_dict['created_at'], 'isoformat'):
                    profile_dict['created_at'] = profile_dict['created_at'].isoformat()
            return profile_dict
        raise ValueError(f"Voice profile {profile_id} not found after activation")
    except Exception as e:
        print(f"ERROR in set_active_voice_profile for user {user_id}, profile {profile_id}: {e}")
        import traceback
        traceback.print_exc()
        raise


async def deactivate_all_voice_profiles(user_id: UUID) -> None:
    """Deactivate all voice profiles for a user"""
    query = voice_profiles.update().where(
        voice_profiles.c.user_id == user_id
    ).values(is_active=False)
    await database.execute(query)


async def delete_voice_profile(user_id: UUID, profile_id: UUID) -> bool:
    """Delete a voice profile (only if it belongs to the user)"""
    query = voice_profiles.delete().where(
        (voice_profiles.c.id == profile_id) & (voice_profiles.c.user_id == user_id)
    )
    result = await database.execute(query)
    return result.rowcount > 0


# ========== CONVERSATION OPERATIONS ==========

async def create_conversation(user_id: UUID) -> Dict[str, Any]:
    """Create a new conversation"""
    conversation_id = uuid4()
    query = conversations.insert().values(
        id=conversation_id,
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    await database.execute(query)
    return {
        "id": str(conversation_id),
        "user_id": str(user_id),
        "created_at": datetime.utcnow().isoformat()
    }


async def get_conversations_by_user(
    user_id: UUID,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get all conversations for a user, ordered by most recent"""
    query = conversations.select().where(
        conversations.c.user_id == user_id
    ).order_by(conversations.c.created_at.desc()).limit(limit)
    results = await database.fetch_all(query)
    return [dict(row) for row in results]


async def get_conversation_by_id(conversation_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a conversation by ID"""
    query = conversations.select().where(conversations.c.id == conversation_id)
    result = await database.fetch_one(query)
    if result:
        return dict(result)
    return None


# ========== MESSAGE OPERATIONS ==========

async def create_message(
    conversation_id: UUID,
    role: str,
    text: str,
    emotion: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new message in a conversation"""
    if role not in ["user", "assistant"]:
        raise ValueError("Role must be 'user' or 'assistant'")
    
    message_id = uuid4()
    query = messages.insert().values(
        id=message_id,
        conversation_id=conversation_id,
        role=role,
        text=text,
        emotion=emotion,
        timestamp=datetime.utcnow()
    )
    await database.execute(query)
    return {
        "id": str(message_id),
        "conversation_id": str(conversation_id),
        "role": role,
        "text": text,
        "emotion": emotion,
        "timestamp": datetime.utcnow().isoformat()
    }


async def get_messages_by_conversation(
    conversation_id: UUID,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Get all messages for a conversation, ordered by timestamp"""
    query = messages.select().where(
        messages.c.conversation_id == conversation_id
    ).order_by(messages.c.timestamp.asc()).limit(limit)
    results = await database.fetch_all(query)
    return [dict(row) for row in results]


async def get_conversation_history(
    conversation_id: UUID
) -> List[Dict[str, Any]]:
    """Get full conversation history with messages ordered chronologically"""
    messages_list = await get_messages_by_conversation(conversation_id)
    return messages_list


# ========== UTILITY FUNCTIONS ==========

async def get_or_create_user(email: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Get existing user or create a new one"""
    user = await get_user_by_email(email)
    if user:
        return user
    return await create_user(email, name)


async def create_conversation_with_message(
    user_id: UUID,
    user_text: str,
    assistant_text: str,
    emotion: Optional[str] = None
) -> Dict[str, Any]:
    """Create a conversation and initial user/assistant message pair"""
    # Create conversation
    conversation = await create_conversation(user_id)
    conversation_id = UUID(conversation["id"])
    
    # Create user message
    await create_message(
        conversation_id=conversation_id,
        role="user",
        text=user_text,
        emotion=emotion
    )
    
    # Create assistant message
    await create_message(
        conversation_id=conversation_id,
        role="assistant",
        text=assistant_text
    )
    
    # Return conversation with messages
    conversation["messages"] = await get_messages_by_conversation(conversation_id)
    return conversation

