import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { handleGoogleCallback } from '../services/authService';

const GoogleCallback = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get the authorization code from URL parameters
        const urlParams = new URLSearchParams(location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        const error = urlParams.get('error');

        if (error) {
          setError(`Google OAuth error: ${error}`);
          setLoading(false);
          return;
        }

        if (!code) {
          setError('No authorization code received from Google');
          setLoading(false);
          return;
        }

        if (!state) {
          setError('No state parameter received from Google');
          setLoading(false);
          return;
        }

        // Get stored state from sessionStorage
        const storedState = sessionStorage.getItem('google_oauth_state');
        if (!storedState) {
          setError('No stored state found. Please try logging in again.');
          setLoading(false);
          return;
        }

        // Validate state parameter
        if (state !== storedState) {
          setError('Invalid state parameter. Possible CSRF attack.');
          setLoading(false);
          return;
        }

        // Clear stored state
        sessionStorage.removeItem('google_oauth_state');

        // Exchange code for token
        await handleGoogleCallback(code, state);
        
        // Redirect to dashboard on success
        navigate('/dashboard');
      } catch (err) {
        console.error('Google callback error:', err);
        setError(err.message || 'Failed to authenticate with Google');
        setLoading(false);
      }
    };

    handleCallback();
  }, [navigate, location]);

  if (loading) {
    return (
      <div className="auth-card">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{ marginBottom: '1rem' }}>
            <div className="loading-spinner"></div>
          </div>
          <h3>Authenticating with Google...</h3>
          <p>Please wait while we complete your authentication.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="auth-card">
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <h3>Authentication Failed</h3>
          <p className="error">{error}</p>
          <button 
            onClick={() => navigate('/login')}
            style={{ 
              marginTop: '1rem',
              padding: '0.75rem 1.5rem',
              backgroundColor: 'var(--primary-color)',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Back to Login
          </button>
        </div>
      </div>
    );
  }

  return null;
};

export default GoogleCallback;
