import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { detectEmotion, generateResponse } from '../services/chatService';
import { synthesizeSpeech } from '../services/ttsService';
import VoiceProfileSelection from './VoiceProfileSelection';
import microphoneIcon from '../assets/microphone.svg';
import './Chat.css';

const Chat = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [conversations, setConversations] = useState([
    {
      id: 1,
      name: 'Chat 1',
      messages: []
    }
  ]);
  const [activeConversationId, setActiveConversationId] = useState(1);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [detectedMood, setDetectedMood] = useState('Neutral');
  const [isMuted, setIsMuted] = useState(false);
  const [hasVoiceCloned, setHasVoiceCloned] = useState(false);
  const [voiceName, setVoiceName] = useState(null);
  const [audioError, setAudioError] = useState(null);
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [showVoiceProfileModal, setShowVoiceProfileModal] = useState(false);
  const [inputMode, setInputMode] = useState('voice'); // 'voice' or 'text'
  const [textInput, setTextInput] = useState('');
  const [showPastConversations, setShowPastConversations] = useState(false);
  const [renameModalOpen, setRenameModalOpen] = useState(false);
  const [renameConversationId, setRenameConversationId] = useState(null);
  const [renameValue, setRenameValue] = useState('');
  const [userId, setUserId] = useState(() => localStorage.getItem('user_id')); // Track user_id in state
  
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioRef = useRef(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);

  // Monitor user_id changes and reload conversations when user signs in
  useEffect(() => {
    const checkUserId = () => {
      const currentUserId = localStorage.getItem('user_id');
      if (currentUserId !== userId) {
        setUserId(currentUserId);
      }
    };
    
    // Check immediately
    checkUserId();
    
    // Check periodically (for same-tab login)
    const interval = setInterval(checkUserId, 500);
    
    // Listen for storage events (for cross-tab login)
    const handleStorageChange = (e) => {
      if (e.key === 'user_id') {
        setUserId(e.newValue);
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [userId]);

  // Load conversations from database (when user is logged in or when user_id changes)
  useEffect(() => {
    const loadConversations = async () => {
      if (!userId) {
        // No user logged in - load from localStorage only
        try {
          const stored = localStorage.getItem('echocare_conversations');
          if (stored) {
            const parsed = JSON.parse(stored);
            if (parsed.conversations && Array.isArray(parsed.conversations) && parsed.conversations.length > 0) {
              setConversations(parsed.conversations);
              setActiveConversationId(
                parsed.activeConversationId ||
                parsed.conversations[0]?.id ||
                1
              );
            }
          }
        } catch (e) {
          console.error('Failed to load conversations from localStorage', e);
        }
        return;
      }

      // User is logged in - load from database
      try {
        // Fetch conversations from database
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}/conversations`);
        
        if (response.ok) {
          const dbConversations = await response.json();
          
          // Load messages for each conversation
          const conversationsWithMessages = await Promise.all(
            dbConversations.map(async (conv, index) => {
              try {
                const messagesResponse = await fetch(
                  `${API_BASE_URL}/api/conversations/${conv.id}/messages?limit=100`
                );
                
                if (messagesResponse.ok) {
                  const messagesData = await messagesResponse.json();
                  const messages = messagesData.messages.map(msg => ({
                    id: msg.id,
                    role: msg.role,
                    text: msg.text,
                    emotion: msg.emotion
                  }));
                  
                  return {
                    id: Date.now() + Math.random(), // Local ID for UI
                    dbId: conv.id, // Database conversation ID
                    name: `Chat ${index + 1}`, // Use sequential numbering
                    messages: messages || []
                  };
                }
                
                return {
                  id: Date.now() + Math.random(),
                  dbId: conv.id,
                  name: `Chat ${index + 1}`, // Use sequential numbering
                  messages: []
                };
              } catch (err) {
                console.error(`Failed to load messages for conversation ${conv.id}:`, err);
                return {
                  id: Date.now() + Math.random(),
                  dbId: conv.id,
                  name: `Chat ${index + 1}`, // Use sequential numbering
                  messages: []
                };
              }
            })
          );

          if (conversationsWithMessages.length > 0) {
            setConversations(conversationsWithMessages);
            setActiveConversationId(conversationsWithMessages[0].id);
          } else {
            // No conversations in database - create a new one
            await handleNewConversation();
          }
        } else {
          console.warn('Failed to load conversations from database, falling back to localStorage');
          // Fallback to localStorage
          const stored = localStorage.getItem('echocare_conversations');
          if (stored) {
            const parsed = JSON.parse(stored);
            if (parsed.conversations && Array.isArray(parsed.conversations) && parsed.conversations.length > 0) {
              setConversations(parsed.conversations);
              setActiveConversationId(
                parsed.activeConversationId ||
                parsed.conversations[0]?.id ||
                1
              );
            }
          }
        }
      } catch (error) {
        console.error('Error loading conversations from database:', error);
        // Fallback to localStorage
        try {
          const stored = localStorage.getItem('echocare_conversations');
          if (stored) {
            const parsed = JSON.parse(stored);
            if (parsed.conversations && Array.isArray(parsed.conversations) && parsed.conversations.length > 0) {
              setConversations(parsed.conversations);
              setActiveConversationId(
                parsed.activeConversationId ||
                parsed.conversations[0]?.id ||
                1
              );
            }
          }
        } catch (e) {
          console.error('Failed to load conversations from localStorage', e);
        }
      }
    };

    loadConversations();
  }, [userId]); // Reload when user_id changes

  // Persist conversations to localStorage
  useEffect(() => {
    try {
      const payload = {
        conversations,
        activeConversationId
      };
      localStorage.setItem('echocare_conversations', JSON.stringify(payload));
    } catch (e) {
      console.error('Failed to save conversations to localStorage', e);
    }
  }, [conversations, activeConversationId]);

  // Load messages when switching to a conversation (if not already loaded)
  useEffect(() => {
    const loadMessagesForActiveConversation = async () => {
      const userId = localStorage.getItem('user_id');
      if (!userId) return; // Only load from database if user is logged in

      const currentConv = conversations.find(conv => conv.id === activeConversationId);
      
      // If conversation has dbId but no messages (or empty messages), load from database
      if (currentConv && currentConv.dbId && (!currentConv.messages || currentConv.messages.length === 0)) {
        try {
          const messagesResponse = await fetch(
            `${API_BASE_URL}/api/conversations/${currentConv.dbId}/messages?limit=100`
          );
          
          if (messagesResponse.ok) {
            const messagesData = await messagesResponse.json();
            const messages = messagesData.messages.map(msg => ({
              id: msg.id,
              role: msg.role,
              text: msg.text,
              emotion: msg.emotion
            }));
            
            // Update conversation with messages (only if still on the same conversation)
            setConversations(prev => {
              const currentConvAfterUpdate = prev.find(conv => conv.id === activeConversationId);
              // Only update if messages still missing (prevent race conditions)
              if (currentConvAfterUpdate && (!currentConvAfterUpdate.messages || currentConvAfterUpdate.messages.length === 0)) {
                return prev.map(conv =>
                  conv.id === activeConversationId
                    ? { ...conv, messages: messages }
                    : conv
                );
              }
              return prev;
            });
          }
        } catch (error) {
          console.error(`Failed to load messages for conversation ${currentConv.dbId}:`, error);
        }
      }
    };

    loadMessagesForActiveConversation();
  }, [activeConversationId]); // Only depend on activeConversationId to avoid loops

  // Check if user has cloned their voice and get voice name
  useEffect(() => {
    const voiceId = localStorage.getItem('voice_id');
    const storedVoiceName = localStorage.getItem('voice_name');
    setHasVoiceCloned(!!voiceId && !!storedVoiceName);
    // Only set voiceName if it's not empty/null
    setVoiceName(storedVoiceName && storedVoiceName.trim() ? storedVoiceName : null);
  }, [showVoiceProfileModal]); // Refresh when modal closes

  // Also check on mount
  useEffect(() => {
    const voiceId = localStorage.getItem('voice_id');
    const storedVoiceName = localStorage.getItem('voice_name');
    setHasVoiceCloned(!!voiceId && !!storedVoiceName);
    setVoiceName(storedVoiceName && storedVoiceName.trim() ? storedVoiceName : null);
  }, []); // Run on mount

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


  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    
    const text = textInput.trim();
    setTextInput('');
    await handleFinalTranscript(text);
  };

  const handleFinalTranscript = useCallback(async (text) => {
    if (!text.trim()) return;

    setIsProcessing(true);
    setError(null);
    setInterimTranscript('');

    try {
      // Add user message immediately to the active conversation
      const userMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        text: text.trim()
      };

      setConversations(prev =>
        prev.map(conversation =>
          conversation.id === activeConversationId
            ? {
                ...conversation,
                messages: [...conversation.messages, userMessage]
              }
            : conversation
        )
      );

      // Detect emotion
      const emotionData = await detectEmotion(text.trim());
      // Format emotion name for display
      const emotionName = emotionData.emotion
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      setDetectedMood(emotionName);

      // Get user_id and conversation_id for saving to database
      const userId = localStorage.getItem('user_id');
      let conversationId = null;
      
      // Get the current conversation using functional update to ensure we have the latest state
      let currentConversation = null;
      setConversations(prevConvs => {
        currentConversation = prevConvs.find(conv => conv.id === activeConversationId);
        return prevConvs; // Don't modify, just read the latest state
      });
      
      // If conversation doesn't have a dbId and user is logged in, create it in database
      if (currentConversation && !currentConversation.dbId && userId) {
        try {
          const createResponse = await fetch(`${API_BASE_URL}/api/users/${userId}/conversations`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
          });
          
          if (createResponse.ok) {
            const dbConversation = await createResponse.json();
            conversationId = dbConversation.id;
            
            // Update conversation with dbId
            setConversations(prevConvs =>
              prevConvs.map(conv =>
                conv.id === activeConversationId
                  ? { ...conv, dbId: dbConversation.id }
                  : conv
              )
            );
          } else {
            console.warn('Failed to create conversation in database, continuing without dbId');
          }
        } catch (err) {
          console.error('Failed to create conversation in database:', err);
          // Continue without dbId - conversation will still work locally
        }
      } else {
        conversationId = currentConversation?.dbId || null;
      }

      // Generate assistant response (with user_id and conversation_id for saving)
      const response = await generateResponse(text.trim(), emotionData.emotion, userId, conversationId);
      
      // Add assistant message
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        text: response.responseText
      };

      setConversations(prev =>
        prev.map(conversation =>
          conversation.id === activeConversationId
            ? {
                ...conversation,
                messages: [...conversation.messages, assistantMessage]
              }
            : conversation
        )
      );

      // Get user's voice ID from localStorage (if they've cloned their voice)
      const userVoiceId = localStorage.getItem('voice_id');
      
      // Synthesize speech with user's voice and emotion for prosody-aware synthesis
      // Only synthesize if voice_id is available (user has cloned their voice)
      if (userVoiceId) {
        try {
          console.log('Synthesizing speech with voice_id:', userVoiceId);
          const ttsResult = await synthesizeSpeech(
            response.responseText, 
            userVoiceId,  // Use user's cloned voice
            emotionData.emotion
          );
          console.log('TTS result:', ttsResult);
          
          if (ttsResult && ttsResult.audioUrl) {
            console.log('Setting audio URL:', ttsResult.audioUrl);
            setAudioUrl(ttsResult.audioUrl);
          } else {
            console.warn('TTS returned no audio URL');
            setError('Voice synthesis completed but no audio URL returned.');
            setAudioError('No audio URL received from server.');
          }
        } catch (ttsError) {
          console.error('Voice synthesis failed:', ttsError);
          const errorMessage = ttsError.message || 'Failed to generate voice';
          setError(`Voice synthesis failed: ${errorMessage}. Please check if your voice is cloned and ElevenLabs API is configured.`);
          setAudioError('Voice synthesis failed. Please check console for details.');
          // Continue without audio - conversation text is still displayed
        }
      } else {
        console.log('No voice_id found - skipping voice synthesis. User can clone their voice in Voice Profile.');
        setHasVoiceCloned(false);
        // Conversation text is still displayed even without audio
      }
    } catch (err) {
      console.error('Error processing transcript:', err);
      setError('Failed to generate response. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  }, [activeConversationId]); // Remove conversations from deps - we use functional updates to get latest state

  const toggleMute = () => {
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  const formatConversationName = (dateString) => {
    const convDate = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    if (convDate.toDateString() === today.toDateString()) {
      return `Today ${convDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else if (convDate.toDateString() === yesterday.toDateString()) {
      return `Yesterday ${convDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    } else {
      return convDate.toLocaleDateString([], { 
        month: 'short', 
        day: 'numeric', 
        year: convDate.getFullYear() !== today.getFullYear() ? 'numeric' : undefined 
      }) + ` ${convDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    }
  };

  const handleNewConversation = async () => {
    const userId = localStorage.getItem('user_id');
    
    // Create conversation in database if user is logged in
    let dbConversationId = null;
    // Use simple "Chat X" naming for new conversations
    const chatNumber = conversations.length + 1;
    let conversationName = `Chat ${chatNumber}`;
    
    if (userId) {
      try {
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}/conversations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const dbConversation = await response.json();
          dbConversationId = dbConversation.id;
          // Keep simple "Chat X" name for new conversations
          conversationName = `Chat ${chatNumber}`;
        } else {
          console.warn('Failed to create conversation in database, will create locally only');
          // Keep simple "Chat X" name
          conversationName = `Chat ${chatNumber}`;
        }
      } catch (error) {
        console.error('Error creating conversation in database:', error);
        // Keep simple "Chat X" name
        conversationName = `Chat ${chatNumber}`;
      }
    } else {
      // No user logged in - use simple "Chat X" name
      conversationName = `Chat ${chatNumber}`;
    }

    const newConversation = {
      id: Date.now() + Math.random(),
      dbId: dbConversationId, // Database conversation ID (if created)
      name: conversationName,
      messages: []
    };

    setConversations(prev => [...prev, newConversation]);
    setActiveConversationId(newConversation.id);
    setError(null);
    setAudioUrl(null);
  };

  const openRenameModal = (conversationId, e) => {
    e.stopPropagation();
    const current = conversations.find(conv => conv.id === conversationId);
    setRenameConversationId(conversationId);
    setRenameValue(current?.name || '');
    setRenameModalOpen(true);
  };

  const closeRenameModal = () => {
    setRenameModalOpen(false);
    setRenameConversationId(null);
    setRenameValue('');
  };

  const handleRenameSubmit = (e) => {
    e.preventDefault();
    const trimmed = renameValue.trim();
    if (!trimmed || !renameConversationId) {
      closeRenameModal();
      return;
    }

    setConversations(prev =>
      prev.map(conv =>
        conv.id === renameConversationId ? { ...conv, name: trimmed } : conv
      )
    );
    closeRenameModal();
  };

  const handleDeleteConversation = (conversationId, e) => {
    e.stopPropagation(); // Prevent triggering the conversation selection
    
    setConversations(prev => {
      const filtered = prev.filter(conv => conv.id !== conversationId);
      
      // If we deleted the active conversation, switch to another one
      if (conversationId === activeConversationId) {
        if (filtered.length > 0) {
          setActiveConversationId(filtered[0].id);
        } else {
          // If no conversations left, create a new one
          const newConversation = {
            id: Date.now(),
            name: 'Chat 1',
            messages: []
          };
          setActiveConversationId(newConversation.id);
          return [newConversation];
        }
      }
      
      return filtered;
    });
  };

  const currentConversation =
    conversations.find(conv => conv.id === activeConversationId) ||
    conversations[0] ||
    { id: 1, name: 'Chat 1', messages: [] };

  const messages = currentConversation.messages || [];

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesContainerRef.current && messages.length > 0) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages.length, activeConversationId]);

  return (
    <div className="chat-page-new">
      {/* Header */}
      <header className="chat-header">
        <div className="header-left">
          <div className="header-logo"></div>
          <div className="header-title-wrapper">
            <div className="header-title">
              <h1 className="app-title">Echocare</h1>
              <p className="app-subtitle">Your personal therapy companion</p>
            </div>
            <div className="voice-profile-button-wrapper">
              <button 
                className="voice-profile-button"
                onClick={() => setShowVoiceProfileModal(!showVoiceProfileModal)}
                title={voiceName ? "Manage your voice profile" : "Set up your voice profile"}
              >
                {voiceName && voiceName.trim() ? voiceName : "Set up voice profile"}
              </button>
              {showVoiceProfileModal && (
                <VoiceProfileSelection
                  onClose={() => {
                    setShowVoiceProfileModal(false);
                    // Refresh voice profile info
                    const voiceId = localStorage.getItem('voice_id');
                    const storedVoiceName = localStorage.getItem('voice_name');
                    setHasVoiceCloned(!!voiceId && !!storedVoiceName);
                    setVoiceName(storedVoiceName && storedVoiceName.trim() ? storedVoiceName : null);
                  }}
                  onNavigateToSetup={() => {
                    setShowVoiceProfileModal(false);
                    navigate('/voice-profile', { state: { isNewProfile: true } });
                  }}
                />
              )}
            </div>
          </div>
        </div>
        <div className="header-icons">
          <button
            className="icon-button menu-icon"
            onClick={() => setShowPastConversations(true)}
            aria-label="Open past conversations"
          >
            ☰
          </button>
        </div>
      </header>

      {/* Main Layout */}
      <div className="chat-layout">
        {/* Left: Conversation Messages */}
        <section className="conversation-section">
          <div className="conversation-header">
            <h2 className="conversation-title">
              {currentConversation.name || 'Conversation'}
            </h2>
            {!hasVoiceCloned && messages.length > 0 && (
              <button
                onClick={() => setShowVoiceProfileModal(true)}
                className="clone-voice-button"
                title="Clone your voice to hear responses in your own voice"
              >
                <img src={microphoneIcon} alt="Microphone" className="clone-voice-icon" /> Clone Voice
              </button>
            )}
          </div>
          <div className="conversation-messages" ref={messagesContainerRef}>
            {messages.length === 0 ? (
              <div className="empty-conversation">
                <p>Your conversation will appear here</p>
              </div>
            ) : (
              <>
                {messages.map(message => (
                  <div 
                    key={message.id} 
                    className={`conversation-message ${message.role}`}
                  >
                    <div className="message-content">
                      {message.text}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </section>

        {/* Middle: Mood card + mic controls */}
        <main className="chat-main">
          {/* Mood Card */}
          <div className="mood-card">
            <p className="mood-card-main-text">I'm here with you.</p>
            <p className="mood-card-secondary-text">How are you feeling right now?</p>
            <div className="mood-card-insight-row">
              <span className="mood-insight-label">Mood insight:</span>
              <span className="mood-insight-value">{detectedMood}</span>
              <span className="mood-insight-status">(learning)</span>
            </div>
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
            {inputMode === 'text' 
              ? 'You can start whenever you feel ready.' 
              : isListening 
                ? 'Listening...' 
                : 'You can start whenever you feel ready.'}
          </p>

          {/* Text Input (when in text mode) */}
          {inputMode === 'text' && (
            <form onSubmit={handleTextSubmit} className="text-input-form">
              <textarea
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type your message here..."
                className="text-input-field"
                rows="3"
                disabled={isProcessing}
              />
              <button 
                type="submit" 
                className="text-submit-button"
                disabled={isProcessing || !textInput.trim()}
              >
                Send
              </button>
            </form>
          )}

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
              disabled={inputMode === 'text'}
            >
              <img src={microphoneIcon} alt="Microphone" className="chat-mic-icon" />
            </button>
            <button
              className={`control-button text-button ${inputMode === 'text' ? 'active' : ''}`}
              onClick={() => setInputMode(inputMode === 'text' ? 'voice' : 'text')}
              aria-label={inputMode === 'text' ? 'Switch to voice' : 'Switch to text'}
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

          {/* Audio Playing Indicator */}
          {isAudioPlaying && !isMuted && (
            <div className="audio-playing-indicator" style={{
              color: '#20b2aa',
              fontSize: '0.9rem',
              textAlign: 'center',
              marginTop: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem'
            }}>
              🔊 Playing response...
            </div>
          )}
        </main>

      </div>

      {/* Right-side Past Conversations Overlay */}
      {showPastConversations && (
        <div className="past-conversations-overlay">
          <div className="past-conversations-panel gradient">
            <div className="past-conversations-topbar">
              <span className="past-conversations-title">Past Conversations</span>
              <div className="past-conversations-topbar-icons">
                <button
                  className="topbar-exit-button"
                  type="button"
                  onClick={() => setShowPastConversations(false)}
                  title="Exit"
                >
                  Exit
                </button>
              </div>
            </div>

            <button
              className="new-conversation-button"
              onClick={handleNewConversation}
              type="button"
            >
              + New Conversation
            </button>

            <div className="past-conversations-list">
              {conversations.length === 0 ? (
                <div className="no-conversations">No past conversations yet</div>
              ) : (
                conversations.map((conversation, index) => (
                  <div
                    key={conversation.id}
                    className={`conversation-list-item ${
                      conversation.id === activeConversationId ? 'active' : ''
                    }`}
                  >
                    <div
                      className="conversation-item-main"
                      onClick={() => {
                        setActiveConversationId(conversation.id);
                        setShowPastConversations(false);
                      }}
                    >
                      <div className="conversation-list-number">
                        {conversation.name || `Chat ${index + 1}`}
                      </div>
                      <div className="conversation-list-preview">
                        {conversation.messages[conversation.messages.length - 1]?.text ||
                          'Start talking to begin this chat'}
                      </div>
                    </div>
                    <button
                      className="conversation-rename-button"
                      onClick={(e) => openRenameModal(conversation.id, e)}
                      type="button"
                      title="Rename conversation"
                    >
                      ✎
                    </button>
                    <button
                      className="conversation-delete-button"
                      onClick={(e) => handleDeleteConversation(conversation.id, e)}
                      type="button"
                      title="Delete conversation"
                    >
                      ✕
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Rename Conversation Modal */}
      {renameModalOpen && (
        <div className="rename-modal-backdrop" onClick={closeRenameModal}>
          <div
            className="rename-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="rename-modal-title">Rename conversation</h3>
            <form onSubmit={handleRenameSubmit} className="rename-modal-form">
              <input
                type="text"
                className="rename-modal-input"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                placeholder="Enter a name for this chat"
                autoFocus
              />
              <div className="rename-modal-actions">
                <button
                  type="button"
                  className="rename-modal-button secondary"
                  onClick={closeRenameModal}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rename-modal-button primary"
                  disabled={!renameValue.trim()}
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

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

    </div>
  );
};

export default Chat;
