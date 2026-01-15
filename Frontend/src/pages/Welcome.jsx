import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Welcome.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Welcome = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!email || !password) {
      setError('Please enter both email and password');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Check if user doesn't exist (401 could be wrong password or user not found)
        if (response.status === 401 || response.status === 404) {
          throw new Error(data.detail || 'Invalid email or password');
        }
        throw new Error(data.detail || 'Sign in failed');
      }

      // Store token and user info
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('user_email', data.email);
      if (data.name) {
        localStorage.setItem('user_name', data.name);
      }
      
      // Store voice profile if available
      if (data.voice_id) {
        localStorage.setItem('voice_id', data.voice_id);
      }
      if (data.voice_name) {
        localStorage.setItem('voice_name', data.voice_name);
      }

      // Redirect to onboarding
      navigate('/onboarding');
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
      console.error('Sign in error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAccount = () => {
    navigate('/signup');
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
        
        {/* Sign In Form */}
        <div className="signin-section">
          <form className="signin-form" onSubmit={handleSignIn}>
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}
            
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email</label>
              <input
                type="email"
                id="email"
                className="form-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                disabled={loading}
                minLength={6}
              />
            </div>
            
            <button 
              type="submit" 
              className="signin-button"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          
          <div className="signup-divider">
            <span>Don't have an account?</span>
          </div>
          
          <button 
            className="create-account-button"
            onClick={handleCreateAccount}
            disabled={loading}
          >
            Create Account
          </button>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
