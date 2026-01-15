"""
Therapeutic Response Wrapper
Enforces safety guidelines for AI-generated therapeutic responses:
- Empathy first
- No diagnosis
- Gentle encouragement
- Questions over directives
"""

import re
from typing import List, Tuple


# Empathy indicators
EMPATHY_PHRASES = [
    "i understand", "i hear you", "that sounds", "i can imagine",
    "that must be", "it makes sense", "i appreciate", "thank you for sharing",
    "that's valid", "your feelings are", "it's okay to feel"
]

# Diagnostic language to avoid
DIAGNOSTIC_PHRASES = [
    "you have", "you are", "you're", "you suffer from", "you're diagnosed",
    "you need medication", "you need therapy", "you should see a doctor",
    "you have a disorder", "you have a condition", "you're depressed",
    "you're anxious", "you're bipolar", "you're ocd"
]

# Directive/command language to soften
DIRECTIVE_PHRASES = [
    r"you must\s+", r"you should\s+", r"you need to\s+", r"you have to\s+",
    r"you can't\s+", r"you shouldn't\s+", r"don't\s+", r"stop\s+",
    r"you must not\s+", r"you should not\s+"
]

# Softening alternatives
SOFTENING_PHRASES = {
    "you must": "you might consider",
    "you should": "it might help to",
    "you need to": "you could try",
    "you have to": "it could be helpful to",
    "you can't": "it might be challenging to",
    "you shouldn't": "it might be worth considering",
    "don't": "perhaps avoid",
    "stop": "you might pause"
}


def check_empathy(response: str) -> bool:
    """
    Check if response contains empathy indicators
    
    Returns:
        True if empathy is present, False otherwise
    """
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in EMPATHY_PHRASES)


def check_diagnosis(response: str) -> bool:
    """
    Check if response contains diagnostic language
    
    Returns:
        True if diagnostic language is found, False otherwise
    """
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in DIAGNOSTIC_PHRASES)


def check_directives(response: str) -> List[Tuple[str, str]]:
    """
    Find directive/command language in response
    
    Returns:
        List of tuples (original_phrase, suggested_replacement)
    """
    found_directives = []
    response_lower = response.lower()
    
    for pattern, replacement in SOFTENING_PHRASES.items():
        if re.search(pattern, response_lower):
            found_directives.append((pattern, replacement))
    
    # Also check for regex patterns
    for pattern in DIRECTIVE_PHRASES:
        if re.search(pattern, response_lower):
            # Extract the actual phrase
            match = re.search(pattern, response_lower)
            if match:
                found_directives.append((match.group(0), "consider"))
    
    return found_directives


def check_off_topic(response: str, user_text: str) -> bool:
    """
    Check if response seems off-topic compared to user input
    
    Returns:
        True if response seems off-topic, False otherwise
    """
    # Simple heuristic: check for shared keywords
    user_words = set(re.findall(r'\b\w{3,}\b', user_text.lower()))
    response_words = set(re.findall(r'\b\w{3,}\b', response.lower()))
    
    # Common stop words to ignore
    stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'with',
                  'this', 'that', 'from', 'have', 'has', 'was', 'were',
                  'been', 'being', 'can', 'could', 'should', 'would'}
    
    user_words = user_words - stop_words
    response_words = response_words - stop_words
    
    if not user_words:
        return False
    
    # If less than 10% word overlap, might be off-topic
    overlap = len(user_words & response_words) / len(user_words)
    return overlap < 0.1


def add_empathy_validation(response: str) -> str:
    """
    Prepend empathy validation if response lacks empathy
    
    Returns:
        Response with empathy validation prepended if needed
    """
    empathy_validations = [
        "I understand this is difficult for you. ",
        "I hear you, and I want you to know that your feelings are valid. ",
        "Thank you for sharing this with me. ",
        "I appreciate you opening up about this. "
    ]
    
    # Use a simple one based on response length
    validation = empathy_validations[len(response) % len(empathy_validations)]
    return validation + response


def soften_directives(response: str) -> str:
    """
    Soften directive language in response
    
    Returns:
        Response with softened language
    """
    softened = response
    
    # Replace directive phrases
    for original, replacement in SOFTENING_PHRASES.items():
        # Case-insensitive replacement
        pattern = re.compile(re.escape(original), re.IGNORECASE)
        softened = pattern.sub(replacement, softened)
    
    # Handle "don't" and "stop" more carefully
    softened = re.sub(r'\bdon\'t\s+', 'perhaps avoid ', softened, flags=re.IGNORECASE)
    softened = re.sub(r'\bstop\s+', 'you might pause ', softened, flags=re.IGNORECASE)
    
    # Convert commands to questions where appropriate
    # "You should X" -> "Have you considered X?"
    softened = re.sub(
        r'\bit might help to\s+([^.!?]+)',
        r'have you considered \1?',
        softened,
        flags=re.IGNORECASE
    )
    
    return softened


def wrap_therapeutic_response(
    raw_response: str,
    user_text: str,
    max_regenerations: int = 2
) -> str:
    """
    Wrap and validate therapeutic response with safety checks
    
    Args:
        raw_response: The raw AI-generated response
        user_text: The user's input text (for context checking)
        max_regenerations: Maximum number of times to attempt fixing issues
        
    Returns:
        Validated and wrapped therapeutic response
    """
    response = raw_response.strip()
    
    # Check 1: Empathy
    if not check_empathy(response):
        response = add_empathy_validation(response)
    
    # Check 2: No diagnosis
    if check_diagnosis(response):
        # Remove or replace diagnostic language
        response_lower = response.lower()
        for phrase in DIAGNOSTIC_PHRASES:
            if phrase in response_lower:
                # Replace with softer language
                response = re.sub(
                    re.compile(re.escape(phrase), re.IGNORECASE),
                    "you're experiencing",
                    response
                )
    
    # Check 3: Soften directives
    directives = check_directives(response)
    if directives:
        response = soften_directives(response)
    
    # Check 4: Off-topic (note: this is a simple heuristic)
    # We'll be lenient here since AI responses can be valid even without word overlap
    # Only flag if response is very short and completely unrelated
    if len(response) < 30 and check_off_topic(response, user_text):
        # Add a bridging phrase
        response = f"I hear you. {response}"
    
    # Final cleanup: ensure response ends properly
    if not response.endswith(('.', '!', '?')):
        response += '.'
    
    # Ensure response is not too short
    if len(response) < 15:
        response = "I understand this is difficult. Would you like to tell me more about what's on your mind?"
    
    # Ensure response is not too long (therapeutic responses should be concise)
    if len(response) > 300:
        # Truncate at sentence boundary
        sentences = re.split(r'[.!?]', response)
        response = '. '.join(sentences[:3]) + '.'
    
    return response


def validate_response_quality(response: str) -> dict:
    """
    Validate response quality and return a report
    
    Returns:
        Dictionary with validation results
    """
    has_empathy = check_empathy(response)
    has_diagnosis = check_diagnosis(response)
    has_directives = len(check_directives(response)) > 0
    
    return {
        "has_empathy": has_empathy,
        "has_diagnosis": has_diagnosis,
        "has_directives": has_directives,
        "is_valid": has_empathy and not has_diagnosis,
        "warnings": []
    }

