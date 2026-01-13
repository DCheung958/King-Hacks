import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadVoiceSample } from '../services/voiceService';
import './VoiceProfile.css';

const VOICE_SAMPLES = [
  "Hello, I'm creating my voice profile. This recording will help personalize my therapy experience.",
  "I believe in taking care of my mental health. Speaking about my feelings helps me grow and heal.",
  "Today is a new day, and I choose to approach it with kindness towards myself and others."
];

const VoiceProfile = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  const [recordings, setRecordings] = useState([]);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  const progress = ((currentStep + 1) / VOICE_SAMPLES.length) * 100;

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
        setRecordings(prev => [...prev, blob]);
        
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
    if (currentStep < VOICE_SAMPLES.length - 1) {
      setCurrentStep(prev => prev + 1);
      setError(null);
    } else {
      // All samples recorded, upload them
      try {
        setError(null);
        for (let i = 0; i < recordings.length; i++) {
          await uploadVoiceSample(recordings[i]);
        }
        // Navigate to chat after all samples are uploaded
        navigate('/chat');
      } catch (err) {
        console.error('Error uploading voice samples:', err);
        setError('Failed to upload voice samples. Please try again.');
      }
    }
  };

  // Can proceed if we have a recording for the current step and we're not currently recording
  const canProceed = recordings.length > currentStep && !isRecording;

  return (
    <div className="voice-profile-page">
      <div className="voice-profile-container">
        {/* Progress Header */}
        <div className="progress-header">
          <span className="progress-text">
            Voice Sample {currentStep + 1} of {VOICE_SAMPLES.length}
          </span>
          <div className="progress-info">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
            <span className="progress-percentage">{Math.round(progress)}% Complete</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="voice-profile-title">Create Your Voice Profile</h1>
        
        {/* Instructions */}
        <p className="voice-profile-instructions">
          Read the text below clearly. Your voice will be used to personalize your therapy experience.
        </p>

        {/* Text Sample Box */}
        <div className="text-sample-box">
          <p className="text-sample">{VOICE_SAMPLES[currentStep]}</p>
        </div>

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

        {/* Recording Button */}
        <div className="recording-controls">
          {isRecording ? (
            <button className="stop-button" onClick={stopRecording}>
              <span className="stop-icon">■</span>
            </button>
          ) : (
            <button className="mic-button" onClick={startRecording}>
              <span className="mic-icon">🎤</span>
            </button>
          )}
          <p className="recording-instruction">
            {isRecording ? 'Recording... Tap the square to stop' : 'Tap the microphone to start recording'}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">{error}</div>
        )}

        {/* Navigation Buttons */}
        <div className="navigation-buttons">
          {currentStep > 0 && (
            <button className="back-button" onClick={() => setCurrentStep(prev => prev - 1)}>
              Back
            </button>
          )}
          <button 
            className="next-button" 
            onClick={handleNext}
            disabled={!canProceed}
          >
            {currentStep < VOICE_SAMPLES.length - 1 ? 'Next' : 'Complete'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default VoiceProfile;

