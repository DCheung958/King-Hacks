import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Welcome.css';

const Welcome = () => {
  const navigate = useNavigate();

  const handleBeginJourney = () => {
    navigate('/voice-profile');
  };

  return (
    <div className="welcome-page">
      <div className="welcome-container">
        {/* Logo Circle */}
        <div className="logo-circle"></div>
        
        {/* Title */}
        <h1 className="welcome-title">
          Welcome to <span className="title-echocare">Echocare</span>
        </h1>
        
        {/* Description */}
        <p className="welcome-description">
          Experience personalized emotional therapy with AI that speaks in your own voice, creating a deeply personal healing journey.
        </p>
        
        {/* Feature Cards */}
        <div className="feature-cards">
          <div className="feature-card">
            <div className="feature-icon">🎤</div>
            <h3 className="feature-title">Your Voice, Your Therapy</h3>
            <p className="feature-description">Record your voice to create a personalized therapeutic experience</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">❤️</div>
            <h3 className="feature-title">Emotional Understanding</h3>
            <p className="feature-description">AI-powered emotion detection for truly empathetic responses</p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon">🛡️</div>
            <h3 className="feature-title">Safe & Private</h3>
            <p className="feature-description">Your conversations and voice data are secure and confidential</p>
          </div>
        </div>
        
        {/* Begin Journey Button */}
        <button className="begin-journey-button" onClick={handleBeginJourney}>
          Begin Your Journey
        </button>
      </div>
    </div>
  );
};

export default Welcome;

