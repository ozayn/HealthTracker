import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../App';
import './Dashboard.css';

function Dashboard({ user }) {
  const [integrations, setIntegrations] = useState([]);
  const [healthSummary, setHealthSummary] = useState({});
  const [bloodTests, setBloodTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    if (user) {
      loadDashboardData();
    }
  }, [user]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Load integrations
      const integrationsResponse = await apiFetch('/api/auth/integrations');
      const integrationsData = await integrationsResponse.json();
      setIntegrations(integrationsData);

      // Load health summary
      const healthResponse = await apiFetch('/api/health/summary?days=7');
      const healthData = await healthResponse.json();
      setHealthSummary(healthData);

      // Load recent blood tests
      const bloodTestsResponse = await apiFetch('/api/blood-tests');
      const bloodTestsData = await bloodTestsResponse.json();
      setBloodTests(bloodTestsData.slice(0, 3)); // Show only 3 most recent
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const syncHealthData = async () => {
    console.log('Sync button clicked!');
    setSyncing(true);
    try {
      console.log('Making sync API call...');
      const response = await apiFetch('/api/health/sync', {
        method: 'POST',
        body: JSON.stringify({ days: 7 }) // Sync last 7 days
      });

      console.log('Sync response status:', response.status);
      const results = await response.json();
      console.log('Sync results:', results);

      // Reload dashboard data after sync
      await loadDashboardData();

      alert('Health data synced successfully!');
    } catch (error) {
      console.error('Error syncing health data:', error);
      alert(`Error syncing health data: ${error.message}`);
    } finally {
      setSyncing(false);
    }
  };

  const connectedIntegrations = integrations.filter(i => i.is_active);
  const availableIntegrations = ['fitbit', 'oura', 'clue'].filter(
    provider => !connectedIntegrations.find(i => i.provider === provider)
  );

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        <p className="subtitle">Your health overview</p>
        <button
          onClick={syncHealthData}
          className="btn btn-secondary"
          disabled={syncing}
          style={{ marginTop: '1rem' }}
        >
          {syncing ? 'Syncing...' : 'Sync Health Data'}
        </button>
      </div>

      <div className="dashboard-grid">
        {/* Integrations Card */}
        <div className="card">
          <div className="card-header">
            <span>Integrations</span>
            <Link to="/integrations" className="card-link">Manage</Link>
          </div>
          <div className="integrations-list">
            {connectedIntegrations.length === 0 ? (
              <p className="empty-state">No integrations connected</p>
            ) : (
              connectedIntegrations.map(integration => (
                <div key={integration.id} className="integration-item">
                  <div className="integration-icon">{integration.provider[0].toUpperCase()}</div>
                  <div className="integration-info">
                    <div className="integration-name">{integration.provider}</div>
                    {integration.last_sync && (
                      <div className="integration-sync">
                        Last sync: {new Date(integration.last_sync).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                  <span className="status-badge status-connected">Connected</span>
                </div>
              ))
            )}
          </div>
          {availableIntegrations.length > 0 && (
            <Link to="/integrations" className="btn btn-secondary" style={{ marginTop: '1rem' }}>
              Connect More
            </Link>
          )}
        </div>

        {/* Health Summary Card */}
        <div className="card">
          <div className="card-header">
            <span>Health Summary</span>
            <Link to="/health-data" className="card-link">View All</Link>
          </div>
          <div className="health-metrics">
            {Object.keys(healthSummary).length === 0 ? (
              <p className="empty-state">No health data yet</p>
            ) : (
              Object.entries(healthSummary).slice(0, 4).map(([type, data]) => (
                <div key={type} className="metric-item">
                  <div className="metric-label">{type.replace(/_/g, ' ')}</div>
                  <div className="metric-value">
                    {data.values.length > 0 && (
                      <>
                        {data.values[data.values.length - 1].value.toFixed(1)} 
                        <span className="metric-unit">{data.unit}</span>
                      </>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Blood Tests Card */}
        <div className="card">
          <div className="card-header">
            <span>Recent Blood Tests</span>
            <Link to="/blood-tests" className="card-link">View All</Link>
          </div>
          <div className="blood-tests-list">
            {bloodTests.length === 0 ? (
              <p className="empty-state">No blood tests recorded</p>
            ) : (
              bloodTests.map(test => (
                <div key={test.id} className="blood-test-item">
                  <div className="blood-test-date">
                    {new Date(test.test_date).toLocaleDateString()}
                  </div>
                  <div className="blood-test-lab">{test.lab_name || 'Lab Test'}</div>
                  <div className="blood-test-markers">
                    {test.markers.length} markers
                  </div>
                </div>
              ))
            )}
          </div>
          <Link to="/blood-tests" className="btn btn-primary" style={{ marginTop: '1rem' }}>
            Add Blood Test
          </Link>
        </div>

        {/* Quick Stats Card */}
        <div className="card">
          <div className="card-header">Stats</div>
          <div className="stats-grid">
            <div className="stat-box">
              <div className="stat-number">{connectedIntegrations.length}</div>
              <div className="stat-label">Connected</div>
            </div>
            <div className="stat-box">
              <div className="stat-number">{Object.keys(healthSummary).length}</div>
              <div className="stat-label">Metrics</div>
            </div>
            <div className="stat-box">
              <div className="stat-number">{bloodTests.length}</div>
              <div className="stat-label">Blood Tests</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

