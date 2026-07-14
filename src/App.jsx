import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [stats, setStats] = useState({
    vehicles: 0,
    ambulance: false,
    lastUpdate: null,
    camera_status: 'disconnected'
  });
  const [fullscreen, setFullscreen] = useState(false);

  // Check stream connection status
  useEffect(() => {
    const checkConnection = () => {
      const img = new Image();
      img.onload = () => setIsConnected(true);
      img.onerror = () => setIsConnected(false);
      img.src = `http://localhost:5000/video_feed?t=${Date.now()}`;
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, []);

  // Fetch real-time data from Firebase
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('https://v2v-communication-d46c6-default-rtdb.firebaseio.com/traffic.json');
        if (response.ok) {
          const data = await response.json();
          if (data) {
            setStats(prev => ({
              vehicles: data.vehicle_count || 0,
              ambulance: data.ambulance === 1,
              camera_status: data.camera_status || 'disconnected',
              lastUpdate: new Date().toLocaleTimeString()
            }));
          }
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };

    // Initial fetch
    fetchStats();

    // Poll every 2 seconds for real-time updates
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  const toggleFullscreen = () => {
    setFullscreen(!fullscreen);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <h1 className="title">
            <span className="title-icon">🚨</span>
            Live Vehicle Detection System
            <span className="title-badge">AI-Powered</span>
          </h1>
          <div className="connection-status">
            <div className={`status-indicator ${isConnected && stats.camera_status === 'connected' ? 'connected' : 'disconnected'}`}>
              <div className="pulse"></div>
            </div>
            <span className="status-text">
              {isConnected && stats.camera_status === 'connected' ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Stats Dashboard */}
      <div className="stats-container">
        <div className="stat-card">
          <div className="stat-icon">🚗</div>
          <div className="stat-content">
            <div className="stat-value">{stats.vehicles}</div>
            <div className="stat-label">Vehicles Detected</div>
          </div>
        </div>

        <div className={`stat-card ${stats.ambulance ? 'emergency' : ''}`}>
          <div className="stat-icon">🚑</div>
          <div className="stat-content">
            <div className="stat-value">{stats.ambulance ? 'ACTIVE' : 'CLEAR'}</div>
            <div className="stat-label">Emergency Vehicle</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏰</div>
          <div className="stat-content">
            <div className="stat-value">{stats.lastUpdate || '--:--:--'}</div>
            <div className="stat-label">Last Update</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📹</div>
          <div className="stat-content">
            <div className="stat-value">{stats.camera_status.toUpperCase()}</div>
            <div className="stat-label">Camera Status</div>
          </div>
        </div>
      </div>

      {/* Video Stream Container */}
      <div className={`video-container ${fullscreen ? 'fullscreen' : ''}`}>
        <div className="video-wrapper">
          {stats.ambulance && (
            <div className="emergency-overlay">
              <div className="emergency-text">EMERGENCY VEHICLE DETECTED</div>
            </div>
          )}

          <img
            src="http://localhost:5000/video_feed"
            alt="Live Vehicle Detection Stream"
            className="video-stream"
            onLoad={() => setIsConnected(true)}
            onError={() => setIsConnected(false)}
          />

          <div className="video-controls">
            <button className="control-btn" onClick={toggleFullscreen} title="Toggle Fullscreen">
              {fullscreen ? '🔲' : '⛶'}
            </button>
          </div>

          {/* Live indicators */}
          <div className="live-indicators">
            <div className="live-badge">
              <div className="live-dot"></div>
              LIVE
            </div>
            <div className="resolution-badge">HD</div>
            {stats.vehicles > 0 && (
              <div className="vehicle-count-badge">
                🚗 {stats.vehicles}
              </div>
            )}
          </div>
        </div>

        {/* Data refresh indicator
        <div className="refresh-indicator">
          <div className="refresh-dot"></div>
          <span>Real-time data</span>
        </div> */}
      </div>

      {/* Footer Info */}
      {/* <footer className="footer">
        <div className="footer-content">
          <div className="system-info">
            <span>🎯 AI Detection System</span>
            <span>📡 Real-time Processing</span>
            <span>🛡️ Traffic Management</span>
            <span>🔥 Firebase Integration</span>
          </div>
          <div className="tech-stack">
            <span className="tech-badge">YOLO</span>
            <span className="tech-badge">OpenCV</span>
            <span className="tech-badge">Flask</span>
            <span className="tech-badge">React</span>
            <span className="tech-badge">Firebase</span>
          </div>
        </div>
      </footer> */}
    </div>
  );
}

export default App;