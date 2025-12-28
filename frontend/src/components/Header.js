import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

function Header({ user, onLogout }) {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;

  return (
    <header className="header">
      <div className="header-container">
        <div className="header-logo">
          <h1>Health Tracker</h1>
        </div>
        
        <nav className="header-nav">
          <Link 
            to="/dashboard" 
            className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`}
          >
            Dashboard
          </Link>
          <Link 
            to="/integrations" 
            className={`nav-link ${isActive('/integrations') ? 'active' : ''}`}
          >
            Integrations
          </Link>
          <Link 
            to="/health-data" 
            className={`nav-link ${isActive('/health-data') ? 'active' : ''}`}
          >
            Health Data
          </Link>
          <Link 
            to="/blood-tests" 
            className={`nav-link ${isActive('/blood-tests') ? 'active' : ''}`}
          >
            Blood Tests
          </Link>
        </nav>
        
        {user && (
          <div className="header-user">
            <span className="user-email">{user.email}</span>
            <button
              className="logout-btn"
              onClick={onLogout}
              title="Logout"
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;

