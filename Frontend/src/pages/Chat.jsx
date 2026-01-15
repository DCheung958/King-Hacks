import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { detectEmotion, generateResponse } from '../services/chatService';
import { synthesizeSpeech } from '../services/ttsService';
import elephantLogo from '../assets/elephant-logo.png';
import './Chat.css';

const Chat = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [messages, setMessages] = useState([]);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [detectedMood, setDetectedMood] = useState('Neutral');
  const [isMuted, setIsMuted] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [showTextInput, setShowTextInput] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [pastConversations, setPastConversations] = useState([]);
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [currentConversationId, setCurrentConversationId] = useState(null);

  const recognitionRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioRef = useRef(null);
  const textInputRef = useRef(null);
  const visualizationRef = useRef(null);
  const [orbState, setOrbState] = useState('ready'); // 'ready', 'listening', 'speaking', 'silent'

  // Check if user has cloned their voice and get voice name
  useEffect(() => {
    const voiceId = localStorage.getItem('voice_id');
    const storedVoiceName = localStorage.getItem('voice_name');
    setHasVoiceCloned(!!voiceId);
    setVoiceName(storedVoiceName);
  }, [showVoiceProfileModal]); // Refresh when modal closes

  // Reset modal state when returning to chat page
  useEffect(() => {
    // If we're on the chat page and coming from voice profile, close modal
    if (location.pathname === '/chat') {
      // Check if we're returning from voice profile (no state means we navigated back)
      if (location.state === null || location.state === undefined) {
        setShowVoiceProfileModal(false);
      }
    }
  }, [location]);

  // Handle audio playback when audioUrl changes
  useEffect(() => {
    if (audioUrl && audioRef.current) {
      console.log('Audio URL set, attempting to play:', audioUrl);
      setAudioError(null);
      
      const playAudio = async () => {
        try {
          // Reset audio element
          audioRef.current.load();
          
          // Wait for audio to be ready
          const handleCanPlay = async () => {
            try {
              if (!isMuted && audioRef.current) {
                await audioRef.current.play();
                console.log('Audio playing successfully');
                setAudioError(null);
              } else {
                console.log('Audio muted, not playing');
              }
            } catch (playError) {
              console.error('Error playing audio:', playError);
              setAudioError('Could not play audio automatically. Click the play button below.');
              // Some browsers require user interaction
              if (playError.name === 'NotAllowedError') {
                console.warn('Autoplay blocked. User interaction required.');
              }
            }
            // Remove listener after first play attempt
            audioRef.current.removeEventListener('canplay', handleCanPlay);
          };
          
          audioRef.current.addEventListener('canplay', handleCanPlay);
          
          // Also try immediate play (in case it's already loaded)
          if (audioRef.current.readyState >= 2) {
            handleCanPlay();
          }
        } catch (error) {
          console.error('Error loading audio:', error);
          setAudioError('Failed to load audio file.');
        }
      };
      
      playAudio();
    }
  }, [audioUrl, isMuted]);

  const playAudioManually = () => {
    if (audioRef.current && audioUrl) {
      audioRef.current.play().catch(err => {
        console.error('Manual play error:', err);
        setAudioError('Could not play audio: ' + err.message);
      });
    }
  };

  // Initialize speech recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
        setOrbState('listening');
      };
      recognition.onend = () => {
        setIsListening(false);
        setOrbState('ready');
        // Reset orb styles when recognition ends
        setTimeout(() => {
          if (visualizationRef.current) {
            visualizationRef.current.style.transform = '';
            visualizationRef.current.style.boxShadow = '';
            visualizationRef.current.style.setProperty('--inner-glow-alpha', '0');
            visualizationRef.current.style.setProperty('--inner-glow-scale', '1');
          }
        }, 300);
      };
      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setOrbState('ready');
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
      if (visualizationRef.current) {
        visualizationRef.current.style.transform = '';
        visualizationRef.current.style.boxShadow = '';
        visualizationRef.current.style.setProperty('--inner-glow-alpha', '0');
        visualizationRef.current.style.setProperty('--inner-glow-scale', '1');
      }
    };
  }, []);

  // Audio visualization with orb reactivity
  const visualizeAudio = () => {
    if (!analyserRef.current || !visualizationRef.current) return;

    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const timeDataArray = new Uint8Array(analyserRef.current.fftSize);

    const draw = () => {
      if (!analyserRef.current || !visualizationRef.current) {
        const bars = document.querySelectorAll('.chat-audio-bar');
        bars.forEach(bar => {
          bar.style.height = '8px';
          bar.style.opacity = '0.5';
        });
        return;
      }

      animationFrameRef.current = requestAnimationFrame(draw);

      // Get frequency data for bars
      analyserRef.current.getByteFrequencyData(dataArray);

      // Get time domain data for orb reactivity (amplitude)
      analyserRef.current.getByteTimeDomainData(timeDataArray);

      // Calculate average amplitude for orb reactivity
      let sum = 0;
      for (let i = 0; i < timeDataArray.length; i++) {
        const value = Math.abs(timeDataArray[i] - 128);
        sum += value;
      }
      const averageAmplitude = sum / timeDataArray.length;
      const normalizedAmplitude = Math.min(1, averageAmplitude / 128); // Normalize to 0-1

      // Update orb based on audio amplitude
      if (isListening && normalizedAmplitude > 0.05) {
        setOrbState('speaking');

        // Scale orb based on amplitude (subtle breathing + audio response)
        const baseScale = 1.0;
        const audioScale = 1.0 + (normalizedAmplitude * 0.7); // Scale up to 30% based on audio
        const totalScale = baseScale * audioScale;
        visualizationRef.current.style.transform = `scale(${totalScale})`;

        // much brighter, multi-layered glow that grows with amplitude
        const glowAlpha = 0.3 + normalizedAmplitude * 0.7; // 0.3 to 1.0
        const outerGlow = 20 + normalizedAmplitude * 500; // px for outer blur
        visualizationRef.current.style.boxShadow = `0 18px 56px rgba(32,178,170,${Math.min(0.9, glowAlpha)}), 0 0 ${outerGlow}px rgba(32,178,170,${Math.min(0.75, glowAlpha * 0.85)})`;

        // Set inner glow via CSS variables for smoother, GPU-accelerated transitions
        const innerAlpha = Math.min(1, 0.12 + normalizedAmplitude * 1.05);
        const innerScale = 1 + normalizedAmplitude * 2; // up to ~1.26
        visualizationRef.current.style.setProperty('--inner-glow-alpha', innerAlpha.toString());
        visualizationRef.current.style.setProperty('--inner-glow-scale', innerScale.toString());
      } else if (isListening) {
        setOrbState('listening');
        // Reset to default listening state
        visualizationRef.current.style.transform = '';
        visualizationRef.current.style.boxShadow = '';
        visualizationRef.current.style.setProperty('--inner-glow-alpha', '0.2');
        visualizationRef.current.style.setProperty('--inner-glow-scale', '1');
      }

      // Update audio bars - circular arrangement
      const bars = document.querySelectorAll('.chat-audio-bar');
      if (bars.length > 0) {
        // Use a range of frequencies for more organic feel
        const startFreq = 0;
        const endFreq = Math.floor(bufferLength * 0.3); // Use lower frequencies for smoother visualization
        const freqRange = endFreq - startFreq;
        const step = Math.floor(freqRange / bars.length);

        bars.forEach((bar, i) => {
          const freqIndex = startFreq + (i * step);
          const value = dataArray[freqIndex] || 0;
          // Scale height more gently - max around 20-25px for subtle effect
          const height = Math.max(8, Math.min(25, (value / 255) * 25));
          bar.style.height = `${height}px`;
          // Add subtle opacity variation for softer feel
          const opacity = 0.5 + (value / 255) * 0.5;
          bar.style.opacity = opacity;
        });
      }
    };

    draw();
  };

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        setOrbState('listening');
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
      setOrbState('ready');
      // Reset orb styles after a short delay
      setTimeout(() => {
        if (visualizationRef.current) {
          visualizationRef.current.style.transform = '';
          visualizationRef.current.style.boxShadow = '';
          visualizationRef.current.style.setProperty('--inner-glow-alpha', '0');
          visualizationRef.current.style.setProperty('--inner-glow-scale', '1');
        }
      }, 300);
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

  // Create a new conversation
  const createNewConversation = async () => {
    const userId = localStorage.getItem('user_id');
    if (!userId) return null;

    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ user_id: userId })
      });

      if (response.ok) {
        const data = await response.json();
        return data.id;
      }
    } catch (err) {
      console.error('Error creating conversation:', err);
    }
    return null;
  };

  // Save message to database
  const saveMessage = async (conversationId, role, text, emotion = null) => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      await fetch(`${API_BASE_URL}/api/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          role: role,
          text: text,
          emotion: emotion
        })
      });
    } catch (err) {
      console.error('Error saving message:', err);
      // Don't throw - allow chat to continue even if save fails
    }
  };

  const handleFinalTranscript = useCallback(async (text) => {
    if (!text.trim()) return;

    setIsProcessing(true);
    setError(null);
    setInterimTranscript('');

    try {
      // Ensure we have a conversation ID
      let convId = currentConversationId;
      if (!convId) {
        convId = await createNewConversation();
        setCurrentConversationId(convId);
      }

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

      // Save user message to database
      if (convId) {
        await saveMessage(convId, 'user', text.trim(), emotionData.emotion);
      }

      // Generate assistant response
      const response = await generateResponse(text.trim(), emotionData.emotion);

      // Add assistant message
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: response.responseText
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Save assistant message to database
      if (convId) {
        await saveMessage(convId, 'assistant', response.responseText);
      }

      // Synthesize speech
      const ttsResult = await synthesizeSpeech(response.responseText);
      setAudioUrl(ttsResult.audioUrl);
    } catch (err) {
      console.error('Error processing transcript:', err);
      setError('Failed to generate response. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  }, [currentConversationId]);

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  // Focus text input when shown
  useEffect(() => {
    if (showTextInput && textInputRef.current) {
      textInputRef.current.focus();
    }
  }, [showTextInput]);

  // Handle text input submission
  const handleTextSubmit = async (e) => {
    e.preventDefault();
    const text = textInput.trim();
    if (!text) return;

    setIsProcessing(true);
    setError(null);
    setTextInput('');
    setShowTextInput(false);

    try {
      // Ensure we have a conversation ID
      let convId = currentConversationId;
      if (!convId) {
        convId = await createNewConversation();
        setCurrentConversationId(convId);
      }

      // Add user message immediately
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        text: text
      };

      setMessages(prev => [...prev, userMessage]);

      // Detect emotion
      const emotionData = await detectEmotion(text);
      // Format emotion name for display
      const emotionName = emotionData.emotion
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      setDetectedMood(emotionName);

      // Save user message to database
      if (convId) {
        await saveMessage(convId, 'user', text, emotionData.emotion);
      }

      // Generate assistant response
      const response = await generateResponse(text, emotionData.emotion);

      // Add assistant message
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: response.responseText
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Save assistant message to database
      if (convId) {
        await saveMessage(convId, 'assistant', response.responseText);
      }

      // Synthesize speech
      const ttsResult = await synthesizeSpeech(response.responseText);
      setAudioUrl(ttsResult.audioUrl);
    } catch (err) {
      console.error('Error processing text message:', err);
      setError('Failed to generate response. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle chat button click - show and focus text input
  const handleChatButtonClick = () => {
    setShowTextInput(true);
    // Focus will be handled by useEffect
  };

  // Fetch past conversations
  const fetchConversations = async () => {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    setLoadingConversations(true);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}/conversations?limit=50`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPastConversations(data);
      }
    } catch (err) {
      console.error('Error fetching conversations:', err);
    } finally {
      setLoadingConversations(false);
    }
  };

  // Load a conversation
  const loadConversation = async (conversationId) => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/messages`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Convert API messages to component message format
        const loadedMessages = data.messages.map(msg => ({
          id: msg.id,
          role: msg.role,
          text: msg.text
        }));
        setMessages(loadedMessages);
        setCurrentConversationId(conversationId);
        setSidebarOpen(false);
        // Refresh conversations list
        fetchConversations();
      }
    } catch (err) {
      console.error('Error loading conversation:', err);
      setError('Failed to load conversation');
    }
  };

  // Start new conversation
  const startNewConversation = async () => {
    setMessages([]);
    const newConvId = await createNewConversation();
    setCurrentConversationId(newConvId);
    setSidebarOpen(false);
    // Refresh conversations list to show the new one
    fetchConversations();
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
    if (!sidebarOpen) {
      fetchConversations();
    }
  };

  return (
    <div className="chat-page-new">
      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <div className="header-logo">
            <img src={elephantLogo} alt="Echocare Logo" className="logo-image" />
          </div>
          <div className="header-title">
            <h1 className="app-title">Echocare</h1>
            <p className="app-subtitle">Your personal therapy companion</p>
          </div>
        </div>
        <div className="header-icons">
          <button
            className="icon-button profile-button"
            onClick={() => navigate('/profile-setup')}
            title="Set up your profile"
          >
            👤
          </button>
          <button
            className="icon-button sidebar-toggle"
            onClick={toggleSidebar}
            title="Past conversations"
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
        </div>
      </header>

      {/* Sidebar Overlay */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={toggleSidebar}></div>
      )}

      {/* Past Conversations Sidebar */}
      <div className={`conversations-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-title">Past Conversations</h2>
          <div className="sidebar-header-actions">
            <button
              className="sidebar-refresh"
              onClick={fetchConversations}
              aria-label="Refresh conversations"
              title="Refresh"
            >
              ↻
            </button>
            <button
              className="sidebar-close"
              onClick={toggleSidebar}
              aria-label="Close sidebar"
            >
              ×
            </button>
          </div>
        </div>
        <button
          className="new-conversation-button"
          onClick={startNewConversation}
        >
          + New Conversation
        </button>
        <div className="sidebar-content">
          {loadingConversations ? (
            <div className="sidebar-loading">Loading conversations...</div>
          ) : pastConversations.length === 0 ? (
            <div className="sidebar-empty">No past conversations yet</div>
          ) : (
            <div className="conversations-list">
              {pastConversations.map((conv) => (
                <button
                  key={conv.id}
                  className={`conversation-item ${currentConversationId === conv.id ? 'active' : ''}`}
                  onClick={() => loadConversation(conv.id)}
                >
                  <div className="conversation-date">
                    {new Date(conv.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </div>
                  <div className="conversation-time">
                    {new Date(conv.created_at).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit'
                    })}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Content - Two Column Layout */}
      <main className="chat-main-layout">
        {/* Left Column - Conversation */}
        <div className="conversation-section-left">
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

          {/* Text Input Area */}
          <form className="text-input-container" onSubmit={handleTextSubmit}>
            <input
              ref={textInputRef}
              type="text"
              className="text-input"
              placeholder="Take your time, how are you feeling?"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  setShowTextInput(false);
                  setTextInput('');
                }
              }}
              style={{ display: showTextInput ? 'block' : 'none' }}
            />
            {showTextInput && (
              <div className="text-input-actions">
                <button
                  type="button"
                  className="text-input-cancel"
                  onClick={() => {
                    setShowTextInput(false);
                    setTextInput('');
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="text-input-submit"
                  disabled={!textInput.trim() || isProcessing}
                >
                  Send
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Right Column - Orb and Controls */}
        <div className="orb-controls-section">
          {/* Gentle Emotional Anchor */}
          <div className="emotional-anchor" role="status" aria-live="polite">
            <p className="anchor-message">I'm here with you.<br />How are you feeling right now?</p>
            <div className="anchor-mood">Mood insight: <span className="anchor-mood-value">{detectedMood} <span className="learning-tag">(learning)</span></span></div>
          </div>

          {/* Audio Visualization Circle */}
          <div className="visualization-container">
            <div
              ref={visualizationRef}
              className={`visualization-circle ${orbState}`}
            ></div>
          </div>

          {/* Instruction Text */}
          <p className="instruction-text">
            {isListening ? 'Listening...' : 'You can start whenever you feel ready.'}
          </p>

          {/* Control Buttons - Mute, Mic (larger), Chat */}
          <div className="control-buttons">
            <button
              className={`control-button speaker-button ${isMuted ? 'muted' : ''}`}
              onClick={toggleMute}
              aria-label={isMuted ? 'Unmute' : 'Mute'}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted ? '🔇' : '🔊'}
            </button>
            <div className="mic-button-wrapper">
              {/* Audio Bars - positioned around mic button */}
              {isListening && (
                <div className="audio-bars-container">
                  {Array.from({ length: 12 }).map((_, i) => (
                    <div key={i} className="chat-audio-bar"></div>
                  ))}
                </div>
              )}
              <button
                className={`control-button mic-button ${isListening ? 'active' : ''}`}
                onClick={isListening ? stopListening : startListening}
                aria-label={isListening ? 'Stop' : 'Start speaking'}
                title={isListening ? 'Stop' : 'Start speaking'}
              >
                🎙️
              </button>
            </div>
            <button
              className="control-button chat-button"
              onClick={handleChatButtonClick}
              aria-label="Type your message"
              title="Type your message"
            >
              💬
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
        </div>
      </main>

      {/* Audio Error Message */}
      {audioError && (
        <div className="audio-error-message" style={{
          background: '#fff5f5',
          border: '1px solid #ffcccc',
          borderRadius: '8px',
          padding: '0.75rem',
          marginTop: '1rem',
          textAlign: 'center',
          fontSize: '0.9rem',
          color: '#d32f2f'
        }}>
          {audioError}
          {audioUrl && (
            <button
              onClick={playAudioManually}
              style={{
                marginLeft: '0.5rem',
                padding: '0.25rem 0.75rem',
                background: '#20b2aa',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.85rem'
              }}
            >
              ▶️ Play
            </button>
          )}
        </div>
      )}

      {/* Hidden Audio Player */}
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          autoPlay
          muted={isMuted}
          preload="auto"
          onPlay={() => {
            console.log('Audio started playing');
            setIsAudioPlaying(true);
            setAudioError(null);
          }}
          onPause={() => {
            console.log('Audio paused');
            setIsAudioPlaying(false);
          }}
          onEnded={() => {
            console.log('Audio playback ended');
            setIsAudioPlaying(false);
            setAudioUrl(null);
            setAudioError(null);
          }}
          onError={(e) => {
            console.error('Audio playback error:', e);
            setIsAudioPlaying(false);
            const errorMsg = audioRef.current?.error 
              ? `Audio error: ${audioRef.current.error.message || 'Unknown error'}`
              : 'Failed to play audio. Please check the audio file.';
            setAudioError(errorMsg);
          }}
          onLoadedData={() => {
            console.log('Audio loaded successfully');
          }}
          onCanPlay={() => {
            console.log('Audio can play');
          }}
        />
      )}

      {/* Voice Profile Selection Modal */}
      {showVoiceProfileModal && (
        <VoiceProfileSelection
          onClose={() => {
            setShowVoiceProfileModal(false);
            // Refresh voice profile info
            const voiceId = localStorage.getItem('voice_id');
            const storedVoiceName = localStorage.getItem('voice_name');
            setHasVoiceCloned(!!voiceId);
            setVoiceName(storedVoiceName);
          }}
          onNavigateToSetup={() => {
            setShowVoiceProfileModal(false); // Close modal first
            navigate('/voice-profile', { state: { isNewProfile: true } });
          }}
        />
      )}
    </div>
  );
};

export default Chat;
