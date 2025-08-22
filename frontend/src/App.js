import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import Dashboard from './components/Dashboard';
import Navbar from './components/Navbar';
import GoogleCallback from './components/GoogleCallback';
import SupabaseCallback from './components/SupabaseCallback';
import './App.css';

// Component to handle Supabase error redirects and OAuth callbacks
const SupabaseErrorHandler = () => {
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const error = searchParams.get('error');
  const errorDescription = searchParams.get('error_description');

  React.useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // Check if we have error parameters in the URL
        if (error === 'invalid_request' && errorDescription?.includes('bad_oauth_state')) {
          // This is a Supabase OAuth state error, redirect to login
          window.location.href = '/login?error=supabase_oauth_state_error';
          return;
        }

        // Check for access token in URL hash (implicit flow)
        const hash = window.location.hash;
        if (!hash) {
          // No OAuth data, this might be a regular visit to root
          return;
        }

        // Parse the hash to extract session data
        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');
        const expiresIn = params.get('expires_in');
        const tokenType = params.get('token_type');

        if (!accessToken) {
          // No access token, this might be a regular visit to root
          return;
        }

        // Import Supabase client
        const { createClient } = await import('@supabase/supabase-js');
        
        const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
        const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
        
        if (!supabaseUrl || !supabaseAnonKey) {
          throw new Error('Supabase configuration is missing');
        }
        
        const supabase = createClient(supabaseUrl, supabaseAnonKey);

        // Create session from tokens
        const session = {
          access_token: accessToken,
          refresh_token: refreshToken,
          expires_in: parseInt(expiresIn) || 3600,
          token_type: tokenType || 'bearer',
          expires_at: Date.now() / 1000 + (parseInt(expiresIn) || 3600)
        };

        // Set the session manually
        await supabase.auth.setSession(session);

        // Get user info
        const { data: { user }, error: userError } = await supabase.auth.getUser();
        
        if (userError) {
          throw new Error(userError.message);
        }

        if (!user) {
          throw new Error('No user found after setting session');
        }

        // Store Supabase session in localStorage for our app
        localStorage.setItem('supabase_session', JSON.stringify(session));
        localStorage.setItem('token', accessToken);
        
        // Clear the hash from URL
        window.history.replaceState(null, '', window.location.pathname);
        
        // Redirect to dashboard on success
        window.location.href = '/dashboard';
      } catch (err) {
        console.error('Supabase OAuth callback error:', err);
        // Redirect to login with error
        window.location.href = `/login?error=oauth_error&message=${encodeURIComponent(err.message)}`;
      }
    };

    handleOAuthCallback();
  }, [error, errorDescription]);

  // Check if this is a successful OAuth callback (no error parameters)
  if (!error && !errorDescription) {
    // Check if we have a hash with access token
    const hash = window.location.hash;
    if (hash && hash.includes('access_token')) {
      // This is an OAuth callback, show loading
      return (
        <div className="auth-card">
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div style={{ marginBottom: '1rem' }}>
              <div className="loading-spinner"></div>
            </div>
            <h3>Authenticating with Supabase...</h3>
            <p>Please wait while we complete your authentication.</p>
          </div>
        </div>
      );
    }
  }

  return (
    <div className="auth-card">
      <div style={{ textAlign: 'center', padding: '2rem' }}>
        <h3>Authentication Error</h3>
        <p className="error">OAuth state error. Please try logging in again.</p>
        <button 
          onClick={() => window.location.href = '/login'}
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
};

function App() {
  const isAuthenticated = () => {
    return localStorage.getItem('token') !== null;
  };

  const ProtectedRoute = ({ children }) => {
    if (!isAuthenticated()) {
      return <Navigate to="/login" />;
    }
    return children;
  };

  return (
    <Router>
      <div className="App">
        <Navbar />
        <div className="container">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/auth/google/callback" element={<GoogleCallback />} />
            <Route path="/auth/supabase/callback" element={<SupabaseCallback />} />
            <Route path="/" element={<SupabaseErrorHandler />} />
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App; 