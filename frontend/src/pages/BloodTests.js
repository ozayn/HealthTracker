import React, { useState, useEffect } from 'react';
import { apiFetch } from '../App';
import './BloodTests.css';

function BloodTests({ user }) {
  const [bloodTests, setBloodTests] = useState([]);
  const [selectedTest, setSelectedTest] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showAddMarker, setShowAddMarker] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const [formData, setFormData] = useState({
    test_date: new Date().toISOString().split('T')[0],
    lab_name: '',
    notes: ''
  });

  const [markerData, setMarkerData] = useState({
    marker_name: '',
    value: '',
    unit: '',
    reference_range_low: '',
    reference_range_high: '',
    notes: ''
  });

  useEffect(() => {
    if (user) {
      loadBloodTests();
    }
  }, [user]);

  const loadBloodTests = async () => {
    setLoading(true);
    try {
      const response = await apiFetch('/api/blood-tests');
      const data = await response.json();
      setBloodTests(data);
    } catch (error) {
      console.error('Error loading blood tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const form = new FormData();
    form.append('test_date', formData.test_date);
    form.append('lab_name', formData.lab_name);
    form.append('notes', formData.notes);
    
    const fileInput = document.getElementById('file-upload');
    if (fileInput && fileInput.files[0]) {
      form.append('file', fileInput.files[0]);
    }

    try {
      await apiFetch('/api/blood-tests', {
        method: 'POST',
        body: form
      });
      
      setShowAddForm(false);
      setFormData({
        test_date: new Date().toISOString().split('T')[0],
        lab_name: '',
        notes: ''
      });
      loadBloodTests();
    } catch (error) {
      console.error('Error creating blood test:', error);
      alert('Failed to create blood test');
    }
  };

  const handleAddMarker = async (e) => {
    e.preventDefault();
    
    if (!selectedTest) return;

    try {
      const response = await apiFetch(`/api/blood-tests/test/${selectedTest.id}/markers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...markerData,
          value: parseFloat(markerData.value),
          reference_range_low: markerData.reference_range_low ? parseFloat(markerData.reference_range_low) : null,
          reference_range_high: markerData.reference_range_high ? parseFloat(markerData.reference_range_high) : null
        })
      });

      if (response.ok) {
        setShowAddMarker(false);
        setMarkerData({
          marker_name: '',
          value: '',
          unit: '',
          reference_range_low: '',
          reference_range_high: '',
          notes: ''
        });
        
        // Refresh the selected test
        const testResponse = await apiFetch(`/api/blood-tests/test/${selectedTest.id}`);
        const updatedTest = await testResponse.json();
        setSelectedTest(updatedTest);
        loadBloodTests();
      }
    } catch (error) {
      console.error('Error adding marker:', error);
      alert('Failed to add marker');
    }
  };

  const handleDeleteTest = async (testId) => {
    if (!window.confirm('Are you sure you want to delete this blood test?')) {
      return;
    }

    try {
      await apiFetch(`/api/blood-tests/test/${testId}`, {
        method: 'DELETE'
      });
      
      if (selectedTest && selectedTest.id === testId) {
        setSelectedTest(null);
      }
      
      loadBloodTests();
    } catch (error) {
      console.error('Error deleting blood test:', error);
      alert('Failed to delete blood test');
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="blood-tests-page">
      <div className="page-header">
        <div>
          <h2>Blood Tests</h2>
          <p className="subtitle">Track your lab results over time</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAddForm(true)}>
          Add Blood Test
        </button>
      </div>

      <div className="blood-tests-layout">
        <div className="tests-list">
          {bloodTests.length === 0 ? (
            <div className="card">
              <p className="empty-state">No blood tests recorded yet</p>
            </div>
          ) : (
            bloodTests.map(test => (
              <div 
                key={test.id} 
                className={`test-card card ${selectedTest && selectedTest.id === test.id ? 'selected' : ''}`}
                onClick={() => setSelectedTest(test)}
              >
                <div className="test-date">
                  {new Date(test.test_date).toLocaleDateString('en-US', { 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </div>
                <div className="test-lab">{test.lab_name || 'Lab Test'}</div>
                <div className="test-markers-count">
                  {test.markers.length} marker{test.markers.length !== 1 ? 's' : ''}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="test-details">
          {selectedTest ? (
            <div className="card">
              <div className="card-header">
                <span>Test Details</span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    className="btn btn-secondary"
                    onClick={() => setShowAddMarker(true)}
                  >
                    Add Marker
                  </button>
                  <button 
                    className="btn btn-danger"
                    onClick={() => handleDeleteTest(selectedTest.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>

              <div className="test-info">
                <div className="info-row">
                  <span className="info-label">Date:</span>
                  <span>{new Date(selectedTest.test_date).toLocaleDateString()}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Lab:</span>
                  <span>{selectedTest.lab_name || 'Not specified'}</span>
                </div>
                {selectedTest.notes && (
                  <div className="info-row">
                    <span className="info-label">Notes:</span>
                    <span>{selectedTest.notes}</span>
                  </div>
                )}
              </div>

              <div className="markers-section">
                <h3>Markers</h3>
                {selectedTest.markers.length === 0 ? (
                  <p className="empty-state">No markers added yet</p>
                ) : (
                  <div className="markers-list">
                    {selectedTest.markers.map(marker => (
                      <div key={marker.id} className="marker-item">
                        <div className="marker-header">
                          <span className="marker-name">{marker.marker_name}</span>
                          {marker.is_abnormal && (
                            <span className="status-badge status-abnormal">Abnormal</span>
                          )}
                        </div>
                        <div className="marker-value">
                          {marker.value} {marker.unit}
                        </div>
                        {(marker.reference_range_low || marker.reference_range_high) && (
                          <div className="marker-range">
                            Range: {marker.reference_range_low || '?'} - {marker.reference_range_high || '?'} {marker.unit}
                          </div>
                        )}
                        {marker.notes && (
                          <div className="marker-notes">{marker.notes}</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card">
              <p className="empty-state">Select a blood test to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Blood Test Modal */}
      {showAddForm && (
        <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Add Blood Test</h3>
            <form onSubmit={handleSubmit}>
              <div className="input-group">
                <label className="input-label">Test Date</label>
                <input
                  type="date"
                  className="input-field"
                  value={formData.test_date}
                  onChange={(e) => setFormData({...formData, test_date: e.target.value})}
                  required
                />
              </div>

              <div className="input-group">
                <label className="input-label">Lab Name</label>
                <input
                  type="text"
                  className="input-field"
                  value={formData.lab_name}
                  onChange={(e) => setFormData({...formData, lab_name: e.target.value})}
                  placeholder="e.g., Quest Diagnostics"
                />
              </div>

              <div className="input-group">
                <label className="input-label">Notes</label>
                <textarea
                  className="input-field"
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  placeholder="Any additional notes..."
                  rows="3"
                />
              </div>

              <div className="input-group">
                <label className="input-label">Upload File (optional)</label>
                <input
                  type="file"
                  id="file-upload"
                  className="input-field"
                  accept=".pdf,.png,.jpg,.jpeg,.csv"
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddForm(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Marker Modal */}
      {showAddMarker && (
        <div className="modal-overlay" onClick={() => setShowAddMarker(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Add Marker</h3>
            <form onSubmit={handleAddMarker}>
              <div className="input-group">
                <label className="input-label">Marker Name</label>
                <input
                  type="text"
                  className="input-field"
                  value={markerData.marker_name}
                  onChange={(e) => setMarkerData({...markerData, marker_name: e.target.value})}
                  placeholder="e.g., Cholesterol, Vitamin D"
                  required
                />
              </div>

              <div className="input-group">
                <label className="input-label">Value</label>
                <input
                  type="number"
                  step="any"
                  className="input-field"
                  value={markerData.value}
                  onChange={(e) => setMarkerData({...markerData, value: e.target.value})}
                  required
                />
              </div>

              <div className="input-group">
                <label className="input-label">Unit</label>
                <input
                  type="text"
                  className="input-field"
                  value={markerData.unit}
                  onChange={(e) => setMarkerData({...markerData, unit: e.target.value})}
                  placeholder="e.g., mg/dL, ng/mL"
                />
              </div>

              <div className="input-row">
                <div className="input-group">
                  <label className="input-label">Range Low</label>
                  <input
                    type="number"
                    step="any"
                    className="input-field"
                    value={markerData.reference_range_low}
                    onChange={(e) => setMarkerData({...markerData, reference_range_low: e.target.value})}
                  />
                </div>

                <div className="input-group">
                  <label className="input-label">Range High</label>
                  <input
                    type="number"
                    step="any"
                    className="input-field"
                    value={markerData.reference_range_high}
                    onChange={(e) => setMarkerData({...markerData, reference_range_high: e.target.value})}
                  />
                </div>
              </div>

              <div className="input-group">
                <label className="input-label">Notes</label>
                <textarea
                  className="input-field"
                  value={markerData.notes}
                  onChange={(e) => setMarkerData({...markerData, notes: e.target.value})}
                  rows="2"
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAddMarker(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Add Marker
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default BloodTests;

