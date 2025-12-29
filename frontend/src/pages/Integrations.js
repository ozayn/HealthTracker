import React, { useState, useEffect } from 'react';
import { apiFetch } from '../App';
import './Integrations.css';

function Integrations({ user }) {
  const [integrations, setIntegrations] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);

  const providers = [
    { name: 'fitbit', displayName: 'Fitbit', icon: 'F', color: '#00b0b9' },
    { name: 'oura', displayName: 'Oura Ring', icon: 'O', color: '#6772e5' },
    { name: 'clue', displayName: 'Clue', icon: 'C', color: '#ff5c8d' },
    { name: 'google_drive', displayName: 'Google Drive (Clue Data)', icon: 'G', color: '#4285f4' }
  ];

  useEffect(() => {
    if (user) {
      loadIntegrations();
    }
  }, [user]);

  const loadIntegrations = async () => {
    setLoading(true);
    try {
      const response = await apiFetch('/api/auth/integrations');
      const data = await response.json();
      setIntegrations(data);
    } catch (error) {
      console.error('Error loading integrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (provider) => {
    try {
      const response = await apiFetch(`/api/auth/${provider}/authorize?user_id=${user.id}`);
      const data = await response.json();
      
      if (data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        alert(`${provider} integration is not yet available. Please configure the API credentials.`);
      }
    } catch (error) {
      console.error(`Error connecting to ${provider}:`, error);
      alert(`Failed to connect to ${provider}`);
    }
  };

  const handleDisconnect = async (integrationId) => {
    if (!window.confirm('Are you sure you want to disconnect this integration?')) {
      return;
    }

    try {
      await apiFetch(`/api/auth/integrations/${integrationId}`, {
        method: 'DELETE'
      });
      loadIntegrations();
    } catch (error) {
      console.error('Error disconnecting integration:', error);
      alert('Failed to disconnect integration');
    }
  };

  const handleImportClueData = async () => {
    try {
      const response = await apiFetch('/api/clue/import-drive', {
        method: 'POST'
      });
      const data = await response.json();
      alert(`Clue data imported successfully!\n${JSON.stringify(data.data, null, 2)}`);
      // Optionally reload integrations or update UI
    } catch (error) {
      console.error('Error importing Clue data:', error);
      alert('Failed to import Clue data. Make sure Google Drive is connected.');
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const response = await apiFetch(`/api/health/sync/${user.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days: 30 })
      });
      const result = await response.json();
      
      alert('Sync completed! Check the console for details.');
      console.log('Sync results:', result);
      
      loadIntegrations();
    } catch (error) {
      console.error('Error syncing data:', error);
      alert('Failed to sync data');
    } finally {
      setSyncing(false);
    }
  };

  const getIntegration = (providerName) => {
    return integrations.find(i => i.provider === providerName && i.is_active);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="integrations-page">
      <div className="page-header">
        <div>
          <h2>Integrations</h2>
          <p className="subtitle">Connect your health tracking devices</p>
        </div>
        {integrations.some(i => i.is_active) && (
          <button 
            className="btn btn-primary" 
            onClick={handleSync}
            disabled={syncing}
          >
            {syncing ? 'Syncing...' : 'Sync All Data'}
          </button>
        )}
      </div>

      <div className="providers-grid">
        {providers.map(provider => {
          const integration = getIntegration(provider.name);
          const isConnected = !!integration;

          return (
            <div key={provider.name} className="provider-card card">
              <div className="provider-header">
                <div 
                  className="provider-icon-large" 
                  style={{ background: provider.color }}
                >
                  {provider.icon}
                </div>
                <div className="provider-info">
                  <h3>{provider.displayName}</h3>
                  {isConnected && integration.last_sync && (
                    <p className="provider-sync">
                      Last synced: {new Date(integration.last_sync).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>

              <div className="provider-status">
                {isConnected ? (
                  <span className="status-badge status-connected">Connected</span>
                ) : (
                  <span className="status-badge status-disconnected">Not Connected</span>
                )}
              </div>

              <div className="provider-description">
                {provider.name === 'fitbit' && 'Track steps, heart rate, sleep, and activities'}
                {provider.name === 'oura' && 'Track sleep quality, readiness, and activity'}
                {provider.name === 'clue' && 'Track menstrual cycle and reproductive health'}
                {provider.name === 'google_drive' && 'Import Clue data from Google Drive (supports ClueDataDownload folders)'}
              </div>

              <div className="provider-actions">
                {isConnected ? (
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleDisconnect(integration.id)}
                    >
                      Disconnect
                    </button>
                    {provider.name === 'clue' && integrations.some(i => i.provider === 'google_drive' && i.is_active) && (
                      <button
                        className="btn btn-success"
                        onClick={handleImportClueData}
                      >
                        Import from Drive
                      </button>
                    )}
                  </div>
                ) : (
                  <button
                    className="btn btn-primary"
                    onClick={() => handleConnect(provider.name)}
                  >
                    Connect
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="card" style={{ marginTop: '2rem' }}>
        <div className="card-header">Setup Instructions</div>
        <div className="instructions">
          <ol>
            <li>Register for developer accounts at Fitbit, Oura, and/or Clue</li>
            <li>Create OAuth applications and get your client IDs and secrets</li>
            <li>Add the credentials to your .env file</li>
            <li>Click "Connect" to authorize the integration</li>
            <li>Your data will automatically sync every time you visit the app</li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default Integrations;

