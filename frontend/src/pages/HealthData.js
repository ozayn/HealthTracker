import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { apiFetch } from '../App';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import './HealthData.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  TimeScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function HealthData({ user }) {
  const [healthData, setHealthData] = useState([]);
  const [dataTypes, setDataTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [dateRange, setDateRange] = useState('30');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      loadDataTypes();
      loadHealthData();
    }
  }, [user, selectedType, dateRange]);

  const loadDataTypes = async () => {
    try {
      const response = await apiFetch('/api/health/types');
      const types = await response.json();
      setDataTypes(types);
      if (types.length > 0 && !selectedType) {
        setSelectedType(types[0]);
      }
    } catch (error) {
      console.error('Error loading data types:', error);
    }
  };

  const loadHealthData = async () => {
    setLoading(true);
    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - parseInt(dateRange));

      const params = new URLSearchParams({
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString()
      });

      if (selectedType) {
        params.append('data_type', selectedType);
      }

      const response = await apiFetch(`/api/health?${params}`);
      const data = await response.json();
      setHealthData(data);
    } catch (error) {
      console.error('Error loading health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = () => {
    if (!healthData.length) {
      return null;
    }

    // Group by provider
    const groupedData = {};
    healthData.forEach(item => {
      if (!groupedData[item.provider]) {
        groupedData[item.provider] = [];
      }
      groupedData[item.provider].push(item);
    });

    // Sort each group by date
    Object.keys(groupedData).forEach(provider => {
      groupedData[provider].sort((a, b) => new Date(a.date) - new Date(b.date));
    });

    const colors = {
      fitbit: { border: '#00b0b9', bg: 'rgba(0, 176, 185, 0.1)' },
      oura: { border: '#6772e5', bg: 'rgba(103, 114, 229, 0.1)' },
      clue: { border: '#ff5c8d', bg: 'rgba(255, 92, 141, 0.1)' }
    };

    const datasets = Object.entries(groupedData).map(([provider, data]) => ({
      label: provider.charAt(0).toUpperCase() + provider.slice(1),
      data: data.map(item => ({
        x: item.date,
        y: item.value
      })),
      borderColor: colors[provider]?.border || '#ff7744',
      backgroundColor: colors[provider]?.bg || 'rgba(255, 119, 68, 0.1)',
      borderWidth: 2,
      tension: 0.4,
      fill: true,
      pointRadius: 4,
      pointHoverRadius: 6
    }));

    return {
      datasets
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
          }
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14
        },
        bodyFont: {
          size: 13
        },
        callbacks: {
          label: function(context) {
            const unit = healthData.find(d => d.provider === context.dataset.label.toLowerCase())?.unit || '';
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)} ${unit}`;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time',
        time: {
          unit: dateRange <= 7 ? 'day' : dateRange <= 30 ? 'day' : 'week',
          displayFormats: {
            day: 'MMM d',
            week: 'MMM d'
          }
        },
        grid: {
          display: false
        },
        ticks: {
          font: {
            size: 11
          }
        }
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        },
        ticks: {
          font: {
            size: 11
          }
        }
      }
    }
  };

  const chartData = prepareChartData();

  const getStats = () => {
    if (!healthData.length) return null;

    const values = healthData.map(d => d.value);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const min = Math.min(...values);
    const max = Math.max(...values);
    const unit = healthData[0]?.unit || '';

    return { avg, min, max, unit };
  };

  const stats = getStats();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="health-data-page">
      <div className="page-header">
        <div>
          <h2>Health Data</h2>
          <p className="subtitle">Visualize your health metrics over time</p>
        </div>
      </div>

      <div className="filters-section card">
        <div className="filter-group">
          <label className="filter-label">Metric</label>
          <select 
            className="filter-select"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
          >
            {dataTypes.map(type => (
              <option key={type} value={type}>
                {type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Time Range</label>
          <select 
            className="filter-select"
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
          >
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="180">Last 6 months</option>
            <option value="365">Last year</option>
          </select>
        </div>
      </div>

      {healthData.length === 0 ? (
        <div className="card">
          <p className="empty-state">
            No data available for this metric. Connect your devices and sync your data to see visualizations.
          </p>
        </div>
      ) : (
        <>
          {stats && (
            <div className="stats-section">
              <div className="stat-card card">
                <div className="stat-label">Average</div>
                <div className="stat-value">{stats.avg.toFixed(1)} <span className="stat-unit">{stats.unit}</span></div>
              </div>
              <div className="stat-card card">
                <div className="stat-label">Minimum</div>
                <div className="stat-value">{stats.min.toFixed(1)} <span className="stat-unit">{stats.unit}</span></div>
              </div>
              <div className="stat-card card">
                <div className="stat-label">Maximum</div>
                <div className="stat-value">{stats.max.toFixed(1)} <span className="stat-unit">{stats.unit}</span></div>
              </div>
              <div className="stat-card card">
                <div className="stat-label">Data Points</div>
                <div className="stat-value">{healthData.length}</div>
              </div>
            </div>
          )}

          <div className="chart-container card">
            <h3 className="chart-title">
              {selectedType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </h3>
            <div className="chart-wrapper">
              {chartData && <Line data={chartData} options={chartOptions} />}
            </div>
          </div>

          <div className="data-table card">
            <h3>Data Points</h3>
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Provider</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {healthData.slice(0, 50).map((item, index) => (
                    <tr key={index}>
                      <td>{new Date(item.date).toLocaleDateString()}</td>
                      <td>
                        <span className={`provider-badge provider-${item.provider}`}>
                          {item.provider}
                        </span>
                      </td>
                      <td>{item.value.toFixed(1)} {item.unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {healthData.length > 50 && (
              <p className="table-footer">Showing 50 of {healthData.length} data points</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default HealthData;

