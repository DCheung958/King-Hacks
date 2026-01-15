import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './SignIn.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SignIn = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGoogleSignIn = async () => {
    setError('');
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/google`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to initiate Google sign in');
      }
      
      // Redirect to Google OAuth
      window.location.href = data.auth_url;
    } catch (err) {
      setError(err.message || 'Failed to sign in with Google');
      setLoading(false);
      console.error('Google sign in error:', err);
    }
  };

  const handleSubmit = async (e) => {
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
        throw new Error(data.detail || 'Login failed');
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

      // Redirect to chat
      navigate('/chat');
    } catch (err) {
      setError(err.message || 'An error occurred. Please try again.');
      console.error('Sign in error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="signin-page">
      <div className="signin-container">
        {/* Logo Circle */}
        <div className="logo-circle"></div>
        
        {/* Title */}
        <h1 className="signin-title">
          Welcome to <span className="title-echocare">Echocare</span>
        </h1>
        
        {/* Description */}
        <p className="signin-description">
          Sign in to continue your healing journey, or create a new account
        </p>
        
        {/* Sign In Form */}
        <form className="signin-form" onSubmit={handleSubmit}>
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
            {loading ? 'Signing in...' : 'Sign In / Create Account'}
          </button>
          
          <div className="divider">
            <span>or</span>
          </div>
          
          <button
            type="button"
            className="google-signin-button"
            onClick={handleGoogleSignIn}
            disabled={loading}
          >
            <svg className="google-icon" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>
          
          <p className="signin-help">
            Don't have an account? Just enter your email and password above, and we'll create one for you automatically.
          </p>
        </form>
      </div>
    </div>
  );
};

export default SignIn;

