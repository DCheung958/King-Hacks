import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignUp.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SignUp = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!email || !password || !confirmPassword) {
      setError('Please fill in all required fields');
      setLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          password: password,
          name: name.trim() || null,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Sign up failed');
      }

      // Store token and user info
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('user_email', data.email);
      if (data.name) {
        localStorage.setItem('user_name', data.name);
      }
      
      // Store voice profile if available (unlikely on signup, but handle it)
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
      console.error('Sign up error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToSignIn = () => {
    navigate('/');
  };

  return (
    <div className="signup-page">
      <div className="signup-container">
        {/* Logo Circle */}
        <div className="logo-circle"></div>
        
        {/* Title */}
        <h1 className="signup-title">
          Create Your <span className="title-echocare">Echocare</span> Account
        </h1>
        
        {/* Description */}
        <p className="signup-description">
          Start your personalized healing journey today
        </p>
        
        {/* Sign Up Form */}
        <form className="signup-form" onSubmit={handleSubmit}>
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="name" className="form-label">Name (Optional)</label>
            <input
              type="text"
              id="name"
              className="form-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email *</label>
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
            <label htmlFor="password" className="form-label">Password *</label>
            <input
              type="password"
              id="password"
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              required
              disabled={loading}
              minLength={6}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword" className="form-label">Confirm Password *</label>
            <input
              type="password"
              id="confirmPassword"
              className="form-input"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter your password"
              required
              disabled={loading}
              minLength={6}
            />
          </div>
          
          <button 
            type="submit" 
            className="signup-button"
            disabled={loading}
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
          
          <div className="signin-link">
            <span>Already have an account? </span>
            <button 
              type="button"
              className="link-button"
              onClick={handleBackToSignIn}
              disabled={loading}
            >
              Sign In
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SignUp;

