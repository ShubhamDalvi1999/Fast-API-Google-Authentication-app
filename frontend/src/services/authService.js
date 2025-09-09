import axios from 'axios';

// Auto-detect API URL based on environment
const API_URL = process.env.REACT_APP_API_URL || (
  process.env.NODE_ENV === 'production' 
    ? 'https://your-backend-domain.com/api/auth'  // Replace with your actual backend URL
    : 'http://localhost:8000/api/auth'
);

// Create an axios instance with common settings
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false  // Changed to false since we don't need credentials for Google OAuth
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('Making request to:', config.url);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('Response received:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('Response error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// Helper function to safely extract error message
const extractErrorMessage = (error) => {
  if (!error) return 'An unknown error occurred';
  
  if (error.response) {
    const { data } = error.response;
    // FastAPI validation errors have a specific format
    if (data && typeof data === 'object') {
      if (data.detail) {
        // If detail is a string, return it
        if (typeof data.detail === 'string') {
          return data.detail;
        }
        // If detail is an array (validation errors), format it
        if (Array.isArray(data.detail)) {
          return data.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
        }
        // If detail is an object, stringify it
        return JSON.stringify(data.detail);
      }
      // Other structured error
      return JSON.stringify(data);
    }
    return data || 'Server error';
  }
  
  if (error.message) return error.message;
  
  return 'An unexpected error occurred';
};

// Register a new user
export const register = async (username, password) => {
  try {
    const response = await api.post('/', {
      username,
      password
    });
    return response.data;
  } catch (error) {
    console.error('Registration error:', error);
    throw extractErrorMessage(error);
  }
};

// Login user and get token
export const login = async (username, password) => {
  try {
    // FastAPI's OAuth2PasswordRequestForm requires x-www-form-urlencoded format
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    
    // Override content-type for this specific request
    const response = await axios.post(`${API_URL}/token`, params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      withCredentials: false  // Changed to false to match the CORS configuration
    });
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw extractErrorMessage(error);
  }
};

// Get current user
export const getCurrentUser = async () => {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('No token found. Please login again.');
    }
    
    const response = await api.get('/users/me', {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    console.error('Get user error:', error);
    throw extractErrorMessage(error);
  }
};

// Logout user
export const logout = async () => {
  try {
    // Check if we have a Supabase session
    const supabaseSession = localStorage.getItem('supabase_session');
    
    if (supabaseSession) {
      // Sign out from Supabase
      const { createClient } = await import('@supabase/supabase-js');
      
      const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
      const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
      
      if (supabaseUrl && supabaseAnonKey) {
        const supabase = createClient(supabaseUrl, supabaseAnonKey);
        
        // Sign out from Supabase
        const { error } = await supabase.auth.signOut();
        if (error) {
          console.error('Supabase logout error:', error);
        }
      }
      
      // Clear Supabase session
      localStorage.removeItem('supabase_session');
    }
    
    // Clear JWT token
    localStorage.removeItem('token');
    
    return true;
  } catch (error) {
    console.error('Logout error:', error);
    // Even if there's an error, clear the local tokens
    localStorage.removeItem('token');
    localStorage.removeItem('supabase_session');
    return true;
  }
};

// Google OAuth functions
export const getGoogleAuthUrl = async () => {
  try {
    const response = await api.get('/google/authorize');
    return response.data;
  } catch (error) {
    console.error('Get Google auth URL error:', error);
    const errorMessage = extractErrorMessage(error);
    
    // Check if Google OAuth is disabled
    if (errorMessage.includes('not configured') || errorMessage.includes('disabled')) {
      throw new Error('Google OAuth is not configured on the server. Please contact the administrator.');
    }
    
    throw errorMessage;
  }
};

export const handleGoogleCallback = async (code, state, nonce = null) => {
  try {
    const requestData = {
      code,
      state
    };
    
    // Only include nonce if it's not null
    if (nonce) {
      requestData.nonce = nonce;
    }
    
    console.log('Sending Google callback data:', requestData);
    
    const response = await api.post('/google/callback', requestData);
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  } catch (error) {
    console.error('Google callback error:', error);
    const errorMessage = extractErrorMessage(error);
    
    // Check if Google OAuth is disabled
    if (errorMessage.includes('not configured') || errorMessage.includes('disabled')) {
      throw new Error('Google OAuth is not configured on the server. Please contact the administrator.');
    }
    
    throw errorMessage;
  }
};

// Handle Google OAuth redirect with state management
export const initiateGoogleLogin = async () => {
  try {
    const authData = await getGoogleAuthUrl();
    
    // Store state in sessionStorage for validation during callback
    sessionStorage.setItem('google_oauth_state', authData.state);
    
    // Redirect to Google OAuth
    window.location.href = authData.authorization_url;
  } catch (error) {
    console.error('Google login initiation error:', error);
    throw error;
  }
};

// Check if Google OAuth is available
export const isGoogleOAuthAvailable = async () => {
  try {
    await getGoogleAuthUrl();
    return true;
  } catch (error) {
    return false;
  }
};

// Supabase OAuth functions
export const getSupabaseAuthUrl = async (provider = "google") => {
  try {
    // Use direct Supabase OAuth instead of going through our backend
    const { createClient } = await import('@supabase/supabase-js');
    
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ;
    
    const supabase = createClient(supabaseUrl, supabaseAnonKey);
    
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: provider,
      options: {
        redirectTo: 'http://localhost:3000/auth/supabase/callback'
      }
    });
    
    if (error) throw error;
    
    // The redirect will happen automatically
    return data;
  } catch (error) {
    console.error('Get Supabase auth URL error:', error);
    const errorMessage = extractErrorMessage(error);
    
    // Check if Supabase Auth is disabled
    if (errorMessage.includes('not configured') || errorMessage.includes('disabled')) {
      throw new Error('Supabase Auth is not configured on the server. Please contact the administrator.');
    }
    
    throw errorMessage;
  }
};



// Supabase email/password authentication
export const supabaseSignup = async (email, password) => {
  try {
    const response = await api.post('/supabase/signup', { email, password });
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  } catch (error) {
    console.error('Supabase signup error:', error);
    throw extractErrorMessage(error);
  }
};

export const supabaseSignin = async (email, password) => {
  try {
    const response = await api.post('/supabase/signin', { email, password });
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  } catch (error) {
    console.error('Supabase signin error:', error);
    throw extractErrorMessage(error);
  }
};

// Direct Supabase OAuth (frontend-to-Supabase)
export const initiateSupabaseLogin = async (provider = "google") => {
  try {
    // Use Supabase client directly for OAuth
    const { createClient } = await import('@supabase/supabase-js');
    
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    
    if (!supabaseUrl || !supabaseAnonKey) {
      throw new Error('Supabase configuration is missing. Please check your environment variables.');
    }
    
    const supabase = createClient(supabaseUrl, supabaseAnonKey);
    
    // Simple OAuth call - let Supabase handle everything
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: provider
    });
    
    if (error) {
      throw new Error(error.message);
    }
    
    return data;
  } catch (error) {
    console.error('Supabase login initiation error:', error);
    throw error;
  }
};

// Get current Supabase user
export const getSupabaseUser = async () => {
  try {
    const { createClient } = await import('@supabase/supabase-js');
    
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    
    if (!supabaseUrl || !supabaseAnonKey) {
      throw new Error('Supabase configuration is missing');
    }
    
    const supabase = createClient(supabaseUrl, supabaseAnonKey);
    
    const { data: { user }, error } = await supabase.auth.getUser();
    
    if (error) {
      throw new Error(error.message);
    }
    
    return user;
  } catch (error) {
    console.error('Get Supabase user error:', error);
    throw error;
  }
};

// Check if Supabase Auth is available
export const isSupabaseAuthAvailable = async () => {
  try {
    await api.get('/supabase/authorize?provider=google');
    return true;
  } catch (error) {
    return false;
  }
}; 