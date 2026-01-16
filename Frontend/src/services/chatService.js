/**
 * Chat Service
 * Connects to backend API for emotion detection and response generation
 * Falls back to mock behavior if backend is unavailable
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Fallback mock responses
const MOCK_RESPONSES = [
  {
    emotion: "calm",
    responseText: "I'm really glad you shared that. Take a deep breath with me."
  },
  {
    emotion: "supportive",
    responseText: "Thank you for trusting me with this. How are you feeling right now?"
  },
  {
    emotion: "empathetic",
    responseText: "That sounds difficult. Remember, you're not alone in this. Let's work through it together."
  },
  {
    emotion: "reassuring",
    responseText: "It's okay to feel this way. Emotions are valid, and we can explore them safely here."
  },
  {
    emotion: "gentle",
    responseText: "I hear you. Would you like to tell me more about what's on your mind?"
  }
];

/**
 * Detect emotion from user text
 * @param {string} text - User input text
 * @returns {Promise<{emotion: string, confidence: number}>}
 */
export async function detectEmotion(text) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/emotion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      emotion: data.emotion,
      confidence: data.confidence || 0.0
    };
  } catch (error) {
    console.warn('Failed to detect emotion from backend, using mock:', error);
    // Fallback: simple mock detection
    const textLower = text.toLowerCase();
    if (textLower.includes('sad') || textLower.includes('unhappy')) {
      return { emotion: 'sadness', confidence: 0.6 };
    } else if (textLower.includes('anxious') || textLower.includes('worried')) {
      return { emotion: 'anxiety', confidence: 0.6 };
    } else if (textLower.includes('angry') || textLower.includes('mad')) {
      return { emotion: 'anger', confidence: 0.6 };
    }
    return { emotion: 'calm', confidence: 0.6 };
  }
}

/**
 * Generate therapeutic response from user text
 * @param {string} userText - User input text
 * @param {string} [emotion] - Detected emotion (optional, will be detected if not provided)
 * @param {string} [userId] - User ID (optional, for saving conversations)
 * @param {string} [conversationId] - Conversation ID (optional, for saving conversations)
 * @returns {Promise<{emotion: string, responseText: string}>}
 */
export async function generateResponse(userText, emotion = null, userId = null, conversationId = null) {
  try {
    // Detect emotion if not provided
    let detectedEmotion = emotion;
    if (!detectedEmotion) {
      const emotionData = await detectEmotion(userText);
      detectedEmotion = emotionData.emotion;
    }

    // Build request body
    const requestBody = { 
      text: userText,
      emotion: detectedEmotion 
    };

    // Add user_id and conversation_id as query parameters if provided
    let url = `${API_BASE_URL}/api/respond`;
    const params = new URLSearchParams();
    if (userId) {
      params.append('user_id', userId);
    }
    if (conversationId) {
      params.append('conversation_id', conversationId);
    }
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    // Generate response from backend
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      emotion: data.emotion || detectedEmotion,
      responseText: data.response_text
    };
  } catch (error) {
    console.warn('Failed to generate response from backend, using mock:', error);
    // Fallback to mock response
    const index = userText.length % MOCK_RESPONSES.length;
    return MOCK_RESPONSES[index];
  }
}
