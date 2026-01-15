"""
Crisis Detection and Safety Layer
Detects crisis situations and provides safe response overrides
This protects ethically and legally by identifying users in distress
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum


class CrisisLevel(Enum):
    """Crisis severity levels"""
    NONE = "none"
    LOW = "low"  # Concerning but not immediate crisis
    MEDIUM = "medium"  # Moderate crisis indicators
    HIGH = "high"  # Severe crisis - immediate intervention needed
    CRITICAL = "critical"  # Life-threatening situation


# Crisis keywords and patterns
CRISIS_KEYWORDS = {
    CrisisLevel.CRITICAL: [
        "kill myself", "kill myself", "suicide", "end my life", "want to die",
        "going to die", "not worth living", "better off dead", "end it all",
        "hurt myself", "self harm", "cutting myself", "overdose", "take pills",
        "jump off", "hang myself", "shoot myself", "no reason to live"
    ],
    CrisisLevel.HIGH: [
        "want to die", "don't want to live", "don't want to be here",
        "want to be here anymore", "not want to be here", "life isn't worth it",
        "everyone would be better", "no one would miss me", "give up",
        "can't go on", "nothing matters", "hopeless", "helpless",
        "severe depression", "can't cope", "breaking down", "losing control"
    ],
    CrisisLevel.MEDIUM: [
        "thoughts of suicide", "suicidal thoughts", "thinking about death",
        "don't see a way out", "feel trapped", "no hope", "desperate",
        "extreme anxiety", "panic attack", "can't function", "overwhelmed",
        "can't sleep", "can't eat", "isolated", "alone"
    ],
    CrisisLevel.LOW: [
        "very depressed", "really sad", "feeling hopeless", "struggling",
        "hard time", "difficult", "stressed out", "anxious", "worried",
        "feeling down", "not doing well", "having trouble"
    ]
}

# Emotion-based crisis triggers
CRISIS_EMOTIONS = {
    CrisisLevel.HIGH: ["sadness", "fear", "anger"],
    CrisisLevel.MEDIUM: ["sadness", "fear"],
    CrisisLevel.LOW: ["sadness"]
}

# Pattern-based detection (regex patterns)
CRISIS_PATTERNS = {
    CrisisLevel.CRITICAL: [
        r"i\s+(want|wanna|going)\s+to\s+(die|kill|end)",
        r"(suicide|kill\s+myself|end\s+my\s+life)",
        r"no\s+reason\s+to\s+live",
        r"better\s+off\s+dead",
        r"(hurt|harm|cut)\s+myself",
        r"(overdose|take\s+pills|end\s+it)"
    ],
    CrisisLevel.HIGH: [
        r"don'?t\s+want\s+to\s+live",
        r"don'?t\s+(think\s+)?(i\s+)?want\s+to\s+be\s+here",
        r"(want|wanna)\s+to\s+be\s+here\s+(anymore|no\s+more)",
        r"not\s+want(ing)?\s+to\s+be\s+here",
        r"don'?t\s+(think\s+)?(i\s+)?want\s+to\s+be",
        r"life\s+isn'?t\s+worth",
        r"everyone\s+would\s+be\s+better",
        r"no\s+one\s+would\s+miss",
        r"can'?t\s+go\s+on",
        r"nothing\s+matters",
        r"(hopeless|helpless)"
    ],
    CrisisLevel.MEDIUM: [
        r"thoughts?\s+of\s+(suicide|death)",
        r"thinking\s+about\s+(death|dying)",
        r"don'?t\s+see\s+a\s+way\s+out",
        r"feel\s+trapped",
        r"(no\s+hope|desperate)"
    ]
}


# Safe response templates for crisis situations
CRISIS_RESPONSES = {
    CrisisLevel.CRITICAL: {
        "response": (
            "I'm really sorry you're feeling this way. You're not alone, and there are people who want to help. "
            "Please consider reaching out to Canadian crisis resources like:\n\n"
            "• Canada Suicide Prevention Service: Call 988 or 1-833-456-4566 (available 24/7)\n"
            "• Crisis Services Canada: Text 686868\n"
            "• Or contact emergency services by calling 911\n\n"
            "You don't have to go through this alone, and there are trained professionals available 24/7 to support you."
        ),
        "should_override": True,
        "log_incident": True
    },
    CrisisLevel.HIGH: {
        "response": (
            "I'm very concerned about what you're experiencing. It sounds like you're going through an extremely difficult time. "
            "Please know that you're not alone, and there are resources available to help:\n\n"
            "• Canada Suicide Prevention Service: Call 988 or 1-833-456-4566 (available 24/7)\n"
            "• Crisis Services Canada: Text 686868\n"
            "• Speak with a mental health professional or your doctor\n"
            "• Or contact emergency services by calling 911\n\n"
            "If you're having thoughts of harming yourself, please reach out for immediate support. "
            "Your wellbeing is important, and there are people trained to help you through this."
        ),
        "should_override": True,
        "log_incident": True
    },
    CrisisLevel.MEDIUM: {
        "response": (
            "I hear that you're going through a really tough time right now. It's important to take these feelings seriously. "
            "I want to encourage you to reach out for support:\n\n"
            "• Consider speaking with a mental health professional\n"
            "• Reach out to trusted friends or family members\n"
            "• Canada Suicide Prevention Service: Call 988 or 1-833-456-4566 (available 24/7)\n"
            "• Crisis Services Canada: Text 686868\n"
            "• Or contact emergency services by calling 911 if you need immediate support\n\n"
            "You don't have to face this alone. There are people and resources available to help you through difficult times."
        ),
        "should_override": True,
        "log_incident": False
    },
    CrisisLevel.LOW: {
        "response": (
            "I can hear that you're struggling right now, and I want you to know that your feelings are valid. "
            "It's important to take care of yourself during difficult times. "
            "If these feelings persist or worsen, please consider reaching out to a mental health professional or someone you trust. "
            "You don't have to go through this alone."
        ),
        "should_override": False,
        "log_incident": False
    }
}


def detect_crisis_keywords(text: str) -> List[Tuple[CrisisLevel, str]]:
    """
    Detect crisis keywords in text
    
    Args:
        text: User input text
        
    Returns:
        List of tuples (crisis_level, matched_keyword)
    """
    text_lower = text.lower()
    detected = []
    
    for level in [CrisisLevel.CRITICAL, CrisisLevel.HIGH, CrisisLevel.MEDIUM, CrisisLevel.LOW]:
        for keyword in CRISIS_KEYWORDS.get(level, []):
            if keyword in text_lower:
                detected.append((level, keyword))
    
    return detected


def detect_crisis_patterns(text: str) -> List[Tuple[CrisisLevel, str]]:
    """
    Detect crisis patterns using regex
    
    Args:
        text: User input text
        
    Returns:
        List of tuples (crisis_level, matched_pattern)
    """
    text_lower = text.lower()
    detected = []
    
    for level in [CrisisLevel.CRITICAL, CrisisLevel.HIGH, CrisisLevel.MEDIUM]:
        for pattern in CRISIS_PATTERNS.get(level, []):
            match = re.search(pattern, text_lower)
            if match:
                detected.append((level, match.group(0)))
    
    return detected


def check_emotion_crisis(emotion: str, emotion_confidence: float) -> Optional[CrisisLevel]:
    """
    Check if emotion indicates crisis
    
    Args:
        emotion: Detected emotion
        emotion_confidence: Confidence score
        
    Returns:
        CrisisLevel if crisis detected, None otherwise
    """
    if emotion_confidence < 0.7:
        return None
    
    emotion_lower = emotion.lower()
    
    # High confidence sadness/fear/anger with high intensity
    if emotion_confidence > 0.9:
        if emotion_lower in CRISIS_EMOTIONS.get(CrisisLevel.HIGH, []):
            return CrisisLevel.MEDIUM
    
    if emotion_lower in CRISIS_EMOTIONS.get(CrisisLevel.MEDIUM, []):
        if emotion_confidence > 0.85:
            return CrisisLevel.LOW
    
    return None


def detect_crisis(
    text: str,
    emotion: Optional[str] = None,
    emotion_confidence: float = 0.0
) -> Dict[str, any]:
    """
    Main crisis detection function
    
    Args:
        text: User input text
        emotion: Detected emotion (optional)
        emotion_confidence: Emotion confidence score
        
    Returns:
        Dictionary with crisis detection results
    """
    if not text or not text.strip():
        return {
            "crisis_detected": False,
            "level": CrisisLevel.NONE,
            "should_override": False,
            "reasons": []
        }
    
    reasons = []
    detected_levels = []
    
    # Check keywords
    keyword_matches = detect_crisis_keywords(text)
    if keyword_matches:
        for level, keyword in keyword_matches:
            detected_levels.append(level)
            reasons.append(f"Keyword detected: '{keyword}'")
    
    # Check patterns
    pattern_matches = detect_crisis_patterns(text)
    if pattern_matches:
        for level, pattern in pattern_matches:
            detected_levels.append(level)
            reasons.append(f"Pattern matched: '{pattern}'")
    
    # Check emotion-based triggers
    if emotion:
        emotion_crisis = check_emotion_crisis(emotion, emotion_confidence)
        if emotion_crisis:
            detected_levels.append(emotion_crisis)
            reasons.append(f"Emotion-based trigger: {emotion} (confidence: {emotion_confidence:.2f})")
    
    # Determine highest crisis level
    if not detected_levels:
        return {
            "crisis_detected": False,
            "level": CrisisLevel.NONE,
            "should_override": False,
            "reasons": []
        }
    
    # Get highest severity level
    level_priority = {
        CrisisLevel.CRITICAL: 4,
        CrisisLevel.HIGH: 3,
        CrisisLevel.MEDIUM: 2,
        CrisisLevel.LOW: 1
    }
    
    highest_level = max(detected_levels, key=lambda l: level_priority[l])
    
    # Get response configuration
    response_config = CRISIS_RESPONSES.get(highest_level, CRISIS_RESPONSES[CrisisLevel.LOW])
    
    return {
        "crisis_detected": True,
        "level": highest_level,
        "should_override": response_config["should_override"],
        "log_incident": response_config.get("log_incident", False),
        "safe_response": response_config["response"],
        "reasons": reasons
    }


def get_crisis_response(crisis_level: CrisisLevel) -> str:
    """
    Get safe response for crisis level
    
    Args:
        crisis_level: Detected crisis level
        
    Returns:
        Safe response text
    """
    response_config = CRISIS_RESPONSES.get(crisis_level, CRISIS_RESPONSES[CrisisLevel.LOW])
    return response_config["response"]


def should_log_crisis_incident(crisis_level: CrisisLevel) -> bool:
    """
    Determine if crisis incident should be logged
    
    Args:
        crisis_level: Detected crisis level
        
    Returns:
        True if should log
    """
    response_config = CRISIS_RESPONSES.get(crisis_level, {})
    return response_config.get("log_incident", False)


# Crisis detection statistics (for monitoring)
_crisis_stats = {
    "total_detections": 0,
    "by_level": {
        CrisisLevel.CRITICAL: 0,
        CrisisLevel.HIGH: 0,
        CrisisLevel.MEDIUM: 0,
        CrisisLevel.LOW: 0
    }
}


def get_crisis_stats() -> Dict[str, any]:
    """
    Get crisis detection statistics
    
    Returns:
        Dictionary with statistics
    """
    return _crisis_stats.copy()


def log_crisis_detection(crisis_level: CrisisLevel):
    """
    Log crisis detection for statistics
    
    Args:
        crisis_level: Detected crisis level
    """
    _crisis_stats["total_detections"] += 1
    _crisis_stats["by_level"][crisis_level] = _crisis_stats["by_level"].get(crisis_level, 0) + 1

