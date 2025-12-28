import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Integrations from './pages/Integrations';
import BloodTests from './pages/BloodTests';
import HealthData from './pages/HealthData';
import Login from './pages/Login';

// API base URL - use relative URLs since frontend and API are on same server
const API_BASE = '';

// Helper function for authenticated API calls
const apiFetch = (url, options = {}) => {
  return fetch(`${API_BASE}${url}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
};

export { API_BASE, apiFetch };

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('App component mounted');
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    console.log('Checking auth status...');
    try {
      const response = await fetch(`${API_BASE}/api/auth/status`);
      const data = await response.json();
      console.log('Auth status response:', data);

      if (data.authenticated) {
        console.log('User is authenticated:', data.user);
        setUser(data.user);
      } else {
        console.log('User is not authenticated');
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      setLoading(false);
      console.log('Auth check complete, loading:', false);
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST' });
      setUser(null);
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  if (loading) {
    console.log('Rendering loading spinner');
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!user) {
    console.log('Rendering Login component');
    return <Login onLogin={handleLogin} />;
  }

  console.log('Rendering main app with user:', user);

  return (
    <Router>
      <div className="App">
        <Header user={user} onLogout={handleLogout} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard user={user} />} />
            <Route path="/integrations" element={<Integrations user={user} />} />
            <Route path="/blood-tests" element={<BloodTests user={user} />} />
            <Route path="/health-data" element={<HealthData user={user} />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

