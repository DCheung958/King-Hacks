# Crisis Safety Layer

## Overview

The crisis safety layer is a **Priority 1** feature that protects users ethically and legally by detecting crisis situations and providing appropriate safe responses.

---

## 🛡️ Crisis Detection

### Detection Methods

#### 1. **Pattern-Based Detection**
- Uses regex patterns to detect crisis language
- Examples:
  - "kill myself", "suicide", "end my life"
  - "want to die", "no reason to live"
  - "hurt myself", "self harm"

#### 2. **Keyword-Based Detection**
- Scans for crisis-related keywords
- Categorized by severity level:
  - **Critical**: Immediate life-threatening
  - **High**: Severe crisis indicators
  - **Medium**: Moderate crisis indicators
  - **Low**: Concerning but not immediate

#### 3. **Emotion-Based Triggers**
- Combines emotion detection with crisis patterns
- High-confidence sadness/fear/anger can trigger crisis detection
- Works in conjunction with pattern/keyword detection

---

## 🚨 Crisis Levels

### Critical Level
**Triggers:**
- Direct suicide statements
- Self-harm language
- Life-threatening statements

**Response:**
- Immediate override of AI response
- Provides crisis helpline numbers
- Encourages emergency services contact
- Logs incident for monitoring

**Example Triggers:**
- "I want to kill myself"
- "I'm going to end my life"
- "I'm going to hurt myself"

### High Level
**Triggers:**
- Strong suicidal ideation
- Hopelessness statements
- Severe depression indicators

**Response:**
- Overrides AI response
- Provides crisis resources
- Encourages professional help
- Logs incident

**Example Triggers:**
- "I don't want to live anymore"
- "Life isn't worth it"
- "Everyone would be better without me"

### Medium Level
**Triggers:**
- Suicidal thoughts (not immediate)
- Feeling trapped
- Desperation

**Response:**
- Overrides AI response
- Provides support resources
- Encourages professional help
- Does not log (privacy)

**Example Triggers:**
- "I have thoughts of suicide"
- "I don't see a way out"
- "I feel trapped"

### Low Level
**Triggers:**
- Concerning but not immediate
- General distress
- Struggling statements

**Response:**
- Does not override AI response
- Adds supportive context
- Encourages self-care
- Does not log

**Example Triggers:**
- "I'm very depressed"
- "I'm struggling"
- "Having a hard time"

---

## 🔄 Integration Flow

1. **User sends message** → Text received
2. **Emotion detected** → For crisis context
3. **Crisis detection runs** → Pattern + keyword + emotion analysis
4. **If crisis detected:**
   - Check crisis level
   - Get safe response template
   - Override AI response if needed
   - Log incident if critical/high
5. **Return safe response** → With crisis resources

---

## 📊 Crisis Response Templates

### Critical Response
```
I'm really concerned about what you've shared. Your life has value, and there are people who want to help you right now.

Please reach out to a crisis helpline immediately:
• National Suicide Prevention Lifeline: 988 (US)
• Crisis Text Line: Text HOME to 741741
• International Association for Suicide Prevention: [link]

If you're in immediate danger, please call emergency services (911 in US, 999 in UK, etc.).
```

### High Response
```
I'm very concerned about what you're experiencing. It sounds like you're going through an extremely difficult time.

Please know that you're not alone, and there are resources available to help:
• Crisis helpline: 988 (US) or your local crisis line
• Crisis Text Line: Text HOME to 741741
• Speak with a mental health professional or your doctor
```

### Medium Response
```
I hear that you're going through a really tough time right now. It's important to take these feelings seriously.

I want to encourage you to reach out for support:
• Consider speaking with a mental health professional
• Reach out to trusted friends or family members
• Contact a crisis helpline if you need immediate support
```

---

## 🔍 Detection Examples

### Example 1: Critical Crisis
**Input:** "I want to kill myself"
**Detection:**
- Pattern: ✓ (matches "kill myself")
- Keyword: ✓ ("kill myself")
- Level: CRITICAL
**Action:** Override response, provide crisis resources, log incident

### Example 2: High Crisis
**Input:** "I don't want to live anymore. Everyone would be better without me."
**Detection:**
- Pattern: ✓ ("don't want to live")
- Keyword: ✓ ("better without me")
- Level: HIGH
**Action:** Override response, provide resources, log incident

### Example 3: Medium Crisis
**Input:** "I've been having thoughts of suicide lately"
**Detection:**
- Pattern: ✓ ("thoughts of suicide")
- Level: MEDIUM
**Action:** Override response, provide resources, no logging

### Example 4: Emotion-Based
**Input:** "I'm feeling really sad and hopeless" (emotion: sadness, confidence: 0.95)
**Detection:**
- Emotion: ✓ (high-confidence sadness)
- Level: LOW
**Action:** Add supportive context, no override

---

## 📈 Statistics & Monitoring

The crisis detector tracks:
- Total crisis detections
- Detections by level (Critical/High/Medium/Low)
- Can be used for monitoring and improvement

**Access:**
```python
from crisis_detector import get_crisis_stats

stats = get_crisis_stats()
# Returns: {"total_detections": 5, "by_level": {...}}
```

---

## ⚖️ Legal & Ethical Protection

### Why This Matters

1. **Legal Protection:**
   - Demonstrates duty of care
   - Shows proactive crisis intervention
   - Provides audit trail for incidents

2. **Ethical Protection:**
   - Ensures users get appropriate help
   - Prevents AI from giving harmful advice
   - Connects users to professional resources

3. **User Safety:**
   - Immediate crisis response
   - Professional resource connection
   - Appropriate escalation

---

## 🛠️ Implementation

**File:** `Backend/crisis_detector.py`

**Key Functions:**
- `detect_crisis()` - Main detection function
- `detect_crisis_keywords()` - Keyword detection
- `detect_crisis_patterns()` - Pattern detection
- `check_emotion_crisis()` - Emotion-based triggers
- `get_crisis_response()` - Get safe response
- `should_log_crisis_incident()` - Determine if logging needed

**Integration:**
- Automatically runs in `/api/respond` endpoint
- Runs before AI response generation
- Overrides response if critical/high/medium detected

---

## 🔐 Privacy & Logging

### What Gets Logged
- **Critical/High levels:** Logged for safety monitoring
- **Medium/Low levels:** Not logged (privacy)

### What Gets Logged
- Crisis level
- Detection reasons (keywords/patterns matched)
- Timestamp
- User ID (if available)

### Privacy Considerations
- Logs are for safety monitoring only
- Should be stored securely
- Should comply with privacy regulations
- Consider anonymization for analytics

---

## 🚀 Future Enhancements

- [ ] Multi-language crisis detection
- [ ] Context-aware detection (conversation history)
- [ ] Integration with crisis helpline APIs
- [ ] Real-time monitoring dashboard
- [ ] Machine learning-based detection improvements
- [ ] Regional crisis resource customization

---

## ⚠️ Important Notes

1. **Not a replacement for professional help** - Always encourages professional resources
2. **False positives possible** - May detect non-crisis situations
3. **Regular updates needed** - Crisis language evolves
4. **Compliance required** - Must comply with local regulations
5. **Human review recommended** - For critical detections

---

## 📞 Crisis Resources

### United States
- **988 Suicide & Crisis Lifeline:** 988
- **Crisis Text Line:** Text HOME to 741741

### United Kingdom
- **Samaritans:** 116 123
- **Crisis Text Line UK:** Text SHOUT to 85258

### International
- **International Association for Suicide Prevention:** https://www.iasp.info/resources/Crisis_Centres/

---

**Remember:** This is a safety feature, not a replacement for professional mental health care. Always encourage users to seek professional help when needed.

