"""
User Style Analyzer
Extracts speech patterns, common phrases, and style characteristics from user messages
"""

from typing import List, Dict, Optional
import re
from collections import Counter
from uuid import UUID


def extract_common_phrases(messages: List[str], min_count: int = 2, min_length: int = 3) -> List[str]:
    """
    Extract common phrases and expressions from user messages
    
    Args:
        messages: List of user message texts
        min_count: Minimum occurrences to be considered common
        min_length: Minimum phrase length
        
    Returns:
        List of common phrases
    """
    if not messages:
        return []
    
    # Extract 2-4 word phrases
    phrases = []
    for message in messages:
        words = message.lower().split()
        # Extract 2-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if len(phrase) >= min_length:
                phrases.append(phrase)
        # Extract 3-word phrases
        for i in range(len(words) - 2):
            phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
            phrases.append(phrase)
    
    # Count and filter
    phrase_counts = Counter(phrases)
    common = [phrase for phrase, count in phrase_counts.items() 
              if count >= min_count and len(phrase.split()) >= 2]
    
    return common[:10]  # Return top 10


def analyze_speech_style(messages: List[str]) -> Dict[str, any]:
    """
    Analyze speech style characteristics from user messages
    
    Args:
        messages: List of user message texts
        
    Returns:
        Dictionary with style characteristics
    """
    if not messages:
        return {
            "avg_length": 0,
            "punctuation_style": "normal",
            "formality": "neutral",
            "common_starters": [],
            "common_connectors": []
        }
    
    # Average message length
    avg_length = sum(len(msg) for msg in messages) / len(messages) if messages else 0
    
    # Punctuation style
    exclamation_count = sum(msg.count('!') for msg in messages)
    question_count = sum(msg.count('?') for msg in messages)
    ellipsis_count = sum(msg.count('...') for msg in messages) + sum(msg.count('…') for msg in messages)
    
    punctuation_style = "normal"
    if ellipsis_count > len(messages) * 0.3:
        punctuation_style = "thoughtful"
    elif exclamation_count > len(messages) * 0.2:
        punctuation_style = "enthusiastic"
    
    # Formality (simple heuristic: contractions, casual words)
    contractions = sum(1 for msg in messages for word in ['don\'t', 'can\'t', 'won\'t', 'i\'m', 'it\'s', 'that\'s'])
    casual_words = sum(1 for msg in messages for word in ['yeah', 'yep', 'nah', 'gonna', 'wanna'] if word in msg.lower())
    
    formality = "casual" if (contractions + casual_words) > len(messages) * 0.5 else "neutral"
    if avg_length > 100 and contractions < len(messages) * 0.2:
        formality = "formal"
    
    # Common sentence starters
    starters = []
    for msg in messages:
        first_words = msg.strip().split()[:2]
        if first_words:
            starters.append(' '.join(first_words).lower())
    common_starters = [phrase for phrase, count in Counter(starters).items() if count >= 2][:5]
    
    # Common connectors (words that connect thoughts)
    connectors = ['but', 'and', 'so', 'because', 'though', 'however', 'also', 'plus', 'or', 'like']
    connector_counts = {}
    for connector in connectors:
        count = sum(1 for msg in messages if f' {connector} ' in f' {msg.lower()} ' or msg.lower().startswith(f'{connector} '))
        if count > 0:
            connector_counts[connector] = count
    common_connectors = sorted(connector_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    common_connectors = [word for word, _ in common_connectors]
    
    return {
        "avg_length": avg_length,
        "punctuation_style": punctuation_style,
        "formality": formality,
        "common_starters": common_starters,
        "common_connectors": common_connectors
    }


def extract_key_terms(messages: List[str], limit: int = 10) -> List[str]:
    """
    Extract key terms and topics from user messages
    
    Args:
        messages: List of user message texts
        limit: Maximum number of terms to return
        
    Returns:
        List of key terms
    """
    if not messages:
        return []
    
    # Simple keyword extraction (can be enhanced with NLP)
    all_text = ' '.join(messages).lower()
    
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
                  'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 
                  'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 
                  'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 
                  'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 
                  'his', 'her', 'its', 'our', 'their'}
    
    # Extract words (2+ characters, alphanumeric)
    words = re.findall(r'\b[a-z]{2,}\b', all_text)
    words = [w for w in words if w not in stop_words]
    
    # Count and return most common
    word_counts = Counter(words)
    return [word for word, _ in word_counts.most_common(limit)]


async def get_user_speech_style(user_id: UUID, limit_messages: int = 50) -> Dict[str, any]:
    """
    Get speech style analysis for a user from their recent messages
    
    Args:
        user_id: User UUID
        limit_messages: Maximum number of messages to analyze
        
    Returns:
        Dictionary with style analysis
    """
    try:
        from db_operations import get_conversations_by_user, get_messages_by_conversation
        from uuid import UUID
        
        # Get user's conversations
        user_conversations = await get_conversations_by_user(user_id, limit=10)
        
        # Collect all user messages
        user_messages = []
        for conv in user_conversations:
            conv_id = UUID(conv["id"])
            messages = await get_messages_by_conversation(conv_id, limit=limit_messages)
            # Filter only user messages
            user_messages.extend([msg["text"] for msg in messages if msg.get("role") == "user"])
        
        if not user_messages:
            return {
                "common_phrases": [],
                "speech_style": {},
                "key_terms": [],
                "message_count": 0
            }
        
        # Analyze style
        common_phrases = extract_common_phrases(user_messages)
        speech_style = analyze_speech_style(user_messages)
        key_terms = extract_key_terms(user_messages)
        
        return {
            "common_phrases": common_phrases,
            "speech_style": speech_style,
            "key_terms": key_terms,
            "message_count": len(user_messages)
        }
    except Exception as e:
        print(f"Warning: Failed to analyze user speech style: {e}")
        return {
            "common_phrases": [],
            "speech_style": {},
            "key_terms": [],
            "message_count": 0
        }


async def get_recent_user_messages(user_id: UUID, conversation_id: Optional[UUID] = None, limit: int = 5) -> List[str]:
    """
    Get recent user messages for context
    
    Args:
        user_id: User UUID
        conversation_id: Optional conversation ID (if provided, uses this conversation)
        limit: Maximum number of recent messages to return
        
    Returns:
        List of recent user message texts
    """
    try:
        from db_operations import get_conversations_by_user, get_messages_by_conversation, get_conversation_by_id
        from uuid import UUID
        
        if conversation_id:
            # Get messages from current conversation
            messages = await get_messages_by_conversation(conversation_id, limit=limit * 2)
            user_messages = [msg["text"] for msg in messages if msg.get("role") == "user"]
            return user_messages[-limit:] if user_messages else []
        else:
            # Get most recent messages across all conversations
            conversations = await get_conversations_by_user(user_id, limit=3)
            all_user_messages = []
            for conv in conversations:
                conv_id = UUID(conv["id"])
                messages = await get_messages_by_conversation(conv_id, limit=limit)
                user_messages = [msg["text"] for msg in messages if msg.get("role") == "user"]
                all_user_messages.extend(user_messages)
            
            # Return most recent
            return all_user_messages[-limit:] if all_user_messages else []
    except Exception as e:
        print(f"Warning: Failed to get recent user messages: {e}")
        return []
