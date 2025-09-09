import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { logout } from '../services/authService';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const navigate = useNavigate();
  const { isAuthenticated, logout: authLogout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
      authLogout(); // Update the auth context state
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, clear the local state
      authLogout();
      navigate('/login');
    }
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">Auth App</Link>
        <ul>
          {isAuthenticated ? (
            <>
              <li>
                <Link to="/dashboard">Dashboard</Link>
              </li>
              <li>
                <button onClick={handleLogout}>Logout</button>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link to="/login">Login</Link>
              </li>
              <li>
                <Link to="/register">Register</Link>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar; 