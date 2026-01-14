# User Voice & Style Emulation Feature

## Overview

The Echocare backend now supports **personalized voice and style emulation**, allowing the AI chatbot to adapt its responses to match the user's communication style, speech patterns, and preferences - making conversations feel like talking to a friend who gives therapeutic advice.

## Features Implemented

### 1. User Speech Style Analysis ✅

**Module:** `user_style_analyzer.py`

Analyzes user messages to extract:
- **Common phrases** - Frequently used expressions and phrases
- **Speech style** - Formality level (casual/neutral/formal)
- **Punctuation style** - Enthusiastic, thoughtful, or normal
- **Common connectors** - Words used to connect thoughts (but, and, so, etc.)
- **Key terms** - Important topics and keywords
- **Recent messages** - Context from recent conversations

**Functions:**
- `get_user_speech_style(user_id, limit_messages)` - Analyzes user's overall style
- `get_recent_user_messages(user_id, conversation_id, limit)` - Gets recent messages for context
- `extract_common_phrases(messages)` - Extracts frequently used phrases
- `analyze_speech_style(messages)` - Analyzes communication characteristics

### 2. Personalized Response Generation ✅

**Updated:** `response_model.py`

The AI response generation now:
- **Adapts formality level** - Matches user's communication style (casual/neutral/formal)
- **Uses common phrases** - Incorporates user's frequently used expressions
- **Considers recent context** - Uses recent messages for better continuity
- **Maintains therapeutic tone** - Keeps empathetic, supportive responses while matching style

**How it works:**
1. Analyzes user's speech patterns from message history
2. Builds style-aware prompts with user characteristics
3. Generates responses that match the user's communication style
4. Maintains therapeutic quality while feeling personal

### 3. Enhanced Voice Sample Upload ✅

**Updated:** `main.py` - `/api/voice-sample` endpoint

The voice upload endpoint now:
- **Tracks sample count** - Shows total samples uploaded by user
- **Provides suggestions** - Encourages uploading multiple varied samples
- **Guides users** - Suggests different emotions/topics for better voice capture
- **Returns feedback** - Includes `total_samples` and `suggestion` in response

**Response includes:**
```json
{
  "message": "Voice sample uploaded successfully (3 total samples)",
  "filename": "uuid-filename.webm",
  "file_size": 12345,
  "voice_id": "optional-voice-id",
  "total_samples": 3,
  "suggestion": "Excellent! You have 3 samples. Add a few more with different emotions for best results."
}
```

**Suggestions by sample count:**
- **1 sample:** "Great start! Upload 2-3 more varied samples (different emotions, topics) for better voice capture."
- **2 samples:** "Good progress! One more sample with varied tone would help capture your full voice style."
- **3-4 samples:** "Excellent! You have X samples. Add a few more with different emotions for best results."
- **5+ samples:** "Perfect! You have enough samples for great voice emulation."

### 4. Automatic Chat Transcript Storage ✅

**Already Implemented:** Messages are automatically saved when `user_id` is provided

**How it works:**
- When `user_id` is provided to `/api/respond`, messages are automatically saved
- Both user messages and AI responses are stored
- Emotions are tracked alongside messages
- Conversations are linked to user profiles
- Full conversation history is available via database endpoints

**Database Structure:**
- `users` - User profiles
- `conversations` - Conversation sessions (linked to users)
- `messages` - Individual messages (linked to conversations, includes emotions)
- `voice_samples` - Voice samples (linked to users)

## Usage

### For Response Generation

The `/api/respond` endpoint automatically uses user style if `user_id` is provided:

```python
POST /api/respond
{
  "text": "I'm feeling really stressed today",
  "emotion": "anxiety",  # optional
  "user_id": "uuid-here",  # optional but recommended
  "conversation_id": "uuid-here"  # optional
}
```

**Benefits:**
- If `user_id` provided → Uses personalized style
- If `user_id` not provided → Uses default style (still works)
- Graceful fallback if style analysis fails

### For Voice Upload

The `/api/voice-sample` endpoint encourages multiple samples:

```python
POST /api/voice-sample
Form data:
- file: audio file
- user_id: "uuid-here"  # optional but recommended
```

**Response includes:**
- Total sample count
- Suggestions for better voice capture
- Voice ID (if ElevenLabs cloning successful)

### For Frontend Integration

**Recommended Flow:**
1. User creates/gets user account
2. User uploads multiple voice samples (different emotions, topics)
3. User chats with system (provides `user_id` and `conversation_id`)
4. System automatically:
   - Saves all messages to database
   - Analyzes user's speech style
   - Generates personalized responses
   - Emulates user's voice style in responses

## Implementation Details

### Style Analysis

The style analyzer looks at:
- **30 most recent messages** (default, configurable)
- **Common phrases** (2-4 word phrases, appears 2+ times)
- **Formality indicators** (contractions, casual words, message length)
- **Punctuation patterns** (exclamations, questions, ellipses)
- **Connector words** (but, and, so, because, etc.)

### Prompt Engineering

The response generation uses style context:
- **Style context:** "Respond in a friendly, casual way" (matches user formality)
- **Common phrases:** "The person often says things like: 'you know', 'I mean', 'like that'"
- **Emotion context:** Includes detected emotion
- **Recent messages:** Used for conversation continuity

### Database Integration

All features require database to be set up (optional but recommended):
- User accounts for style tracking
- Message storage for style analysis
- Voice sample tracking
- Conversation history

**If database not available:**
- System still works (graceful fallback)
- Style analysis skipped (uses default style)
- Messages not saved (no persistence)

## Benefits

1. **Personalized Experience** - Responses match user's communication style
2. **Better Voice Emulation** - Multiple samples improve voice cloning quality
3. **Conversation Continuity** - Recent messages provide context
4. **Therapeutic Quality** - Maintains empathetic tone while being personal
5. **User Engagement** - Feels like talking to a friend who gives good advice

## Future Enhancements

Potential improvements:
- **Fine-tuned models** - Train models on user's specific style
- **Voice style mapping** - Link speech patterns to voice characteristics
- **Style evolution** - Track how user's style changes over time
- **Advanced NLP** - Use more sophisticated language analysis
- **Multi-modal style** - Combine text style with voice characteristics

## Testing

To test the features:
1. Create a user account via `/api/users`
2. Upload multiple voice samples with `user_id`
3. Send messages via `/api/respond` with `user_id`
4. Check responses - they should adapt to your communication style
5. Review style analysis via database queries

## Notes

- Style analysis requires database and message history
- More messages = better style analysis
- Multiple voice samples = better voice emulation
- All features work gracefully without database (fallback mode)
- Style analysis improves over time as more messages are saved
