"""
Conversation Memory and Summarization
Maintains rolling context of user conversations with emotional trajectory tracking
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime
import json


# In-memory storage for conversation summaries (in production, use Redis or database)
_conversation_summaries: Dict[str, Dict[str, Any]] = {}


async def get_conversation_summary(
    user_id: UUID,
    conversation_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Get or create conversation summary for a user
    
    Args:
        user_id: User UUID
        conversation_id: Optional conversation ID (if None, uses most recent)
        
    Returns:
        Dictionary with conversation summary
    """
    try:
        from db_operations import (
            get_conversations_by_user,
            get_messages_by_conversation,
            get_conversation_by_id
        )
        
        # Get conversation ID if not provided
        if not conversation_id:
            conversations = await get_conversations_by_user(user_id, limit=1)
            if conversations:
                conversation_id = UUID(conversations[0]["id"])
            else:
                return _create_empty_summary()
        
        # Check cache first
        cache_key = f"{user_id}_{conversation_id}"
        if cache_key in _conversation_summaries:
            summary = _conversation_summaries[cache_key]
            # Check if summary is recent (within last hour)
            if summary.get("last_updated"):
                last_updated = datetime.fromisoformat(summary["last_updated"])
                if (datetime.utcnow() - last_updated).total_seconds() < 3600:
                    return summary
        
        # Get messages
        messages = await get_messages_by_conversation(conversation_id, limit=100)
        
        if not messages:
            return _create_empty_summary()
        
        # Build summary
        summary = _build_summary_from_messages(messages, user_id, conversation_id)
        
        # Cache summary
        _conversation_summaries[cache_key] = summary
        
        return summary
        
    except Exception as e:
        print(f"Warning: Failed to get conversation summary: {e}")
        return _create_empty_summary()


def _create_empty_summary() -> Dict[str, Any]:
    """Create an empty summary structure"""
    return {
        "user_id": None,
        "conversation_id": None,
        "message_count": 0,
        "emotional_trajectory": [],
        "key_topics": [],
        "user_context": "",
        "last_updated": datetime.utcnow().isoformat()
    }


def _build_summary_from_messages(
    messages: List[Dict[str, Any]],
    user_id: UUID,
    conversation_id: UUID
) -> Dict[str, Any]:
    """
    Build conversation summary from messages
    
    Args:
        messages: List of message dictionaries
        user_id: User UUID
        conversation_id: Conversation UUID
        
    Returns:
        Summary dictionary
    """
    user_messages = [msg for msg in messages if msg.get("role") == "user"]
    assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
    
    # Extract emotional trajectory
    emotional_trajectory = []
    for msg in user_messages:
        if msg.get("emotion"):
            emotional_trajectory.append({
                "emotion": msg["emotion"],
                "timestamp": msg.get("timestamp", ""),
                "text_preview": msg.get("text", "")[:50] + "..." if len(msg.get("text", "")) > 50 else msg.get("text", "")
            })
    
    # Extract key topics (simple keyword extraction)
    all_user_text = " ".join([msg.get("text", "") for msg in user_messages])
    key_topics = _extract_key_topics(all_user_text)
    
    # Build user context summary
    user_context = _build_user_context(user_messages, emotional_trajectory, key_topics)
    
    return {
        "user_id": str(user_id),
        "conversation_id": str(conversation_id),
        "message_count": len(messages),
        "user_message_count": len(user_messages),
        "emotional_trajectory": emotional_trajectory[-10:],  # Last 10 emotions
        "key_topics": key_topics[:5],  # Top 5 topics
        "user_context": user_context,
        "last_updated": datetime.utcnow().isoformat()
    }


def _extract_key_topics(text: str, limit: int = 5) -> List[str]:
    """
    Extract key topics from text (simple keyword extraction)
    
    Args:
        text: Input text
        limit: Maximum number of topics
        
    Returns:
        List of key topics
    """
    import re
    from collections import Counter
    
    # Common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its',
        'our', 'their', 'what', 'when', 'where', 'why', 'how', 'about', 'feel',
        'feeling', 'feelings', 'think', 'thought', 'thoughts'
    }
    
    # Extract words (3+ characters)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    words = [w for w in words if w not in stop_words]
    
    # Count and return most common
    word_counts = Counter(words)
    return [word for word, _ in word_counts.most_common(limit)]


def _build_user_context(
    user_messages: List[Dict[str, Any]],
    emotional_trajectory: List[Dict[str, Any]],
    key_topics: List[str]
) -> str:
    """
    Build a natural language summary of user context
    
    Args:
        user_messages: List of user messages
        emotional_trajectory: List of emotional states
        key_topics: List of key topics
        
    Returns:
        Natural language context summary
    """
    if not user_messages:
        return ""
    
    context_parts = []
    
    # Emotional trajectory summary
    if emotional_trajectory:
        recent_emotions = [e["emotion"] for e in emotional_trajectory[-5:]]
        if recent_emotions:
            emotion_counts = {}
            for emotion in recent_emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
            context_parts.append(f"The user has been expressing {dominant_emotion} recently.")
    
    # Key topics
    if key_topics:
        topics_str = ", ".join(key_topics[:3])
        context_parts.append(f"Key topics discussed: {topics_str}.")
    
    # Message count context
    if len(user_messages) > 10:
        context_parts.append(f"This is an ongoing conversation with {len(user_messages)} user messages.")
    
    return " ".join(context_parts) if context_parts else "Starting a new conversation."


async def update_conversation_summary(
    user_id: UUID,
    conversation_id: UUID,
    new_message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update conversation summary with a new message
    
    Args:
        user_id: User UUID
        conversation_id: Conversation UUID
        new_message: New message dictionary
        
    Returns:
        Updated summary
    """
    # Invalidate cache
    cache_key = f"{user_id}_{conversation_id}"
    if cache_key in _conversation_summaries:
        del _conversation_summaries[cache_key]
    
    # Rebuild summary
    return await get_conversation_summary(user_id, conversation_id)


def should_summarize(
    message_count: int,
    n_messages: int = 5
) -> bool:
    """
    Check if conversation should be summarized
    
    Args:
        message_count: Current message count
        n_messages: Summarize every N messages
        
    Returns:
        True if should summarize
    """
    return message_count > 0 and message_count % n_messages == 0


def get_emotional_trajectory_summary(emotional_trajectory: List[Dict[str, Any]]) -> str:
    """
    Generate a summary of emotional trajectory
    
    Args:
        emotional_trajectory: List of emotional states
        
    Returns:
        Natural language summary
    """
    if not emotional_trajectory:
        return "No emotional pattern detected yet."
    
    recent = emotional_trajectory[-5:] if len(emotional_trajectory) > 5 else emotional_trajectory
    emotions = [e["emotion"] for e in recent]
    
    # Count emotions
    emotion_counts = {}
    for emotion in emotions:
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    
    if not emotion_counts:
        return "Emotional state is varied."
    
    # Find dominant emotion
    dominant = max(emotion_counts.items(), key=lambda x: x[1])
    
    # Check for trends
    if len(emotions) >= 3:
        if emotions[-1] == emotions[-2] == emotions[-3]:
            return f"The user has been consistently expressing {emotions[-1]}."
        elif emotions[-1] != emotions[0]:
            return f"Emotional state has shifted from {emotions[0]} to {emotions[-1]}."
    
    return f"Recent emotional state: {dominant[0]} (appeared {dominant[1]} times)."

