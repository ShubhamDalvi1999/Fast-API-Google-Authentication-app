import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    const checkAuthStatus = () => {
      const token = localStorage.getItem('token');
      const supabaseSession = localStorage.getItem('supabase_session');
      
      if (token || supabaseSession) {
        setIsAuthenticated(true);
        // Optionally fetch user data here
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
      setLoading(false);
    };

    checkAuthStatus();
  }, []);

  // Listen for storage changes (for logout from other tabs)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'token' || e.key === 'supabase_session') {
        const token = localStorage.getItem('token');
        const supabaseSession = localStorage.getItem('supabase_session');
        
        if (token || supabaseSession) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
          setUser(null);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const login = (userData) => {
    setIsAuthenticated(true);
    setUser(userData);
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUser(null);
  };

  const value = {
    isAuthenticated,
    user,
    loading,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
