# Therapeutic Response Enhancements

## Overview

This document describes the advanced therapeutic response features that make Echocare safer, more personalized, and more human-like.

---

## 🛡️ Tier 1: Therapeutic Response Wrapper

### Purpose
Enforces safety guidelines for all AI-generated responses to ensure they remain therapeutic, empathetic, and safe.

### Features

#### 1. **Empathy First**
- Checks if response contains empathy indicators
- If missing, automatically prepends validation phrases like:
  - "I understand this is difficult for you. "
  - "I hear you, and I want you to know that your feelings are valid. "
  - "Thank you for sharing this with me. "

#### 2. **No Diagnosis**
- Detects and removes diagnostic language
- Prevents responses like "you have depression" or "you're anxious"
- Replaces with softer language like "you're experiencing"

#### 3. **Gentle Encouragement**
- Softens directive/command language
- Converts "you must" → "you might consider"
- Converts "you should" → "it might help to"
- Converts "don't" → "perhaps avoid"

#### 4. **Questions Over Directives**
- Converts commands to questions where appropriate
- "You should X" → "Have you considered X?"

### Implementation

**File:** `Backend/therapeutic_wrapper.py`

**Key Functions:**
- `wrap_therapeutic_response()` - Main wrapper function
- `check_empathy()` - Validates empathy presence
- `check_diagnosis()` - Detects diagnostic language
- `check_directives()` - Finds directive language
- `soften_directives()` - Softens commands

**Usage:**
```python
from therapeutic_wrapper import wrap_therapeutic_response

raw_response = "You should try meditation."
safe_response = wrap_therapeutic_response(raw_response, user_text="I'm stressed")
# Result: "It might help to try meditation. Have you considered it?"
```

---

## 🧠 Tier 2: Conversation Memory Summarization

### Purpose
Maintains rolling context of user conversations with emotional trajectory tracking, making the bot feel like it knows you.

### Features

#### 1. **Emotional Trajectory Tracking**
- Tracks emotional states across conversation
- Identifies patterns and shifts
- Stores last 10 emotional states

#### 2. **Key Topics Extraction**
- Extracts important topics from conversation
- Tracks what user discusses most
- Feeds into response generation

#### 3. **Rolling User Context**
- Builds natural language summary of user context
- Updates every N messages (default: 5)
- Includes:
  - Recent emotional states
  - Key topics discussed
  - Conversation length context

#### 4. **Automatic Summarization**
- Summarizes conversation every 5 messages
- Caches summaries for performance
- Invalidates cache when new messages arrive

### Implementation

**File:** `Backend/conversation_memory.py`

**Key Functions:**
- `get_conversation_summary()` - Get or create summary
- `update_conversation_summary()` - Update with new message
- `should_summarize()` - Check if summarization needed
- `get_emotional_trajectory_summary()` - Get emotion summary

**Usage:**
```python
from conversation_memory import get_conversation_summary

summary = await get_conversation_summary(user_id, conversation_id)
# Returns:
# {
#   "emotional_trajectory": [...],
#   "key_topics": ["work", "stress", "anxiety"],
#   "user_context": "The user has been expressing anxiety recently. Key topics: work, stress."
# }
```

---

## 🎭 Tier 3: Speech-Style Mirroring

### Purpose
Subtly mirrors user's speech patterns to make responses feel more natural and personalized.

### Features

#### 1. **Filler Word Detection**
- Detects common fillers: "like", "uh", "um", "you know", "i mean"
- Calculates filler frequency
- Identifies user's most common fillers

#### 2. **Sentence Structure Analysis**
- Analyzes average sentence length
- Determines speech pace (fast/normal/slow)
- Tracks words per sentence

#### 3. **Subtle Mirroring**
- **Filler words**: Only mirrors if user uses fillers frequently (>5% of words)
- **Sentence length**: Adjusts response length to match user's pace
- **Pace matching**: Keeps responses concise for fast speakers, allows detail for slow speakers

**⚠️ Important:** Mirroring is subtle - only applied when natural and appropriate. Over-mirroring is avoided.

### Implementation

**File:** `Backend/user_style_analyzer.py`

**Key Functions:**
- `detect_filler_words()` - Analyzes filler word usage
- `analyze_sentence_structure()` - Analyzes sentence patterns
- `apply_speech_style_mirroring()` - Applies subtle mirroring (in response_model.py)

**Usage:**
```python
from user_style_analyzer import detect_filler_words, analyze_sentence_structure

filler_info = detect_filler_words(user_messages)
# Returns: {"filler_frequency": 0.08, "common_fillers": ["like", "you know"]}

sentence_info = analyze_sentence_structure(user_messages)
# Returns: {"pace": "fast", "avg_words_per_sentence": 7}
```

---

## 🔄 Integration Flow

### How It All Works Together

1. **User sends message** → `/api/respond` endpoint
2. **Emotion detection** → Detects emotion from text
3. **Get conversation summary** → Retrieves rolling context
4. **Get user style** → Analyzes speech patterns
5. **Generate response** → AI generates with all context
6. **Apply style mirroring** → Subtly mirrors user's style
7. **Apply therapeutic wrapper** → Ensures safety and empathy
8. **Save to database** → Stores for future context
9. **Update summary** → Updates conversation memory (every 5 messages)

### Example Flow

```
User: "I'm like, really stressed about work, you know?"

1. Emotion detected: "anxiety"
2. Conversation summary: "User has been expressing anxiety. Topics: work, stress."
3. User style: 
   - Fillers: ["like", "you know"] (frequency: 0.12)
   - Pace: "fast" (avg 6 words/sentence)
4. AI generates: "I understand work stress can be overwhelming..."
5. Style mirroring: Adds subtle "you know" if appropriate
6. Therapeutic wrapper: Ensures empathy, removes any directives
7. Final response: "I understand work stress can be overwhelming, you know? 
   Have you considered what specifically about work is causing this stress?"
```

---

## 📊 Configuration

### Therapeutic Wrapper
- **Max regenerations**: 2 (default)
- **Empathy validation**: Automatic if missing
- **Directive softening**: Automatic

### Conversation Memory
- **Summarization frequency**: Every 5 messages (configurable)
- **Emotional trajectory**: Last 10 emotions stored
- **Key topics**: Top 5 topics extracted
- **Cache TTL**: 1 hour

### Speech-Style Mirroring
- **Filler threshold**: 5% frequency (only mirrors if above)
- **Mirroring probability**: 30% chance (subtle)
- **Pace matching**: Automatic based on sentence length

---

## 🧪 Testing

### Test Therapeutic Wrapper
```python
from therapeutic_wrapper import wrap_therapeutic_response

# Test empathy check
response = "Try meditation."
wrapped = wrap_therapeutic_response(response, "I'm stressed")
assert "understand" in wrapped.lower() or "hear" in wrapped.lower()

# Test directive softening
response = "You must exercise."
wrapped = wrap_therapeutic_response(response, "I'm tired")
assert "must" not in wrapped.lower()
```

### Test Conversation Memory
```python
from conversation_memory import get_conversation_summary

summary = await get_conversation_summary(user_id, conversation_id)
assert "emotional_trajectory" in summary
assert "user_context" in summary
```

### Test Speech-Style Mirroring
```python
from user_style_analyzer import detect_filler_words

messages = ["I'm like, really stressed, you know?", "It's like, so hard"]
fillers = detect_filler_words(messages)
assert fillers["filler_frequency"] > 0.05
assert "like" in fillers["common_fillers"]
```

---

## 🚀 Benefits

### Safety
- ✅ Prevents diagnostic language
- ✅ Ensures empathy in every response
- ✅ Softens potentially harmful directives
- ✅ Maintains therapeutic boundaries

### Personalization
- ✅ Remembers emotional trajectory
- ✅ Tracks conversation topics
- ✅ Adapts to user's communication style
- ✅ Feels like talking to someone who knows you

### Naturalness
- ✅ Subtle style mirroring
- ✅ Matches user's pace
- ✅ Feels human, not robotic
- ✅ Maintains therapeutic quality

---

## 📝 Notes

1. **Subtlety is key** - Speech-style mirroring is intentionally subtle to avoid sounding unnatural
2. **Safety first** - Therapeutic wrapper always runs, even if it means regenerating responses
3. **Performance** - Conversation summaries are cached to avoid database overhead
4. **Graceful degradation** - All features work independently - if one fails, others continue

---

## 🔮 Future Enhancements

- [ ] Voice sample transcription for audio-based filler detection
- [ ] More sophisticated emotional trajectory analysis
- [ ] Multi-turn conversation context (beyond recent messages)
- [ ] User preference learning (what responses work best)
- [ ] A/B testing for response effectiveness

