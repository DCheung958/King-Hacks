"""
Voice Persona Configuration
Defines different speaking styles: Friend, Therapist, Family
Same voice, different word choice, pacing, and prosody
"""

from typing import Dict, Optional
from prosody_config import get_voice_settings


# Persona definitions
PERSONA_CONFIGS = {
    "friend": {
        "name": "Friend",
        "description": "Casual, validating, conversational",
        "prompt_style": (
            "Respond as a supportive friend would. "
            "Use casual, warm language. "
            "Validate their feelings. "
            "Be conversational and relatable. "
            "Avoid clinical or structured therapy language. "
            "Use affirmations like 'I hear you' and 'That makes sense'. "
            "Keep sentences shorter and more natural."
        ),
        "prosody": {
            "stability": 0.6,  # Moderate stability - friendly variation
            "similarity_boost": 0.75,  # Moderate similarity
            "style_exaggeration": 0.3,  # Some warmth
        },
        "characteristics": {
            "sentence_length": "short_to_medium",  # 8-15 words
            "question_ratio": 0.2,  # 20% questions
            "formality": "casual",
            "validation_frequency": "high"
        }
    },
    "therapist": {
        "name": "Therapist",
        "description": "Slower, reflective, questions-focused",
        "prompt_style": (
            "Respond as a professional therapist would. "
            "Ask reflective questions to help them explore. "
            "Use slower, more thoughtful pacing. "
            "Avoid giving direct advice unless asked. "
            "Focus on helping them understand their own feelings. "
            "Use open-ended questions. "
            "Be patient and non-judgmental."
        ),
        "prosody": {
            "stability": 0.8,  # Higher stability - professional, steady
            "similarity_boost": 0.85,  # Higher similarity
            "style_exaggeration": 0.15,  # Minimal exaggeration - professional
        },
        "characteristics": {
            "sentence_length": "medium_to_long",  # 12-20 words
            "question_ratio": 0.4,  # 40% questions
            "formality": "professional",
            "validation_frequency": "moderate"
        }
    },
    "family": {
        "name": "Family",
        "description": "Encouraging, action-oriented, motivating",
        "prompt_style": (
            "Respond as a caring family member would. "
            "Be encouraging and supportive. "
            "Offer gentle guidance and motivation. "
            "Be action-oriented but not pushy. "
            "Show care and concern. "
            "Use encouraging phrases like 'You've got this' and 'I believe in you'. "
            "Balance empathy with gentle encouragement to take steps forward."
        ),
        "prosody": {
            "stability": 0.7,  # Moderate-high stability - steady encouragement
            "similarity_boost": 0.8,  # Higher similarity
            "style_exaggeration": 0.25,  # Some warmth and encouragement
        },
        "characteristics": {
            "sentence_length": "medium",  # 10-16 words
            "question_ratio": 0.25,  # 25% questions
            "formality": "warm_casual",
            "validation_frequency": "high"
        }
    }
}

# Default persona
DEFAULT_PERSONA = "friend"


def get_persona_config(persona: Optional[str] = None) -> Dict:
    """
    Get persona configuration
    
    Args:
        persona: Persona name ("friend", "therapist", "family")
        
    Returns:
        Persona configuration dictionary
    """
    if not persona:
        persona = DEFAULT_PERSONA
    
    persona_lower = persona.lower()
    
    if persona_lower in PERSONA_CONFIGS:
        return PERSONA_CONFIGS[persona_lower].copy()
    
    # Default to friend if unknown
    return PERSONA_CONFIGS[DEFAULT_PERSONA].copy()


def get_persona_prompt_style(persona: Optional[str] = None) -> str:
    """
    Get prompt style instructions for persona
    
    Args:
        persona: Persona name
        
    Returns:
        Prompt style string
    """
    config = get_persona_config(persona)
    return config["prompt_style"]


def get_persona_prosody(persona: Optional[str] = None, emotion: Optional[str] = None) -> Dict[str, float]:
    """
    Get prosody settings for persona (with emotion adjustment)
    
    Args:
        persona: Persona name
        emotion: Emotion for additional adjustment
        
    Returns:
        Dictionary with prosody settings
    """
    config = get_persona_config(persona)
    base_prosody = config["prosody"].copy()
    
    # Get emotion-based prosody
    from prosody_config import get_prosody_for_emotion
    emotion_prosody = get_prosody_for_emotion(emotion)
    
    # Blend persona and emotion prosody (persona is base, emotion adjusts)
    # Average them for a balanced approach
    blended = {
        "stability": (base_prosody["stability"] + emotion_prosody["stability"]) / 2,
        "similarity_boost": (base_prosody["similarity_boost"] + emotion_prosody["similarity_boost"]) / 2,
        "style_exaggeration": (base_prosody["style_exaggeration"] + emotion_prosody["style_exaggeration"]) / 2
    }
    
    return blended


def adjust_response_for_persona(
    response: str,
    persona: Optional[str] = None
) -> str:
    """
    Adjust response text for persona characteristics
    
    Args:
        response: Generated response
        persona: Persona name
        
    Returns:
        Adjusted response
    """
    config = get_persona_config(persona)
    characteristics = config["characteristics"]
    
    # Adjust sentence length if needed
    sentence_length_pref = characteristics["sentence_length"]
    sentences = [s.strip() for s in response.split('.') if s.strip()]
    
    if sentence_length_pref == "short_to_medium":
        # Ensure sentences aren't too long (max 15 words)
        adjusted_sentences = []
        for sent in sentences:
            words = sent.split()
            if len(words) > 15:
                # Split long sentences
                mid = len(words) // 2
                adjusted_sentences.append(' '.join(words[:mid]) + '.')
                adjusted_sentences.append(' '.join(words[mid:]))
            else:
                adjusted_sentences.append(sent)
        response = '. '.join(adjusted_sentences) + '.'
    
    elif sentence_length_pref == "medium_to_long":
        # Combine short sentences if too many
        if len(sentences) > 3 and any(len(s.split()) < 8 for s in sentences):
            # Keep longer sentences, combine short ones
            pass  # For now, keep as is
    
    # Adjust question ratio if needed
    question_ratio = characteristics["question_ratio"]
    current_questions = sum(1 for s in sentences if '?' in s)
    current_ratio = current_questions / len(sentences) if sentences else 0
    
    if question_ratio > current_ratio + 0.1:  # Need more questions
        # Convert last statement to question if appropriate
        if sentences and '?' not in sentences[-1]:
            last_sent = sentences[-1]
            if any(word in last_sent.lower() for word in ['could', 'might', 'would', 'can']):
                sentences[-1] = last_sent.rstrip('.') + '?'
                response = '. '.join(sentences)
    
    return response


