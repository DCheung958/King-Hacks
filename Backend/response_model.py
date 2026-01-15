"""
AI-Based Therapeutic Response Generation using Hugging Face Transformers
Uses google/flan-t5-large for generating warm, supportive responses
Enhanced with therapeutic wrapper, conversation memory, and speech-style mirroring
Tone: Warm friend/family member (not clinical therapist)
"""

import re
import random

# Try to load the model, but gracefully handle if transformers/torch not installed
RESPONSE_MODEL_AVAILABLE = False
tokenizer = None
model = None

try:
    from transformers import AutoTokenizer, T5ForConditionalGeneration
    import torch
    
    # Load model and tokenizer once (expensive, do it at startup)
    print("Loading response generation model (google/flan-t5-large)...")
    MODEL_NAME = "google/flan-t5-large"  # Text-to-text model for dialogue
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
    model.eval()  # Set to evaluation mode
    
    RESPONSE_MODEL_AVAILABLE = True
    print("Response generation model loaded successfully!")
except ImportError:
    print("Warning: transformers or torch not installed. Response generation will use mock implementation.")
    print("Install with: pip install transformers torch")
except Exception as e:
    print(f"Warning: Failed to load response generation model: {e}")
    print("Falling back to mock response generation.")

def check_repetition(response: str, last_message: str) -> bool:
    """
    Check if response repeats phrases from the last assistant message
    
    Returns:
        True if significant repetition detected, False otherwise
    """
    if not last_message:
        return False
    
    response_lower = response.lower()
    last_lower = last_message.lower()
    
    # Phrases that indicate repetition
    repetitive_phrases = [
        "i understand this is difficult",
        "i'm sorry to hear that",
        "i understand",
        "i'm sorry",
        "that must be difficult",
        "i hear you",
        "thank you for sharing",
        "i appreciate you sharing"
    ]
    
    # Check if response contains same phrases as last message
    for phrase in repetitive_phrases:
        if phrase in last_lower and phrase in response_lower:
            # Check if it's a significant overlap (not just a common word)
            if len(phrase) > 15:  # Longer phrases are more significant
                return True
            # For shorter phrases, check if they appear in similar positions
            if phrase in last_lower and phrase in response_lower:
                # Check word-level similarity for key phrases
                last_words = set(last_lower.split())
                response_words = set(response_lower.split())
                common_validation_words = {"understand", "sorry", "difficult", "hear", "appreciate"}
                overlap = last_words.intersection(response_words).intersection(common_validation_words)
                if len(overlap) >= 2:  # 2+ common validation words
                    return True
    
    return False

# Import therapeutic wrapper and conversation memory
try:
    from therapeutic_wrapper import wrap_therapeutic_response
    THERAPEUTIC_WRAPPER_AVAILABLE = True
except ImportError:
    print("Warning: therapeutic_wrapper not available. Responses will not be wrapped.")
    THERAPEUTIC_WRAPPER_AVAILABLE = False

try:
    from conversation_memory import get_conversation_summary
    CONVERSATION_MEMORY_AVAILABLE = True
except ImportError:
    print("Warning: conversation_memory not available. Conversation context will be limited.")
    CONVERSATION_MEMORY_AVAILABLE = False


def apply_speech_style_mirroring(
    response: str,
    user_style: dict = None
) -> str:
    """
    Subtly mirror user's speech style in the response
    
    Args:
        response: The generated response text
        user_style: User's speech style characteristics
        
    Returns:
        Response with subtle style mirroring applied
    """
    if not user_style or not user_style.get("speech_style"):
        return response
    
    style = user_style["speech_style"]
    mirrored = response
    
    # Subtle filler word mirroring (only if user uses fillers frequently)
    filler_info = style.get("filler_words", {})
    if filler_info.get("filler_frequency", 0) > 0.05:  # User uses fillers > 5% of words
        common_fillers = filler_info.get("common_fillers", [])
        if common_fillers:
            # Very subtle: only add 1-2 fillers if appropriate, and only common ones
            top_filler = common_fillers[0] if common_fillers else None
            if top_filler and top_filler in ['like', 'you know', 'i mean', 'well']:
                # Only add at natural pause points, and only occasionally
                import random
                if random.random() < 0.3:  # 30% chance
                    # Add after first sentence if it's a natural fit
                    sentences = mirrored.split('. ')
                    if len(sentences) > 1 and top_filler in ['like', 'you know']:
                        sentences[0] = f"{sentences[0]}, {top_filler}"
                        mirrored = '. '.join(sentences)
    
    # Sentence length mirroring (subtle)
    sentence_structure = style.get("sentence_structure", {})
    pace = sentence_structure.get("pace", "normal")
    avg_words = sentence_structure.get("avg_words_per_sentence", 15)
    
    # Adjust sentence length slightly to match user's pace
    sentences = mirrored.split('. ')
    if pace == "fast" and avg_words < 10:
        # User prefers shorter sentences - keep response concise
        if len(sentences) > 2:
            mirrored = '. '.join(sentences[:2]) + '.'
    elif pace == "slow" and avg_words > 18:
        # User prefers longer sentences - can be more detailed
        # (but we'll keep it reasonable for therapeutic responses)
        pass  # Don't force longer sentences, just allow them
    
    return mirrored


def get_emotional_intensity(emotion: str = None, user_text: str = None) -> str:
    """
    Determine emotional intensity level based on emotion and text content
    
    Returns:
        'light', 'moderate', or 'high'
    """
    if not emotion:
        return 'light'
    
    # Strong emotional distress indicators
    high_intensity_emotions = ['anger', 'fear', 'anxiety', 'sadness', 'despair', 'panic']
    moderate_intensity_emotions = ['stress', 'worry', 'frustration', 'disappointment']
    
    # Check text for intensity indicators
    text_lower = (user_text or "").lower()
    distress_keywords = ['terrible', 'awful', 'horrible', 'worst', 'can\'t handle', 'overwhelming', 
                        'breaking down', 'falling apart', 'desperate', 'hopeless', 'suicidal']
    
    if emotion in high_intensity_emotions or any(keyword in text_lower for keyword in distress_keywords):
        return 'high'
    elif emotion in moderate_intensity_emotions:
        return 'moderate'
    else:
        return 'light'


def generate_therapeutic_response(
    user_text: str, 
    emotion: str = None,
    user_style: dict = None,
    recent_messages: list = None,
    conversation_summary: dict = None,
    persona: str = None,
    warmth: float = 0.5,
    last_assistant_message: str = None,
    conversation_history: list = None
) -> str:
    """
    Generate a warm, supportive response like a close friend or family member
    using google/flan-t5-large with adaptive length based on emotional intensity
    
    Args:
        user_text: The user's input text
        emotion: Detected emotion (optional, used for context and length adaptation)
        user_style: User's speech style characteristics (optional)
        recent_messages: Recent user messages for context (optional)
        conversation_summary: Conversation summary with emotional trajectory (optional)
        persona: Persona type (optional, overrides default friend/family tone)
        warmth: Warmth level 0.0-1.0 (default 0.5)
        last_assistant_message: Last assistant response (to avoid repetition)
        conversation_history: List of previous messages in format [{"role": "user/assistant", "content": "..."}]
        
    Returns:
        Generated warm, supportive response text (wrapped for safety)
    """
    if not RESPONSE_MODEL_AVAILABLE or tokenizer is None or model is None:
        raise RuntimeError("Response model not available. Use mock responses instead.")
    
    # Determine emotional intensity for adaptive response length
    intensity = get_emotional_intensity(emotion, user_text)
    
    # Set adaptive length parameters based on intensity
    # Target ~150 tokens for substantial but concise responses
    if intensity == 'light':
        min_tokens = 20   # 2-3 sentences
        max_tokens = 100  # ~150 tokens target
    elif intensity == 'moderate':
        min_tokens = 40   # 4-6 sentences
        max_tokens = 150  # ~150 tokens target
    else:  # high intensity
        min_tokens = 60   # 6-8 sentences
        max_tokens = 200  # Can be longer for high intensity, but still concise
    
    # Build context-aware prompt with conversation memory
    context_parts = []
    
    # Add conversation summary context if available
    if conversation_summary:
        user_context = conversation_summary.get("user_context", "")
        if user_context:
            context_parts.append(f"Context: {user_context}")
        
        emotional_trajectory = conversation_summary.get("emotional_trajectory", [])
        if emotional_trajectory:
            recent_emotions = [e["emotion"] for e in emotional_trajectory[-3:]]
            if recent_emotions:
                context_parts.append(f"Recent emotional states: {', '.join(recent_emotions)}")
    
    # Map detected emotion to standard emotion categories
    emotion_categories = {
        'joy': ['joy', 'happy', 'happiness', 'excited', 'excitement', 'elated', 'cheerful'],
        'sadness': ['sadness', 'sad', 'hurt', 'grief', 'grieving', 'disappointment', 'disappointed', 'down', 'depressed'],
        'anger': ['anger', 'angry', 'frustration', 'frustrated', 'irritation', 'irritated', 'annoyed', 'mad'],
        'surprise': ['surprise', 'surprised', 'shock', 'shocked', 'amazement', 'amazed', 'astonished'],
        'disgust': ['disgust', 'disgusted', 'aversion', 'uncomfortable', 'uncomfortable'],
        'fear': ['fear', 'afraid', 'anxiety', 'anxious', 'worried', 'worry', 'scared', 'nervous'],
        'neutral': ['neutral', 'calm', 'fine', 'okay', 'ok', 'alright']
    }
    
    # Determine current emotion category
    current_emotion_category = 'neutral'
    if emotion:
        emotion_lower = emotion.lower()
        for category, keywords in emotion_categories.items():
            if any(keyword in emotion_lower for keyword in keywords):
                current_emotion_category = category
                break
    
    # Track emotional shifts from conversation history
    emotional_shift_context = ""
    if conversation_history and len(conversation_history) >= 2:
        # Extract emotions from recent messages (last 6-8 messages = 3-4 exchanges)
        recent_messages = conversation_history[-8:]
        previous_emotions = []
        for msg in recent_messages:
            msg_emotion = msg.get("emotion")
            if msg_emotion:
                # Map to category
                msg_emotion_lower = msg_emotion.lower()
                for category, keywords in emotion_categories.items():
                    if any(keyword in msg_emotion_lower for keyword in keywords):
                        previous_emotions.append(category)
                        break
        
        # Detect emotional shift
        if previous_emotions and previous_emotions[-1] != current_emotion_category:
            emotional_shift_context = f" IMPORTANT: The user's emotion has shifted from {previous_emotions[-1]} to {current_emotion_category}. Acknowledge this change thoughtfully and respond appropriately to the new emotional state."
    
    # Check for crisis indicators in user text
    user_lower = user_text.lower()
    crisis_indicators = ['hurt myself', 'kill myself', 'suicide', 'end it all', 'not worth living', 'want to die', 'self harm']
    has_crisis_indicators = any(indicator in user_lower for indicator in crisis_indicators)
    
    # Check if we've already provided crisis information (avoid repetition)
    crisis_already_addressed = False
    if last_assistant_message:
        # Check for Canadian crisis resources
        crisis_keywords = ['988', '1-833-456-4566', '686868', 'crisis helpline', 'crisis', 'help is available', 'canada suicide prevention', 'crisis services canada']
        crisis_already_addressed = any(keyword in last_assistant_message.lower() for keyword in crisis_keywords)
    
    # Check if user is feeling better after crisis
    improvement_indicators = ['feeling better', 'feeling calmer', 'feeling safe', 'feeling okay', 'doing better', 'calmer now']
    user_improving = any(indicator in user_lower for indicator in improvement_indicators)
    
    # Build crisis context (only if needed and not already addressed)
    crisis_context = ""
    if has_crisis_indicators and not crisis_already_addressed:
        crisis_context = (
            " CRITICAL: The user expressed distress, self-harm, or suicidal thoughts. "
            "Respond with care and provide Canadian crisis resources: "
            "Canada Suicide Prevention Service (Call 988 or 1-833-456-4566, available 24/7), "
            "Crisis Services Canada (Text 686868), or emergency services (911). "
            "Encourage them to seek help immediately."
        )
    elif user_improving and crisis_already_addressed:
        crisis_context = " The user is indicating they feel better or calmer. Acknowledge this positively and avoid repeating crisis information unless new distress arises."
    
    # Check for repetition from last assistant message
    repetition_warning = ""
    if last_assistant_message:
        # Extract common repetitive phrases from last message
        last_lower = last_assistant_message.lower()
        repetitive_phrases = [
            "i understand this is difficult",
            "i'm sorry to hear that",
            "i understand",
            "i'm sorry",
            "that must be difficult",
            "i hear you"
        ]
        found_repetitions = [phrase for phrase in repetitive_phrases if phrase in last_lower]
        if found_repetitions:
            repetition_warning = f" CRITICAL: Do NOT repeat these phrases from your last response: {', '.join(found_repetitions)}. Use completely different, varied language."
    
    # Core system instruction - comprehensive multi-emotion therapy design
    system_instruction = (
        "You are a compassionate friend and therapist who listens carefully and responds empathetically and naturally. "
        "Your goal is to support the user's emotional well-being by recognizing and validating their current feelings. "
        "These may include: Joy (happiness, excitement), Sadness (hurt, grief, disappointment), "
        "Anger (frustration, irritation), Surprise (shock, amazement), Disgust (aversion, discomfort), "
        "Fear (anxiety, worry), Neutral (calm, no strong emotion). "
        "Pay close attention to emotional shifts during the conversation. "
        "If the user moves from one emotion to another, acknowledge the change thoughtfully and respond appropriately. "
        "Use the full conversation context to understand emotional changes and tailor your responses accordingly. "
        "Keep your responses genuine, meaningful, concise, and natural. "
        "Avoid repeating the same safety warnings unnecessarily. "
        "Respond as both a caring therapist and a supportive friend, blending warmth and understanding. "
        "Do NOT repeat the same empathy or apology phrases across turns. "
        "Always respond to the newest emotional detail the user shared. "
        "Use natural, varied language to acknowledge feelings. "
        "Avoid clinical or scripted responses. "
        "Ask at most one open-ended follow-up question when appropriate. "
        "Never claim personal experience or say you relate personally. "
        "Reference specific details from what the user just said."
    ) + emotional_shift_context + crisis_context + repetition_warning
    
    # Build persona context (overrides default style if persona provided)
    persona_context = ""
    try:
        from persona_config import get_persona_prompt_style
        if persona:
            persona_context = get_persona_prompt_style(persona)
    except ImportError:
        pass
    
    # Build style context (if no persona, use user style)
    style_context = ""
    if not persona_context and user_style and user_style.get("speech_style"):
        style = user_style["speech_style"]
        formality = style.get("formality", "neutral")
        
        # Adapt to user's communication style (but keep it conversational, not clinical)
        if formality == "casual":
            style_context = "Respond in a friendly, casual, conversational way like a close friend"
        elif formality == "formal":
            style_context = "Respond in a warm, thoughtful way like a caring family member"
        else:
            style_context = "Respond in a warm, friendly, conversational way"
    
    # Adjust for warmth level (0.0 = direct, 1.0 = gentle)
    warmth_adjustment = ""
    if warmth < 0.3:
        warmth_adjustment = "Be more direct and supportive, like a friend giving honest advice."
    elif warmth > 0.7:
        warmth_adjustment = "Be very gentle and comforting, like a caring family member."
    
    # Add common phrases if available
    common_phrases = ""
    if user_style and user_style.get("common_phrases"):
        phrases = user_style["common_phrases"][:3]  # Top 3 phrases
        if phrases:
            common_phrases = f" The person often says things like: {', '.join(phrases)}."
    
    # Add recent message context
    recent_context = ""
    if recent_messages and len(recent_messages) > 0:
        recent_text = " ".join(recent_messages[-2:])  # Last 2 messages
        recent_context = f" Recent conversation: {recent_text[:100]}"
    
    # Add last assistant message to avoid repetition
    last_response_context = ""
    if last_assistant_message:
        last_response_context = f" Your previous response was: '{last_assistant_message[:150]}'. Do NOT repeat any phrases from it. Use completely different language."
    
    # Create a therapeutic prompt with all context
    # Emphasize responding to specific details
    if emotion:
        base_prompt = f"I'm feeling {emotion}. {user_text}"
    else:
        base_prompt = user_text
    
    # Check for specific topics that need explicit response
    user_lower = user_text.lower()
    specific_topic_context = ""
    if "bully" in user_lower or "bullied" in user_lower or "bullying" in user_lower:
        specific_topic_context = " IMPORTANT: The user mentioned bullying. Explicitly acknowledge and respond to the bullying. Do not use generic empathy - address the bullying directly."
    elif "school" in user_lower:
        specific_topic_context = " The user mentioned school. Reference this in your response."
    elif "work" in user_lower or "job" in user_lower:
        specific_topic_context = " The user mentioned work. Reference this in your response."
    
    # Combine all context (persona takes priority)
    full_context = " ".join(context_parts) if context_parts else ""
    prompt_parts = []
    
    # Add persona context first (if available)
    if persona_context:
        prompt_parts.append(persona_context)
    elif style_context:
        prompt_parts.append(style_context)
    
    # Add other context
    if full_context:
        prompt_parts.append(full_context)
    if common_phrases:
        prompt_parts.append(common_phrases)
    if recent_context:
        prompt_parts.append(recent_context)
    if last_response_context:
        prompt_parts.append(last_response_context)
    if specific_topic_context:
        prompt_parts.append(specific_topic_context)
    if warmth_adjustment:
        prompt_parts.append(warmth_adjustment)
    
    context_str = ". ".join(prompt_parts) if prompt_parts else ""
    
    # Flan-T5 uses text-to-text format: "task: input"
    # Build conversation history context for Flan-T5 (last 6-8 message pairs = 3-4 exchanges)
    conversation_context = ""
    if conversation_history and len(conversation_history) > 0:
        # Use conversation history from database
        # Format recent conversation for context (last 6-8 messages = 3-4 exchanges)
        recent_history = conversation_history[-8:]
        history_parts = []
        for msg in recent_history:
            role = msg.get("role", "user")
            content = msg.get("content", "") or msg.get("text", "")  # Support both formats
            if role == "user":
                history_parts.append(f"User: {content}")
            elif role == "assistant":
                history_parts.append(f"Bot: {content}")
        if history_parts:
            conversation_context = "Conversation:\n" + "\n".join(history_parts) + "\n\n"
    elif recent_messages and len(recent_messages) > 0:
        # Fallback: use recent messages
        conversation_context = f"Recent conversation: {' '.join(recent_messages[-2:])}\n\n"
    
    # Create a warm, supportive response prompt following the new format
    # Format: System: [System Instruction] + Conversation: [History] + User: [Current] + Bot:
    if conversation_context:
        if context_str:
            full_prompt = f"System: {system_instruction}\n\n{conversation_context}User: {base_prompt}\n\nContext: {context_str}\n\nBot:"
        else:
            full_prompt = f"System: {system_instruction}\n\n{conversation_context}User: {base_prompt}\n\nBot:"
    else:
        if context_str:
            full_prompt = f"System: {system_instruction}\n\nUser: {base_prompt}\n\nContext: {context_str}\n\nBot:"
        else:
            full_prompt = f"System: {system_instruction}\n\nUser: {base_prompt}\n\nBot:"
    
    # Generate response with Flan-T5
    max_regeneration_attempts = 2
    attempt = 0
    response = None
    
    while attempt < max_regeneration_attempts:
        try:
            # Tokenize the prompt (flan-t5 uses standard tokenization)
            inputs = tokenizer(
                full_prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                padding=True
            )
            
            # Generate response with adaptive length
            # Temperature ~0.7 to balance empathy and naturalness (as per design)
            with torch.no_grad():  # Disable gradient computation for inference
                outputs = model.generate(
                    inputs.input_ids,
                    max_length=max_tokens,  # Adaptive max length based on emotional intensity
                    min_length=min_tokens,  # Adaptive min length based on emotional intensity
                    temperature=0.7,  # Balanced for empathy and naturalness (as per design)
                    top_p=0.9,        # Nucleus sampling
                    do_sample=True,   # Enable sampling
                    pad_token_id=tokenizer.pad_token_id,
                    no_repeat_ngram_size=3,  # Avoid repeating 3-grams for better flow
                    repetition_penalty=1.1,  # Slight penalty to avoid repetition
                )
            
            # Decode the generated response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the response
            response = response.strip()
            
            # Remove the prompt prefix if it was included in the output
            if "Bot:" in response:
                response = response.split("Bot:")[-1].strip()
            elif "Your warm, supportive response:" in response:
                response = response.split("Your warm, supportive response:")[-1].strip()
            elif "Response:" in response:
                response = response.split("Response:")[-1].strip()
            
            # Remove anything after newline (but keep first paragraph)
            response = response.split("\n\n")[0].strip()
            response = response.split("\n")[0].strip()
            
            # Check for repetition and regenerate if needed
            if last_assistant_message and check_repetition(response, last_assistant_message) and attempt < max_regeneration_attempts - 1:
                attempt += 1
                print(f"Warning: Detected repetition, regenerating (attempt {attempt}/{max_regeneration_attempts})")
                
                # Regenerate with stronger anti-repetition instruction
                stronger_warning = f" CRITICAL: Your previous response was '{last_assistant_message[:100]}'. You MUST use completely different words and phrases. Do not repeat any validation phrases."
                prompt_with_warning = full_prompt + stronger_warning
                
                inputs = tokenizer(
                    prompt_with_warning,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True,
                    padding=True
                )
                
                with torch.no_grad():
                    outputs = model.generate(
                        inputs.input_ids,
                        max_length=max_tokens,
                        min_length=min_tokens,
                        temperature=0.8,  # Slightly higher for more variation
                        top_p=0.95,
                        do_sample=True,
                        pad_token_id=tokenizer.pad_token_id,
                        no_repeat_ngram_size=4,  # Stronger repetition penalty
                        repetition_penalty=1.3,  # Higher penalty
                    )
                
                response = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
                if "Bot:" in response:
                    response = response.split("Bot:")[-1].strip()
                elif "Your warm, supportive response:" in response:
                    response = response.split("Your warm, supportive response:")[-1].strip()
                response = response.split("\n")[0].strip()
            else:
                break
                
        except Exception as e:
            print(f"Error generating response with Flan-T5: {e}")
            raise RuntimeError(f"Failed to generate response with Flan-T5: {str(e)}")
    
    # Clean up the response
    if not response:
        raise RuntimeError("Flan-T5 returned empty response")
    
    response = response.strip()
    
    # Ensure response is not empty
    if not response or len(response) < 10:
        # Use varied empathy phrase instead of generic
        import random
        varied_empathy_phrases = [
            "That sounds really painful.",
            "That's not fair at all.",
            "Being treated that way can really wear you down.",
            "I'm really glad you told me this.",
            "That must be really hard.",
            "That sounds exhausting.",
            "You don't deserve to be treated that way.",
            "That's really tough to deal with.",
            "I can only imagine how that feels.",
            "That sounds really frustrating."
        ]
        response = f"{random.choice(varied_empathy_phrases)} Would you like to tell me more about what's going on?"
    
    # Remove clinical/therapist language and replace with friend/family language
    clinical_replacements = {
        "I understand this is difficult for you": "I hear you",
        "I'm really glad you shared that with me": "Thanks for sharing that with me",
        "Remember to take deep breaths": "Take your time",
        "How are you feeling right now": "How are you doing",
        "That sounds difficult": "That sounds really tough",
        "It's okay to feel this way": "Your feelings make total sense",
        "I hear you. Would you like to tell me more": "I'm listening. What else is on your mind",
        "Thank you for trusting me": "Thanks for opening up",
        "We can work through it together": "I'm here with you",
        "Your feelings are important and valid": "Your feelings matter",
        "We can navigate this step by step": "We can take this one step at a time"
    }
    
    for clinical, friendly in clinical_replacements.items():
        if clinical.lower() in response.lower():
            # Case-insensitive replacement
            response = re.sub(re.escape(clinical), friendly, response, flags=re.IGNORECASE)
    
    # Apply persona adjustments
    if persona:
        try:
            from persona_config import adjust_response_for_persona
            response = adjust_response_for_persona(response, persona)
        except ImportError:
            pass
    
    # Apply warmth adjustments (keep it conversational, avoid repetition)
    if warmth < 0.3:
        # Make more direct - remove overly gentle phrases
        response = response.replace("I'm really glad you shared that", "Thanks for sharing")
        response = response.replace("I understand this is difficult", "This is challenging")
    elif warmth > 0.7:
        # Make more gentle - ensure validation phrases (but keep it natural and varied)
        validation_phrases = ["That sounds", "That must be", "I hear", "That's", "I can only imagine"]
        has_validation = any(phrase in response for phrase in validation_phrases)
        if not has_validation and not response.startswith(("Thanks", "I'm", "You're", "That", "Being")):
            # Add varied validation, avoiding repetition
            if last_assistant_message:
                last_lower = last_assistant_message.lower()
                if "that sounds" in last_lower:
                    response = f"That must be {response.lower()}" if not response[0].isupper() else f"That must be really hard. {response}"
                elif "that must be" in last_lower:
                    response = f"That sounds {response.lower()}" if not response[0].isupper() else f"That sounds really tough. {response}"
                else:
                    response = f"{random.choice(['That sounds', 'That must be', 'I hear'])} {response.lower()}" if not response[0].isupper() else f"{random.choice(['That sounds really tough', 'That must be hard', 'I hear you'])}. {response}"
            else:
                response = f"{random.choice(['That sounds really tough', 'That must be hard', 'I hear you'])}. {response}"
    
    # Add optional natural interjections sparingly (only when emotionally appropriate)
    # Examples: "hmm", "I see", "that sounds tough", "yeah", "ugh" (never stacked)
    if intensity == 'high' and random.random() < 0.3:  # 30% chance for high intensity
        natural_fillers = ["Hmm", "I see", "That sounds tough", "Yeah", "That's rough"]
        filler = random.choice(natural_fillers)
        # Only add if response doesn't already start with similar phrase
        if not any(f.lower() in response.lower()[:20] for f in natural_fillers):
            response = f"{filler}... {response}"
    
    # Apply speech-style mirroring (subtle)
    if user_style and user_style.get("speech_style"):
        response = apply_speech_style_mirroring(response, user_style["speech_style"])
    elif user_style:
        response = apply_speech_style_mirroring(response, user_style)
    
    # Apply therapeutic wrapper for safety (adjust strictness based on warmth)
    if THERAPEUTIC_WRAPPER_AVAILABLE:
        try:
            response = wrap_therapeutic_response(response, user_text)
        except Exception as e:
            print(f"Warning: Therapeutic wrapper failed: {e}. Using unwrapped response.")
    
    # Adaptive length check - ensure response matches intensity
    # Count sentences to verify appropriate length
    sentences = [s.strip() for s in response.split('.') if s.strip()]
    sentence_count = len(sentences)
    
    if intensity == 'light' and sentence_count > 4:
        # Too long for light intensity - trim to 2-3 sentences
        response = '. '.join(sentences[:3]) + '.'
    elif intensity == 'moderate' and sentence_count < 3:
        # Too short for moderate intensity - try to expand if possible
        if sentence_count == 1 and len(response) < 100:
            # Single sentence that's too short - add validation
            response = f"I hear you. {response}"
    elif intensity == 'high' and sentence_count < 5:
        # Too short for high intensity - ensure adequate support
        if sentence_count < 4:
            # Add additional validation/support
            if "I'm here" not in response and "I'm listening" not in response:
                response = f"I'm here with you. {response}"
    
    # Final check - ensure response isn't too short (minimum 2 sentences for any intensity)
    final_sentences = [s.strip() for s in response.split('.') if s.strip()]
    if len(final_sentences) < 2 and len(response) < 50:
        response = f"I hear you. {response}"
    
    # Ensure empathetic question is included (especially for moderate/high intensity)
    has_question = '?' in response
    if not has_question and intensity in ['moderate', 'high']:
        # Add an empathetic follow-up question
        question_options = [
            "What's been the hardest part about this?",
            "How are you feeling about that?",
            "What's on your mind right now?",
            "What would help you feel better?",
            "What else is going on?",
            "How has this been affecting you?",
            "What do you need right now?",
            "What's making this so difficult?"
        ]
        
        # Choose question based on emotion if available
        if emotion:
            emotion_questions = {
                'sadness': ["What's been the hardest part about this?", "What's making you feel this way?"],
                'anxiety': ["What's worrying you the most?", "What would help you feel calmer?"],
                'anger': ["What's been frustrating you?", "What's making you feel this way?"],
                'stress': ["What's been the most stressful part?", "What would help you feel less overwhelmed?"],
                'fear': ["What's scaring you the most?", "What would make you feel safer?"]
            }
            if emotion.lower() in emotion_questions:
                question_options = emotion_questions[emotion.lower()]
        
        # Add question naturally at the end
        chosen_question = random.choice(question_options)
        
        # Check if response already ends with validation - if so, add question after
        if response.endswith(('.', '!')) and not response.endswith('?'):
            response = f"{response} {chosen_question}"
        else:
            # Add with a connecting phrase
            response = f"{response} {chosen_question}"
    
    # For light intensity, still encourage questions but make them optional
    elif not has_question and intensity == 'light' and len(response) > 80:
        # Only add question if response is substantial enough
        question_options = [
            "How are you doing with that?",
            "What's on your mind?",
            "How does that feel?"
        ]
        chosen_question = random.choice(question_options)
        if response.endswith(('.', '!')):
            response = f"{response} {chosen_question}"
    
    # Add natural conversational fillers sparingly (only for high intensity, emotionally heavy moments)
    if intensity == 'high' and random.random() < 0.3:  # 30% chance
        filler_options = ["Hmm", "Yeah", "Ugh"]
        chosen_filler = random.choice(filler_options)
        # Only add if response doesn't already start with a filler
        if not response.lower().startswith(("hmm", "yeah", "ugh", "well")):
            # Add at natural pause point (after first sentence)
            sentences = response.split('. ')
            if len(sentences) > 1:
                sentences[0] = f"{chosen_filler}... {sentences[0].lower()}"
                response = '. '.join(sentences)
            else:
                response = f"{chosen_filler}... {response.lower()}"
    
    return response
