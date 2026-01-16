# Prompt Engineering Guide - LLaMA 3.1 Response Generation

This document explains all files that contribute to how the LLaMA 3.1 model generates responses.

## Core Files That Build the Prompt

### 1. **`response_model.py`** - Main Prompt Engineering
   **Purpose**: The primary file that constructs the LLaMA 3.1 prompt and orchestrates all context.
   
   **Key Functions**:
   - `generate_therapeutic_response()` - Main function that builds the complete prompt
   - `get_emotional_intensity()` - Determines response length based on emotion
   - Builds the system instruction (detailed friend/family/therapist persona)
   - Assembles conversation history in LLaMA chat format
   - Combines all context sources into the final prompt

   **Prompt Structure**:
   ```
   System Message: [System Instruction + Emotional Shifts + Crisis Context + Repetition Warnings]
   User Message 1: [Past conversation - up to 8 messages]
   Assistant Message 1: [Past responses - up to 8 messages]
   ...
   User Message (Current): [Current user input + Context string]
   ```

### 2. **`conversation_memory.py`** - Conversation Summarization
   **Purpose**: Maintains long-term conversation context and emotional trajectory tracking.
   
   **Key Functions**:
   - `get_conversation_summary()` - Gets conversation summary from database
   - `_build_summary_from_messages()` - Creates summary with emotional trajectory
   - `_extract_key_topics()` - Extracts important topics from conversations
   - `_build_user_context()` - Builds natural language context summary
   - `update_conversation_summary()` - Updates summary when new messages arrive

   **What It Provides**:
   - Emotional trajectory (last 10 emotions)
   - Key topics discussed
   - User context summary
   - Message count and conversation status

   **Currently Active**: ✅ YES - Used in `main.py` line 360-375

### 3. **`persona_config.py`** - Voice Persona Configuration
   **Purpose**: Defines different speaking styles (Friend, Therapist, Family).
   
   **Key Functions**:
   - `get_persona_config()` - Gets persona configuration
   - `get_persona_prompt_style()` - Returns prompt instructions for persona
   - `adjust_response_for_persona()` - Post-processes response for persona characteristics

   **Personas Available**:
   - `friend` - Casual, warm, conversational
   - `therapist` - Professional, reflective, question-focused
   - `family` - Encouraging, action-oriented, motivating

   **Currently Active**: ✅ YES - Used in `response_model.py` if persona is provided

### 4. **`user_style_analyzer.py`** - User Speech Style Analysis
   **Purpose**: Analyzes user's speech patterns to mirror their style subtly.
   
   **Key Functions**:
   - `extract_common_phrases()` - Finds phrases user uses frequently
   - `detect_filler_words()` - Detects filler words and patterns
   - `analyze_sentence_structure()` - Analyzes sentence length and pacing
   - `get_user_speech_style()` - Main function that returns style analysis

   **What It Provides**:
   - Common phrases user uses
   - Filler word frequency
   - Sentence structure (pace, length)
   - Formality level

   **Currently Active**: ✅ YES - Used in `main.py` line 383 to get user style

### 5. **`main.py`** - API Endpoint & Context Assembly
   **Purpose**: The FastAPI endpoint that assembles all context before calling the model.
   
   **Key Functions**:
   - `/api/respond` endpoint - Receives requests and builds context
   - Fetches conversation history from database (lines 387-402)
   - Gets conversation summary from `conversation_memory.py` (lines 360-375)
   - Gets user style from `user_style_analyzer.py` (line 383)
   - Passes everything to `generate_therapeutic_response()`

   **Context Sources It Fetches**:
   - Conversation history (last 10 messages) ✅
   - Conversation summary (emotional trajectory, topics) ✅
   - User speech style (phrases, fillers, structure) ✅
   - Last assistant message (to avoid repetition) ✅

## Conversation Memory Status

### ✅ **YES - The system IS remembering previous conversations!**

**How it works:**

1. **Conversation History** (Immediate Context):
   - Fetches last **10 messages** from database (`main.py` line 390)
   - Passed directly to LLaMA as chat history (up to last 8 messages in the prompt)
   - Includes both user and assistant messages in chronological order
   - Format: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]`

2. **Conversation Summary** (Long-term Context):
   - Built by `conversation_memory.py` from all messages in conversation
   - Updated every 5 messages (`main.py` line 466)
   - Includes:
     - Emotional trajectory (last 10 emotions)
     - Key topics discussed
     - User context summary (natural language)
   - Added to system instruction as context

3. **Emotional Shift Detection**:
   - Tracks emotional transitions in `response_model.py` (lines 333-350)
   - Detects when user moves from one emotion to another
   - Adds explicit instruction to acknowledge the shift

## Prompt Building Flow

```
User sends message
    ↓
main.py /api/respond endpoint
    ↓
1. Get conversation history (last 10 messages) from database
2. Get conversation summary from conversation_memory.py
3. Get user speech style from user_style_analyzer.py
4. Get last assistant message (for repetition avoidance)
    ↓
response_model.py generate_therapeutic_response()
    ↓
Builds LLaMA 3.1 chat format:
    System: [Base System Instruction + Persona + Conversation Summary + Emotional Shifts + Crisis Context]
    User: [Message 1 from history]
    Assistant: [Response 1 from history]
    ...
    User: [Current message + Style Context + Warmth Adjustment]
    ↓
LLaMA 3.1 generates response
    ↓
Post-processing:
    - Remove prompt prefixes
    - Apply persona adjustments (if persona_config.py used)
    - Apply speech style mirroring (if user_style_analyzer.py used)
    - Apply therapeutic wrapper (therapeutic_wrapper.py)
    ↓
Return response
```

## Files That Modify the Prompt (In Order)

1. **`response_model.py`** (lines 399-419):
   - Defines base system instruction (friend/family/therapist persona)

2. **`conversation_memory.py`** (called from `main.py` line 360):
   - Adds conversation summary context
   - Adds emotional trajectory

3. **`persona_config.py`** (if persona specified):
   - Overrides default system instruction with persona-specific style

4. **`user_style_analyzer.py`** (called from `main.py` line 383):
   - Adds user's speech style context
   - Adds common phrases
   - Adds formality level

5. **`response_model.py`** (lines 333-350):
   - Detects emotional shifts
   - Adds emotional shift context

6. **`crisis_detector.py`** (implicitly):
   - Adds crisis context if crisis detected

7. **`response_model.py`** (lines 535-551):
   - Assembles conversation history (last 8 messages)
   - Adds all context to system message
   - Adds current user message

## Configuration Files

- **`persona_config.py`** - Persona definitions
- **`prosody_config.py`** - Voice prosody settings (for TTS, not prompt)
- **`therapeutic_wrapper.py`** - Safety wrapper (post-processing, not prompt)

## Current Limitations

- **Conversation history**: Limited to last 8-10 messages (due to token limits)
- **Summary**: Updates every 5 messages (configurable in `main.py` line 466)
- **Emotional trajectory**: Tracks last 10 emotions
- **Key topics**: Extracts top 5 topics

## Testing Memory

To verify conversation memory is working:
1. Send a message about a topic
2. Wait for response
3. Send another message referencing the previous topic
4. The model should remember and reference the previous conversation

## Improving Memory

To increase memory capacity:
1. Increase `limit=10` in `main.py` line 390 (conversation history)
2. Increase `limit=100` in `conversation_memory.py` line 56 (summary scope)
3. Adjust `recent_history = conversation_history[-8:]` in `response_model.py` line 536
4. Note: More context = slower generation and higher token usage

