import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import './AuthCallback.css';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState('processing');

  useEffect(() => {
    const token = searchParams.get('token');
    const userId = searchParams.get('user_id');
    const email = searchParams.get('email');
    const name = searchParams.get('name');

    if (token && userId && email) {
      // Store authentication data
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_id', userId);
      localStorage.setItem('user_email', email);
      if (name) {
        localStorage.setItem('user_name', name);
      }

      setStatus('success');
      
      // Redirect to chat after a brief delay
      setTimeout(() => {
        navigate('/chat');
      }, 1500);
    } else {
      setStatus('error');
      // Redirect to sign in after showing error
      setTimeout(() => {
        navigate('/');
      }, 3000);
    }
  }, [searchParams, navigate]);

  return (
    <div className="auth-callback-page">
      <div className="auth-callback-container">
        <div className="logo-circle"></div>
        {status === 'processing' && (
          <>
            <h1 className="auth-callback-title">Completing sign in...</h1>
            <div className="spinner"></div>
          </>
        )}
        {status === 'success' && (
          <>
            <h1 className="auth-callback-title">Success!</h1>
            <p className="auth-callback-message">Redirecting to your chat...</p>
          </>
        )}
        {status === 'error' && (
          <>
            <h1 className="auth-callback-title">Authentication Error</h1>
            <p className="auth-callback-message">Something went wrong. Redirecting to sign in...</p>
          </>
        )}
      </div>
    </div>
  );
};

export default AuthCallback;
