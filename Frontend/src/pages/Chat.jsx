import React, { useState, useCallback } from 'react';
import VoiceRecorder from '../components/VoiceRecorder';
import SpeechInput from '../components/SpeechInput';
import ChatWindow from '../components/ChatWindow';
import AudioPlayer from '../components/AudioPlayer';
import { generateResponse } from '../services/chatService';
import { synthesizeSpeech } from '../services/ttsService';
import { uploadVoiceSample } from '../services/voiceService';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleRecordingComplete = useCallback(async (blob) => {
    // Upload voice sample to backend for voice cloning (future use)
    try {
      setIsProcessing(true);
      setError(null);
      const result = await uploadVoiceSample(blob);
      console.log('Voice sample uploaded:', result);
      // Note: In the current flow, we still use SpeechInput for transcription
      // This voice sample is stored for future voice cloning
    } catch (err) {
      console.error('Failed to upload voice sample:', err);
      setError('Failed to upload voice sample. The recording will still be used for transcription.');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const handleFinalTranscript = useCallback(async (text) => {
    if (!text.trim()) return;

    setIsProcessing(true);
    setError(null);

    try {
      // Add user message immediately
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        text: text.trim()
      };

      setMessages(prev => [...prev, userMessage]);

      // Generate assistant response from backend (with fallback)
      const response = await generateResponse(text.trim());
      
      // Add assistant message
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: response.responseText
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Synthesize speech from backend (with fallback)
      const ttsResult = await synthesizeSpeech(response.responseText);
      setAudioUrl(ttsResult.audioUrl);
    } catch (err) {
      console.error('Error processing transcript:', err);
      setError('Failed to generate response. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  return (
    <div className="chat-page">
      <div className="chat-container">
        <h1 className="chat-title">Echocare</h1>
        <p className="chat-subtitle">Your therapeutic conversation companion</p>
        
        {error && (
          <div className="error-banner">
            <p>{error}</p>
          </div>
        )}
        
        {isProcessing && (
          <div className="processing-indicator">
            <p>Processing...</p>
          </div>
        )}
        
        <ChatWindow messages={messages} />
        
        <div className="input-section">
          <SpeechInput onFinalTranscript={handleFinalTranscript} />
          <div className="divider">or</div>
          <VoiceRecorder onRecordingComplete={handleRecordingComplete} />
        </div>
        
        <AudioPlayer audioUrl={audioUrl} />
      </div>
    </div>
  );
};

export default Chat;

