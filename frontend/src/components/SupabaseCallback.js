import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const SupabaseCallback = () => {
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();
  const { login: authLogin } = useAuth();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check if we have error parameters in the URL
        const urlParams = new URLSearchParams(location.search);
        const error = urlParams.get('error');
        const errorDescription = urlParams.get('error_description');

        if (error) {
          setError(`Supabase OAuth error: ${error}${errorDescription ? ` - ${errorDescription}` : ''}`);
          setLoading(false);
          return;
        }

        // Check for access token in URL hash (implicit flow)
        const hash = window.location.hash;
        if (!hash) {
          setError('No OAuth data found in URL');
          setLoading(false);
          return;
        }

        // Parse the hash to extract session data
        const params = new URLSearchParams(hash.substring(1));
        const accessToken = params.get('access_token');
        const refreshToken = params.get('refresh_token');
        const expiresIn = params.get('expires_in');
        const tokenType = params.get('token_type');

        if (!accessToken) {
          setError('No access token found in URL');
          setLoading(false);
          return;
        }

        // Import Supabase client
        const { createClient } = await import('@supabase/supabase-js');
        
        const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
        const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
        
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
        
        // Update auth context
        authLogin({
          username: user.user_metadata?.full_name || user.email?.split('@')[0] || 'Supabase User',
          email: user.email,
          auth_method: 'supabase',
          supabase_id: user.id,
          supabase_email: user.email
        });
        
        // Redirect to dashboard on success
        navigate('/dashboard');
      } catch (err) {
        console.error('Supabase callback error:', err);
        setError(err.message || 'Failed to authenticate with Supabase');
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
          <h3>Authenticating with Supabase...</h3>
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

export default SupabaseCallback;
