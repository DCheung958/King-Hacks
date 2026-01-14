import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './ProfileSetup.css';

const ProfileSetup = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!name.trim()) {
      setError('Please enter your name');
      return;
    }

    setLoading(true);
    
    // Store name in localStorage
    localStorage.setItem('user_name', name.trim());
    
    // Navigate to voice profile setup
    navigate('/voice-profile', { state: { userName: name.trim() } });
  };

  const handleSkip = () => {
    // Navigate to voice profile without name
    navigate('/voice-profile');
  };

  return (
    <div className="profile-setup-page">
      <div className="profile-setup-container">
        {/* Logo Circle */}
        <div className="logo-circle"></div>
        
        {/* Title */}
        <h1 className="profile-setup-title">
          Set Up Your Profile
        </h1>
        
        {/* Description */}
        <p className="profile-setup-description">
          Let's personalize your therapy experience. First, tell us your name.
        </p>
        
        {/* Form */}
        <form className="profile-setup-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="name" className="form-label">Your Name</label>
            <input
              type="text"
              id="name"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              required
              disabled={loading}
              autoFocus
            />
          </div>
          
          <button 
            type="submit" 
            className="continue-button"
            disabled={loading || !name.trim()}
          >
            {loading ? 'Loading...' : 'Continue'}
          </button>
          
          <button 
            type="button"
            className="skip-button"
            onClick={handleSkip}
            disabled={loading}
          >
            Skip for now
          </button>
        </form>
      </div>
    </div>
  );
};

export default ProfileSetup;

