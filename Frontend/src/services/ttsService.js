/**
 * TTS Service
 * Connects to backend API for speech synthesis
 * Falls back to mock behavior if backend is unavailable
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Minimal silent WAV file as data URI (fallback)
const SILENT_AUDIO_DATA_URI = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";

/**
 * Synthesize speech from text with prosody-aware settings
 * @param {string} text - Text to synthesize
 * @param {string} [voiceId] - Optional voice ID for ElevenLabs
 * @param {string} [emotion] - Emotion for prosody adjustment (sadness, fear, anger, joy, etc.)
 * @returns {Promise<{audioUrl: string, duration?: number}>}
 */
export async function synthesizeSpeech(text, voiceId = null, emotion = null) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        text,
        voice_id: voiceId,
        emotion: emotion  // Pass emotion for prosody-aware synthesis
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      audioUrl: data.audio_url,
      duration: data.duration
    };
  } catch (error) {
    console.warn('Failed to synthesize speech from backend, using fallback:', error);
    // Fallback to local sample or silent audio
    return {
      audioUrl: "/sample.mp3",  // Try local file first
      // If /sample.mp3 doesn't exist, AudioPlayer will use the silent fallback
    };
  }
}

