import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Onboarding.css';

const Onboarding = () => {
  const navigate = useNavigate();

  const handleBeginJourney = () => {
    navigate('/chat');
  };

  return (
    <div className="onboarding-page">
      <div className="onboarding-container">
        {/* Logo Circle */}
        <div className="logo-circle"></div>
        
        {/* Title */}
        <h1 className="onboarding-title">
          Welcome to <span className="title-echocare">Echocare</span>
        </h1>
        
        {/* Description */}
        <p className="onboarding-description">
          Experience personalized emotional therapy with AI that speaks in your own voice, creating a deeply personal healing journey.
        </p>
        
        {/* Feature Cards */}
        <div className="feature-cards">
          <div className="feature-card">
            <div className="feature-icon-circle">
              <svg className="feature-icon" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 14C13.1046 14 14 13.1046 14 12V5C14 3.89543 13.1046 3 12 3C10.8954 3 10 3.89543 10 5V12C10 13.1046 10.8954 14 12 14Z"/>
                <path d="M19 10V12C19 15.866 15.866 19 12 19C8.13401 19 5 15.866 5 12V10H7V12C7 14.7614 9.23858 17 12 17C14.7614 17 17 14.7614 17 12V10H19Z"/>
                <path d="M11 22H13V20H11V22Z"/>
              </svg>
            </div>
            <h3 className="feature-title">Your Voice, Your Therapy</h3>
            <p className="feature-description">
              Record your voice to create a personalized therapeutic experience.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon-circle">
              <svg className="feature-icon" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 21.35L10.55 20.03C5.4 15.36 2 12.28 2 8.5C2 5.42 4.42 3 7.5 3C9.24 3 10.91 3.81 12 5.09C13.09 3.81 14.76 3 16.5 3C19.58 3 22 5.42 22 8.5C22 12.28 18.6 15.36 13.45 20.04L12 21.35Z"/>
              </svg>
            </div>
            <h3 className="feature-title">Emotional Understanding</h3>
            <p className="feature-description">
              AI-powered emotion detection for truly empathetic responses.
            </p>
          </div>
          
          <div className="feature-card">
            <div className="feature-icon-circle">
              <svg className="feature-icon" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 1L3 5V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V5L12 1Z"/>
              </svg>
            </div>
            <h3 className="feature-title">Safe & Private</h3>
            <p className="feature-description">
              Your conversations and voice data are secure and confidential.
            </p>
          </div>
        </div>
        
        {/* Begin Your Journey Button */}
        <button 
          className="begin-journey-button"
          onClick={handleBeginJourney}
        >
          Begin Your Journey
        </button>
      </div>
    </div>
  );
};

export default Onboarding;

