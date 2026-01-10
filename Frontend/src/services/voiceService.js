/**
 * Voice Service
 * Handles voice sample uploads for voice cloning
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Upload voice sample for cloning
 * @param {Blob} audioBlob - Audio blob from MediaRecorder
 * @returns {Promise<{message: string, filename: string, file_size: number}>}
 */
export async function uploadVoiceSample(audioBlob) {
  try {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');

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

