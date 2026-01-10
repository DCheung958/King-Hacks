import React, { useState, useEffect, useRef } from 'react';

const SpeechInput = ({ onFinalTranscript }) => {
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    // Check for browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      setIsSupported(true);
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
        
        if (finalText.trim() && onFinalTranscript) {
          onFinalTranscript(finalText.trim());
        }
      };
      
      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
    }
    
    // Cleanup
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [onFinalTranscript]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
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

  if (!isSupported) {
    return (
      <div className="speech-input unsupported">
        <p>Speech recognition is not supported in this browser.</p>
      </div>
    );
  }

  return (
    <div className="speech-input">
      <button 
        className={`speech-button ${isListening ? 'listening' : ''}`}
        onClick={isListening ? stopListening : startListening}
      >
        {isListening ? '🛑 Stop Listening' : '🎤 Start Listening'}
      </button>
      {interimTranscript && (
        <p className="interim-transcript">{interimTranscript}</p>
      )}
      {isListening && (
        <p className="listening-status">Listening...</p>
      )}
    </div>
  );
};

export default SpeechInput;