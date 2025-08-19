import React, { useState, useEffect } from 'react';
import { getCurrentUser } from '../services/authService';

const Dashboard = () => {
  const [userData, setUserData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const data = await getCurrentUser();
        setUserData(data);
      } catch (err) {
        setError(err.detail || 'Failed to fetch user data');
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);

  const getAuthMethodDisplay = (authMethod) => {
    switch (authMethod) {
      case 'local':
        return 'Email & Password';
      case 'google':
        return 'Google Account';
      case 'both':
        return 'Email & Google';
      default:
        return 'Email & Password';
    }
  };

  const getAuthMethodIcon = (authMethod) => {
    switch (authMethod) {
      case 'google':
      case 'both':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" style={{ marginRight: '8px' }}>
            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
        );
      default:
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" style={{ marginRight: '8px' }}>
            <path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>
        );
    }
  };

  if (loading) {
    return (
      <div className="auth-card" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (error) {
    return <div className="auth-card"><div className="error">{error}</div></div>;
  }

  return (
    <div className="auth-card">
      <h2>Dashboard</h2>
      {userData && (
        <div className="dashboard-content">
          <div className="user-info">
            <div className="user-avatar">
              {userData.username.charAt(0).toUpperCase()}
            </div>
            <div className="user-details">
              <h3>Welcome, {userData.username}!</h3>
              <p className="user-id">User ID: {userData.id}</p>
              {userData.email && (
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.3rem' }}>
                  Email: {userData.email}
                </p>
              )}
            </div>
          </div>
          
          <div className="stats-container">
            <div className="stat-card">
              <h4>Account Status</h4>
              <p className="stat-value">Active</p>
            </div>
            <div className="stat-card">
              <h4>Authentication Method</h4>
              <p className="stat-value" style={{ display: 'flex', alignItems: 'center' }}>
                {getAuthMethodIcon(userData.auth_method)}
                {getAuthMethodDisplay(userData.auth_method)}
              </p>
            </div>
            <div className="stat-card">
              <h4>Last Login</h4>
              <p className="stat-value">Just Now</p>
            </div>
            <div className="stat-card">
              <h4>Account Type</h4>
              <p className="stat-value">
                {userData.auth_method === 'both' ? 'Hybrid' : 
                 userData.auth_method === 'google' ? 'Google OAuth' : 'Local'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard; 