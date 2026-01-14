import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { batchCloneVoice } from '../services/voiceService';
import './VoiceProfile.css';

const VOICE_SAMPLES = [
  "Hello, I'm creating my voice profile for Echocare. This detailed recording will help the AI understand my natural speaking patterns, including my tone, pace, and emotional expression. I believe that having a personalized therapeutic experience means the AI can communicate with me in a way that feels authentic and familiar, making our conversations more meaningful and supportive.",
  "Mental health is incredibly important to me, and I take it seriously. When I speak about my feelings, I try to be honest and open. I find that expressing my thoughts out loud helps me process them better. Sometimes I speak quickly when I'm excited or anxious, and other times I take my time to choose my words carefully. I hope this recording captures the natural rhythm of how I communicate.",
  "Today represents a new beginning for me. I'm choosing to approach this day with kindness, both towards myself and towards others. I believe that self-compassion is essential for growth and healing. When I'm feeling down, I try to remind myself that it's okay to have difficult days, and that healing is not a linear process. This voice profile will help create a therapeutic space that truly understands me.",
  "I've learned that communication is a two-way street. When I'm having a conversation, I listen carefully and respond thoughtfully. I value authenticity in my interactions, and I appreciate when others speak to me in a genuine way. I hope that by sharing my voice in this way, the AI companion can learn to communicate with me in a manner that feels natural and supportive, reflecting my own communication style.",
  "Building trust takes time, and I understand that developing a therapeutic relationship requires patience and consistency. I'm committed to this process of self-discovery and healing. Through these voice samples, I'm providing the foundation for an AI companion that can understand not just what I say, but how I say it—the subtle nuances of my speech that make my communication style uniquely mine."
];

const OPTIONAL_FREE_SPEECH = true; // Enable optional free speech page

const VoiceProfile = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const userName = location.state?.userName || localStorage.getItem('user_name') || '';
  
  const [currentStep, setCurrentStep] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  const [recordings, setRecordings] = useState([]);
  const [freeSpeechRecording, setFreeSpeechRecording] = useState(null);
  const [showFreeSpeech, setShowFreeSpeech] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recordingConfirmed, setRecordingConfirmed] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioPlayerRef = useRef(null);

  const totalSteps = OPTIONAL_FREE_SPEECH ? VOICE_SAMPLES.length + 1 : VOICE_SAMPLES.length;
  const isFreeSpeechStep = currentStep === VOICE_SAMPLES.length;
  const progress = ((currentStep + 1) / totalSteps) * 100;

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      // Set up audio visualization
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      analyserRef.current.fftSize = 256;
      
      // Start visualization
      visualizeAudio();
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      const chunks = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        if (isFreeSpeechStep) {
          setFreeSpeechRecording(blob);
        } else {
          const newRecordings = [...recordings];
          newRecordings[currentStep] = blob;
          setRecordings(newRecordings);
        }
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
          audioContextRef.current = null;
        }
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
      };
      
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      setError('Could not access microphone. Please check permissions.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const replayRecording = () => {
    const currentRecording = isFreeSpeechStep ? freeSpeechRecording : recordings[currentStep];
    if (!currentRecording) return;

    // Create audio URL from blob
    const audioUrl = URL.createObjectURL(currentRecording);
    const audio = new Audio(audioUrl);
    audioPlayerRef.current = audio;

    audio.onended = () => {
      setIsPlaying(false);
      URL.revokeObjectURL(audioUrl);
    };

    audio.onerror = () => {
      setIsPlaying(false);
      setError('Failed to play recording');
      URL.revokeObjectURL(audioUrl);
    };

    setIsPlaying(true);
    audio.play();
  };

  const tryAgain = () => {
    // Stop audio if playing
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
    }
    setIsPlaying(false);
    setRecordingConfirmed(false);
    // Clear current recording
    if (isFreeSpeechStep) {
      setFreeSpeechRecording(null);
    } else {
      const newRecordings = [...recordings];
      newRecordings[currentStep] = undefined;
      setRecordings(newRecordings);
    }
  };

  const confirmRecording = () => {
    setRecordingConfirmed(true);
    // Stop audio if playing
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
    }
    setIsPlaying(false);
  };

  const visualizeAudio = () => {
    if (!analyserRef.current) return;
    
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      if (!analyserRef.current) {
        // Reset bars when stopped
        const bars = document.querySelectorAll('.audio-bar');
        bars.forEach(bar => {
          bar.style.height = '10%';
        });
        return;
      }
      
      animationFrameRef.current = requestAnimationFrame(draw);
      analyserRef.current.getByteFrequencyData(dataArray);
      
      // Update visualization bars
      const bars = document.querySelectorAll('.audio-bar');
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

  const handleNext = async () => {
    if (isFreeSpeechStep) {
      // On free speech step, proceed to batch upload and clone
      try {
        setError(null);
        setLoading(true);
        
        // Collect all recordings (required + optional free speech)
        const allRecordings = [...recordings];
        if (freeSpeechRecording) {
          allRecordings.push(freeSpeechRecording);
        }
        
        // Get user ID from localStorage
        const userId = localStorage.getItem('user_id');
        const userName = localStorage.getItem('user_name') || userName || 'User';
        
        // Batch upload and clone all samples at once (saves ElevenLabs credits)
        const result = await batchCloneVoice(
          allRecordings,
          userId,
          `${userName}'s Voice`
        );
        
        // Store voice_id if cloning was successful
        if (result.voiceId) {
          localStorage.setItem('voice_id', result.voiceId);
        }
        
        // Navigate to chat after batch upload/clone
        navigate('/chat');
      } catch (err) {
        console.error('Error batch cloning voice:', err);
        setError(err.message || 'Failed to upload and clone voice samples. Please try again.');
        setLoading(false);
      }
    } else if (currentStep < VOICE_SAMPLES.length - 1) {
      // Move to next test page
      setCurrentStep(prev => prev + 1);
      setError(null);
    } else {
      // Finished test pages, show free speech if enabled
      if (OPTIONAL_FREE_SPEECH) {
        setShowFreeSpeech(true);
        setCurrentStep(prev => prev + 1);
        setError(null);
      } else {
        // Upload and clone all samples
        try {
          setError(null);
          setLoading(true);
          
          // Get user ID from localStorage
          const userId = localStorage.getItem('user_id');
          const userName = localStorage.getItem('user_name') || userName || 'User';
          
          // Batch upload and clone all samples at once
          const result = await batchCloneVoice(
            recordings,
            userId,
            `${userName}'s Voice`
          );
          
          // Store voice_id if cloning was successful
          if (result.voiceId) {
            localStorage.setItem('voice_id', result.voiceId);
          }
          
          navigate('/chat');
        } catch (err) {
          console.error('Error batch cloning voice:', err);
          setError(err.message || 'Failed to upload and clone voice samples. Please try again.');
          setLoading(false);
        }
      }
    }
  };

  const handleSkipFreeSpeech = async () => {
    // Skip free speech and batch upload/clone required samples
    try {
      setError(null);
      setLoading(true);
      
      // Get user ID from localStorage
      const userId = localStorage.getItem('user_id');
      const userName = localStorage.getItem('user_name') || userName || 'User';
      
      // Batch upload and clone all required samples at once
      const result = await batchCloneVoice(
        recordings,
        userId,
        `${userName}'s Voice`
      );
      
      // Store voice_id if cloning was successful
      if (result.voiceId) {
        localStorage.setItem('voice_id', result.voiceId);
      }
      
      navigate('/chat');
    } catch (err) {
      console.error('Error batch cloning voice:', err);
      setError(err.message || 'Failed to upload and clone voice samples. Please try again.');
      setLoading(false);
    }
  };

  // Can proceed if we have a recording for the current step, it's confirmed, and we're not currently recording
  const hasRecording = isFreeSpeechStep ? freeSpeechRecording !== null : recordings[currentStep] !== undefined;
  const canProceed = hasRecording && recordingConfirmed && !isRecording && !isPlaying;

  return (
    <div className="voice-profile-page">
      <div className="voice-profile-container">
        {/* Progress Header */}
        <div className="progress-header">
          <span className="progress-text">
            {isFreeSpeechStep ? 'Optional Recording' : `Voice Sample ${currentStep + 1} of ${VOICE_SAMPLES.length}`}
          </span>
          <div className="progress-info">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <span className="progress-percentage">{Math.round(progress)}% Complete</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="voice-profile-title">
          {isFreeSpeechStep ? 'Optional: Free Speech Recording' : 'Create Your Voice Profile'}
        </h1>
        
        {/* Instructions */}
        <p className="voice-profile-instructions">
          {isFreeSpeechStep 
            ? "Speak freely about anything you'd like. This helps us better understand your natural speaking style, tone, and emotional expression. You can talk for as long as you feel comfortable."
            : "Read the text below clearly and naturally. Your voice will be used to personalize your therapy experience and help the AI understand your communication style."
          }
        </p>

        {/* Text Sample Box - only show for test pages */}
        {!isFreeSpeechStep && (
          <div className="text-sample-box">
            <p className="text-sample">{VOICE_SAMPLES[currentStep]}</p>
          </div>
        )}

        {/* Free Speech Instructions */}
        {isFreeSpeechStep && (
          <div className="text-sample-box free-speech-box">
            <p className="free-speech-instruction">
              🎤 Speak naturally about anything that comes to mind—your day, your thoughts, your feelings, or whatever feels comfortable. There's no script to follow, just be yourself.
            </p>
          </div>
        )}

        {/* Audio Visualization */}
        <div className="audio-visualization">
          {isRecording ? (
            <>
              <div className="audio-visualizer-circle"></div>
              <div className="audio-bars">
                {Array.from({ length: 20 }).map((_, i) => (
                  <div key={i} className="audio-bar"></div>
                ))}
              </div>
            </>
          ) : (
            <div className="audio-visualizer-circle idle"></div>
          )}
        </div>

        {/* Recording Controls */}
        <div className="recording-controls">
          {isRecording ? (
            <>
              <button className="stop-button" onClick={stopRecording}>
                <span className="stop-icon">■</span>
              </button>
              <p className="recording-instruction">
                Recording... Tap the square to stop
              </p>
            </>
          ) : hasRecording ? (
            <>
              <div className="playback-controls">
                <button 
                  className="replay-button" 
                  onClick={replayRecording}
                  disabled={isPlaying}
                >
                  <span className="replay-icon">▶️</span>
                  {isPlaying ? 'Playing...' : 'Replay'}
                </button>
                <button 
                  className="try-again-button" 
                  onClick={tryAgain}
                  disabled={isPlaying}
                >
                  <span className="try-again-icon">🔄</span>
                  Try Again
                </button>
              </div>
              <p className="recording-instruction">
                {isPlaying 
                  ? 'Playing your recording...' 
                  : 'Listen to your recording. If you\'re happy with it, press Next to continue.'}
              </p>
            </>
          ) : (
            <>
              <button className="mic-button" onClick={startRecording}>
                <span className="mic-icon">🎤</span>
              </button>
              <p className="recording-instruction">
                {isFreeSpeechStep
                  ? 'Tap the microphone to start your free speech recording'
                  : 'Tap the microphone to start recording'}
              </p>
            </>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">{error}</div>
        )}

        {/* Navigation Buttons */}
        <div className="navigation-buttons">
          {currentStep > 0 && !isFreeSpeechStep && (
            <button className="back-button" onClick={() => setCurrentStep(prev => prev - 1)}>
              Back
            </button>
          )}
          {isFreeSpeechStep && (
            <button className="skip-button" onClick={handleSkipFreeSpeech}>
              Skip
            </button>
          )}
          <button 
            className="next-button" 
            onClick={handleNext}
            disabled={!hasRecording || isRecording || isPlaying}
          >
            {isFreeSpeechStep 
              ? 'Complete Setup' 
              : currentStep < VOICE_SAMPLES.length - 1 
                ? 'Next' 
                : OPTIONAL_FREE_SPEECH 
                  ? 'Continue' 
                  : 'Complete'
            }
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceProfile;
