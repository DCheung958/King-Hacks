import React, { useState, useCallback, useRef, useEffect } from 'react';
import { detectEmotion, generateResponse } from '../services/chatService';
import { synthesizeSpeech } from '../services/ttsService';
import './Chat.css';

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [detectedMood, setDetectedMood] = useState('Neutral');
  const [isMuted, setIsMuted] = useState(false);
  
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioRef = useRef(null);

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };
      
      recognition.onresult = (event) => {
        let interim = '';
        let finalText = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalText += transcript + ' ';
          } else {
            interim += transcript;
          }
        }
        
        setInterimTranscript(interim);
        
        if (finalText.trim()) {
          handleFinalTranscript(finalText.trim());
        }
      };
      
      recognitionRef.current = recognition;
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Audio visualization
  const visualizeAudio = () => {
    if (!analyserRef.current) return;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      if (!analyserRef.current) {
        const bars = document.querySelectorAll('.chat-audio-bar');
        bars.forEach(bar => {
          bar.style.height = '10%';
        });
        return;
      }
      
      animationFrameRef.current = requestAnimationFrame(draw);
      analyserRef.current.getByteFrequencyData(dataArray);
      
      const bars = document.querySelectorAll('.chat-audio-bar');
      if (bars.length > 0) {
        const step = Math.floor(bufferLength / bars.length);
        
        bars.forEach((bar, i) => {
          const value = dataArray[i * step] || 0;
          const height = Math.max(10, (value / 255) * 100);
          bar.style.height = `${height}%`;
        });
      }
    };
    
    draw();
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
        setupAudioVisualization();
      } catch (error) {
        console.error('Error starting speech recognition:', error);
      }
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const setupAudioVisualization = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;
      
      visualizeAudio();
    } catch (error) {
      console.error('Error setting up audio visualization:', error);
    }
  };


  const handleFinalTranscript = useCallback(async (text) => {
    if (!text.trim()) return;

    setIsProcessing(true);
    setError(null);
    setInterimTranscript('');

    try {
      // Add user message immediately
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        text: text.trim()
      };

      setMessages(prev => [...prev, userMessage]);

      // Detect emotion
      const emotionData = await detectEmotion(text.trim());
      // Format emotion name for display
      const emotionName = emotionData.emotion
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      setDetectedMood(emotionName);

      // Generate assistant response
      const response = await generateResponse(text.trim(), emotionData.emotion);
      
      // Add assistant message
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: response.responseText
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Synthesize speech
      const ttsResult = await synthesizeSpeech(response.responseText);
      setAudioUrl(ttsResult.audioUrl);
    } catch (err) {
      console.error('Error processing transcript:', err);
      setError('Failed to generate response. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  return (
    <div className="chat-page-new">
      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <div className="header-logo"></div>
          <div className="header-title">
            <h1 className="app-title">Echocare</h1>
            <p className="app-subtitle">Your personal therapy companion</p>
          </div>
        </div>
        <div className="header-icons">
          <button className="icon-button chat-icon">💬</button>
          <button className="icon-button settings-icon">⚙️</button>
        </div>
      </header>

      {/* Main Content */}
      <main className="chat-main">
        {/* Mood Detection */}
        <div className="mood-display">
          <span className="mood-label">Detected Mood:</span>
          <span className="mood-value">{detectedMood}</span>
        </div>

        {/* Audio Visualization Circle */}
        <div className="visualization-container">
          <div className={`visualization-circle ${isListening ? 'active' : ''}`}></div>
          
          {/* Audio Bars */}
          {isListening && (
            <div className="audio-bars-container">
              {Array.from({ length: 30 }).map((_, i) => (
                <div key={i} className="chat-audio-bar"></div>
              ))}
            </div>
          )}
        </div>

        {/* Instruction Text */}
        <p className="instruction-text">
          {isListening ? 'Listening...' : 'Tap the microphone to start speaking'}
        </p>

        {/* Control Buttons */}
        <div className="control-buttons">
          <button 
            className={`control-button speaker-button ${isMuted ? 'muted' : ''}`}
            onClick={toggleMute}
            aria-label={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? '🔇' : '🔊'}
          </button>
          <button
            className={`control-button mic-button ${isListening ? 'active' : ''}`}
            onClick={isListening ? stopListening : startListening}
            aria-label={isListening ? 'Stop' : 'Start speaking'}
          >
            🎤
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="error-message">{error}</div>
        )}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="processing-indicator">Processing...</div>
        )}
      </main>

      {/* Conversation Section */}
      <div className="conversation-section">
        <h2 className="conversation-title">Conversation</h2>
        <div className="conversation-messages">
          {messages.length === 0 ? (
            <div className="empty-conversation">
              <p>Your conversation will appear here</p>
            </div>
          ) : (
            messages.map(message => (
              <div 
                key={message.id} 
                className={`conversation-message ${message.role}`}
              >
                <div className="message-content">
                  {message.text}
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Hidden Audio Player */}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          autoPlay
          muted={isMuted}
          onEnded={() => setAudioUrl(null)}
        />
      )}
    </div>
  );
};

export default Chat;
