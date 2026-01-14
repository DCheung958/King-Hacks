/**
 * Voice Service
 * Handles voice sample uploads for voice cloning
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload voice sample (stores locally, no cloning)
 * @param {Blob} audioBlob - Audio blob from MediaRecorder
 * @param {string} userId - Optional user ID
 * @returns {Promise<{message: string, filename: string, file_size: number}>}
 */
export async function uploadVoiceSample(audioBlob, userId = null) {
  try {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    if (userId) {
      formData.append('user_id', userId);
    }

    const response = await fetch(`${API_BASE_URL}/api/voice-sample`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set it with boundary
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      message: data.message,
      filename: data.filename,
      fileSize: data.file_size
    };
  } catch (error) {
    console.warn('Failed to upload voice sample to backend:', error);
    throw error; // Let caller handle the error
  }
}

/**
 * Batch upload and clone voice samples with ElevenLabs (saves credits)
 * @param {Blob[]} audioBlobs - Array of audio blobs from MediaRecorder
 * @param {string} userId - Optional user ID
 * @param {string} voiceName - Optional voice name
 * @returns {Promise<{message: string, voice_id: string, filenames: string[], total_samples: number}>}
 */
export async function batchCloneVoice(audioBlobs, userId = null, voiceName = null) {
  try {
    const formData = new FormData();
    
    // Add all files to form data
    audioBlobs.forEach((blob, index) => {
      formData.append('files', blob, `recording_${index}.webm`);
    });
    
    if (userId) {
      formData.append('user_id', userId);
    }
    
    if (voiceName) {
      formData.append('voice_name', voiceName);
    }

    const response = await fetch(`${API_BASE_URL}/api/voice-clone-batch`, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set it with boundary
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return {
      message: data.message,
      voiceId: data.voice_id,
      filenames: data.filenames,
      totalSamples: data.total_samples
    };
  } catch (error) {
    console.error('Failed to batch clone voice:', error);
    throw error;
  }
}
