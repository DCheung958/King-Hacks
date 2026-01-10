import React, { useEffect, useRef, useState } from 'react';

const AudioPlayer = ({ audioUrl }) => {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (audioUrl && audioRef.current) {
      audioRef.current.src = audioUrl;
      
      // Handle audio loading errors gracefully
      audioRef.current.onerror = () => {
        console.warn('Audio file could not be loaded. Using fallback silent audio.');
        // Use a minimal silent WAV data URI as fallback
        audioRef.current.src = "data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";
      };
      
      // Attempt autoplay
      const playPromise = audioRef.current.play();
      
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            setIsPlaying(true);
          })
          .catch(error => {
            // Autoplay was prevented - user will need to interact first
            console.log('Autoplay prevented:', error);
          });
      }
    }
  }, [audioUrl]);

  const handlePlay = () => {
    if (audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleEnded = () => {
    setIsPlaying(false);
  };

  if (!audioUrl) {
    return null;
  }

  return (
    <div className="audio-player">
      <audio 
        ref={audioRef} 
        onEnded={handleEnded}
        onPlay={handlePlay}
        onPause={handlePause}
        controls
      />
      {isPlaying && <p className="audio-status">Playing audio response...</p>}
    </div>
  );
};

export default AudioPlayer;