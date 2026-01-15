"""
Prosody-Aware Voice Synthesis Configuration
Adjusts ElevenLabs voice parameters based on emotional state
"""

from typing import Dict, Optional


# Prosody settings per emotion
# Parameters: stability, similarity_boost, style_exaggeration
PROSODY_CONFIG = {
    "sadness": {
        "stability": 0.5,  # Lower stability for more variation (sad voices are less stable)
        "similarity_boost": 0.75,  # Moderate similarity
        "style_exaggeration": 0.3,  # Subtle style exaggeration
        "description": "Gentle, empathetic tone with slight variation"
    },
    "fear": {
        "stability": 0.4,  # Lower stability for anxious/unstable voice
        "similarity_boost": 0.7,  # Lower similarity for more variation
        "style_exaggeration": 0.4,  # More exaggeration for emotional intensity
        "description": "Softer, reassuring tone with calming variation"
    },
    "anger": {
        "stability": 0.6,  # Moderate stability
        "similarity_boost": 0.8,  # Higher similarity
        "style_exaggeration": 0.2,  # Less exaggeration (calm response to anger)
        "description": "Calm, steady tone to de-escalate"
    },
    "joy": {
        "stability": 0.7,  # Higher stability for positive emotions
        "similarity_boost": 0.85,  # Higher similarity
        "style_exaggeration": 0.25,  # Subtle positive exaggeration
        "description": "Warm, positive tone with stability"
    },
    "surprise": {
        "stability": 0.55,  # Moderate stability
        "similarity_boost": 0.75,  # Moderate similarity
        "style_exaggeration": 0.3,  # Moderate exaggeration
        "description": "Engaged, responsive tone"
    },
    "disgust": {
        "stability": 0.6,  # Moderate stability
        "similarity_boost": 0.75,  # Moderate similarity
        "style_exaggeration": 0.2,  # Less exaggeration (neutral response)
        "description": "Neutral, understanding tone"
    },
    "anxiety": {
        "stability": 0.45,  # Lower stability for anxious situations
        "similarity_boost": 0.7,  # Lower similarity
        "style_exaggeration": 0.35,  # More exaggeration for empathy
        "description": "Calming, reassuring tone with variation"
    },
    "calm": {
        "stability": 0.75,  # High stability for calm responses
        "similarity_boost": 0.9,  # High similarity
        "style_exaggeration": 0.15,  # Minimal exaggeration
        "description": "Stable, clear, professional tone"
    },
    "concern": {
        "stability": 0.6,  # Moderate stability
        "similarity_boost": 0.8,  # Higher similarity
        "style_exaggeration": 0.25,  # Subtle exaggeration
        "description": "Empathetic, caring tone"
    }
}

# Default prosody settings (fallback)
DEFAULT_PROSODY = {
    "stability": 0.65,
    "similarity_boost": 0.8,
    "style_exaggeration": 0.2,
    "description": "Balanced, neutral tone"
}


def get_prosody_for_emotion(emotion: Optional[str]) -> Dict[str, float]:
    """
    Get prosody settings for a given emotion
    
    Args:
        emotion: Emotion name (lowercase)
        
    Returns:
        Dictionary with prosody parameters
    """
    if not emotion:
        return DEFAULT_PROSODY.copy()
    
    emotion_lower = emotion.lower()
    
    # Direct match
    if emotion_lower in PROSODY_CONFIG:
        return PROSODY_CONFIG[emotion_lower].copy()
    
    # Partial match (e.g., "very sad" -> "sadness")
    for key, config in PROSODY_CONFIG.items():
        if key in emotion_lower or emotion_lower in key:
            return config.copy()
    
    # Default fallback
    return DEFAULT_PROSODY.copy()


def get_voice_settings(
    emotion: Optional[str] = None,
    custom_stability: Optional[float] = None,
    custom_similarity_boost: Optional[float] = None,
    custom_style_exaggeration: Optional[float] = None
) -> Dict[str, float]:
    """
    Get voice settings with optional overrides
    
    Args:
        emotion: Emotion name
        custom_stability: Override stability (0.0-1.0)
        custom_similarity_boost: Override similarity boost (0.0-1.0)
        custom_style_exaggeration: Override style exaggeration (0.0-1.0)
        
    Returns:
        Dictionary with voice settings
    """
    prosody = get_prosody_for_emotion(emotion)
    
    settings = {
        "stability": custom_stability if custom_stability is not None else prosody["stability"],
        "similarity_boost": custom_similarity_boost if custom_similarity_boost is not None else prosody["similarity_boost"],
        "style_exaggeration": custom_style_exaggeration if custom_style_exaggeration is not None else prosody["style_exaggeration"]
    }
    
    # Validate ranges
    settings["stability"] = max(0.0, min(1.0, settings["stability"]))
    settings["similarity_boost"] = max(0.0, min(1.0, settings["similarity_boost"]))
    settings["style_exaggeration"] = max(0.0, min(1.0, settings["style_exaggeration"]))
    
    return settings

