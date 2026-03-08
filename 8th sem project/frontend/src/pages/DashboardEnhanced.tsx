import React, { useEffect, useState, useCallback } from 'react';
import StatCard from '../components/StatCard';
import Charts from '../components/Charts';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { SystemStats, Anomaly } from '../types';
import toast from 'react-hot-toast';

type DetectionMode = 'live' | 'simulation';
type SimulatedEndpoint = '/sim/login' | '/sim/search' | '/sim/profile' | '/sim/payment' | '/sim/signup';

const DashboardEnhanced: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const { anomalies: wsAnomalies, connected } = useWebSocket();
  
  // Mode state
  const [detectionMode, setDetectionMode] = useState<DetectionMode>('live');
  const [simulatedEndpoint, setSimulatedEndpoint] = useState<SimulatedEndpoint>('/sim/login');
  const [simulationActive, setSimulationActive] = useState(false);
  const [simulationStats, setSimulationStats] = useState<any>(null);
  
  // ML status
  const [mlStatus, setMlStatus] = useState<any>(null);

  const loadData = useCallback(async () => {
    try {
      if (detectionMode === 'live') {
        // Load LIVE mode data
        const [statsData, anomaliesData] = await Promise.all([
          apiService.getStats(),
          apiService.getAnomalies(200),
        ]);
        
        setStats(statsData);
        setAnomalies(anomaliesData);
      } else {
        // Load SIMULATION mode data
        const [simStats, simAnomalies] = await Promise.all([
          apiService.getSimulationStats(),
          apiService.getSimulationAnomalies(200),
        ]);
        
        setSimulationStats(simStats);
        setSimulationActive(simStats.active);
        setAnomalies(simAnomalies);
        
        // Convert simulation stats to SystemStats format for display
        setStats({
          mode: 'SIMULATION',
          total_api_calls: simStats.total_requests || 0,
          total_anomalies: simStats.anomalies_detected || 0,
          high_priority: 0,
          medium_priority: 0,
          low_priority: 0,
          avg_response_time: simStats.avg_response_time || 0,
          error_rate: (simStats.error_rate || 0) * 100, // Convert to percentage
          system_health: simStats.active ? 'running' : 'idle'
        });
      }
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  }, [detectionMode]);

  useEffect(() => {
    loadData();
  }, [detectionMode]);

  useEffect(() => {
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);
  
  // Load ML status
  useEffect(() => {
    const loadMLStatus = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/ml/status');
        if (response.ok) {
          const data = await response.json();
          setMlStatus(data);
        }
      } catch (error) {
        console.error('Error loading ML status:', error);
      }
    };
    
    loadMLStatus();
    const interval = setInterval(loadMLStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (wsAnomalies.length > 0) {
      const latestAnomaly = wsAnomalies[0];
      
      if (latestAnomaly.risk_score >= 0.8) {
        toast.error(
          `🚨 HIGH RISK: ${latestAnomaly.endpoint} (Risk: ${latestAnomaly.risk_score.toFixed(3)})`,
          { duration: 5000 }
        );
      }
      
      setAnomalies(prev => {
        const newAnomalies = [...wsAnomalies, ...prev];
        const uniqueAnomalies = Array.from(
          new Map(newAnomalies.map(a => [a.id, a])).values()
        );
        return uniqueAnomalies.slice(0, 100);
      });
    }
  }, [wsAnomalies]);

  const handleStartSimulation = async () => {
    if (!simulatedEndpoint) {
      toast.error('Please select an endpoint');
      return;
    }
    
    try {
      // Clear old simulation data first
      await apiService.clearSimulationData();
      toast.success('Cleared old simulation data');
      
      // Start new simulation
      await apiService.startSimulation(simulatedEndpoint, 60);
      setSimulationActive(true);
      toast.success(`Simulation started: ${simulatedEndpoint}`);
      
      // Force immediate refresh to show empty state
      await loadData();
      
      // Start polling for updates
      const pollInterval = setInterval(async () => {
        try {
          const simStats = await apiService.getSimulationStats();
          setSimulationStats(simStats);
          setSimulationActive(simStats.active);
          
          // Update stats display
          setStats({
            mode: 'SIMULATION',
            total_api_calls: simStats.total_requests || 0,
            total_anomalies: simStats.anomalies_detected || 0,
            high_priority: 0,
            medium_priority: 0,
            low_priority: 0,
            avg_response_time: simStats.avg_response_time || 0,
            error_rate: (simStats.error_rate || 0) * 100,
            system_health: simStats.active ? 'running' : 'idle'
          });
          
          // Reload anomalies
          const simAnomalies = await apiService.getSimulationAnomalies(200);
          setAnomalies(simAnomalies);
          
          if (!simStats.active) {
            clearInterval(pollInterval);
            toast.success('Simulation completed');
            // Force refresh after completion
            setTimeout(() => loadData(), 1000);
          }
        } catch (error) {
          console.error('Error polling simulation stats:', error);
        }
      }, 2000);
    } catch (error: any) {
      console.error('Error starting simulation:', error);
      toast.error(`Failed to start: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleStopSimulation = async () => {
    if (!simulationActive) {
      toast.error('No simulation is running');
      return;
    }
    
    try {
      await apiService.stopSimulation();
      setSimulationActive(false);
      toast.success('Simulation stopped');
      setTimeout(() => loadData(), 1000); // Refresh after delay
    } catch (error: any) {
      console.error('Error stopping simulation:', error);
      if (error.response?.status === 400) {
        toast.error('No simulation is running');
        setSimulationActive(false);
      } else {
        toast.error(`Failed to stop: ${error.response?.data?.detail || error.message}`);
      }
    }
  };

  const testEndpoint = async (endpoint: string, method: string = 'GET') => {
    try {
      const options: RequestInit = {
        method,
        headers: method === 'POST' ? { 'Content-Type': 'application/json' } : {}
      };

      if (method === 'POST') {
        let body = {};
        if (endpoint === '/login' || endpoint === '/logout') {
          body = { username: `testuser_${Date.now()}`, password: 'testpass' };
        } else if (endpoint === '/payment') {
          body = { 
            user_id: `testuser_${Date.now()}`, 
            amount: Math.floor(Math.random() * 1000) + 1, 
            currency: 'USD',
            card_number: '4111111111111111'
          };
        } else if (endpoint === '/signup') {
          body = { 
            username: `testuser_${Date.now()}`, 
            email: `test_${Date.now()}@example.com`, 
            password: 'testpass' 
          };
        }
        options.body = JSON.stringify(body);
      }

      const response = await fetch(`http://localhost:8000${endpoint}`, options);
      
      if (response.ok) {
        toast.success(`${method} ${endpoint} - Status: ${response.status}`);
      } else {
        toast.error(`${method} ${endpoint} - Status: ${response.status}`);
      }
      
      // Wait a bit for backend to process, then refresh
      await new Promise(resolve => setTimeout(resolve, 300));
      await loadData();
      
      // Trigger detection every 10 requests
      if (stats && stats.total_api_calls % 10 === 9) {
        try {
          await apiService.triggerDetection();
          console.log('Anomaly detection triggered automatically');
          await new Promise(resolve => setTimeout(resolve, 300));
          await loadData();
        } catch (error) {
          console.error('Error triggering detection:', error);
        }
      }
    } catch (error) {
      console.error(`Error testing ${endpoint}:`, error);
      toast.error(`Failed to test ${endpoint}`);
    }
  };

  const getModeStats = () => {
    if (detectionMode === 'simulation' && simulationStats) {
      return {
        total_requests: simulationStats.total_requests || 0,
        windows_processed: simulationStats.windows_processed || 0,
        anomalies_detected: simulationStats.anomalies_detected || 0,
        current_window_count: simulationStats.current_window_count || 0,
        window_size: simulationStats.window_size || 10
      };
    } else if (detectionMode === 'live' && stats) {
      return {
        total_requests: stats.total_api_calls || stats.request_count || 0,
        windows_processed: stats.windows_processed || 0,
        anomalies_detected: stats.anomalies_detected || 0,
        current_window_count: (stats.total_api_calls || 0) % 10,
        window_size: 10
      };
    }
    return {
      total_requests: 0,
      windows_processed: 0,
      anomalies_detected: 0,
      current_window_count: 0,
      window_size: 10
    };
  };
if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-dark-muted">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  
  const modeStats = getModeStats();

  return (
    <div className="p-6 space-y-6">
      {/* Header with Mode Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-text">Dashboard Overview</h1>
          <p className="text-dark-muted mt-1">
            {detectionMode === 'live' 
              ? 'Real-time API monitoring with sliding window detection' 
              : 'Simulated traffic with anomaly injection'}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {/* WebSocket Status */}
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${connected ? 'bg-success-500' : 'bg-danger-500'} animate-pulse`} />
            <span className="text-sm text-dark-muted">
              {connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          
          {/* ML Status */}
          {mlStatus && mlStatus.available && (
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-info-500 animate-pulse" />
              <span className="text-sm text-dark-muted">
                ML Active
              </span>
            </div>
          )}
          
          {/* Mode Toggle */}
          <div className="flex items-center space-x-2 bg-dark-700 rounded-lg p-1">
            <button
              onClick={() => setDetectionMode('live')}
              className={`px-4 py-2 rounded-md font-medium transition-all ${
                detectionMode === 'live'
                  ? 'bg-primary-600 text-white'
                  : 'text-dark-muted hover:text-white'
              }`}
            >
              🎯 LIVE MODE
            </button>
            <button
              onClick={() => setDetectionMode('simulation')}
              className={`px-4 py-2 rounded-md font-medium transition-all ${
                detectionMode === 'simulation'
                  ? 'bg-warning-600 text-white'
                  : 'text-dark-muted hover:text-white'
              }`}
            >
              🎬 SIMULATION
            </button>
          </div>
        </div>
      </div>

      {/* Simulation Controls */}
      {detectionMode === 'simulation' && (
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
          <h2 className="text-xl font-bold text-white mb-4">🎬 Auto-Detection Simulation</h2>
          <p className="text-sm text-dark-muted mb-4">
            Select a virtual endpoint. ML models will automatically detect anomaly types from traffic patterns.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-muted mb-2">
                Virtual Endpoint
              </label>
              <select
                value={simulatedEndpoint}
                onChange={(e) => setSimulatedEndpoint(e.target.value as SimulatedEndpoint)}
                disabled={simulationActive}
                className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                style={{ 
                  color: 'white',
                  backgroundColor: '#1f2937'
                }}
              >
                <option value="/sim/login" style={{ color: 'white', backgroundColor: '#1f2937' }}>🔐 /sim/login (ERROR_SPIKE)</option>
                <option value="/sim/search" style={{ color: 'white', backgroundColor: '#1f2937' }}>🔍 /sim/search (TRAFFIC_BURST)</option>
                <option value="/sim/profile" style={{ color: 'white', backgroundColor: '#1f2937' }}>👤 /sim/profile (TIMEOUT)</option>
                <option value="/sim/payment" style={{ color: 'white', backgroundColor: '#1f2937' }}>💳 /sim/payment (LATENCY_SPIKE)</option>
                <option value="/sim/signup" style={{ color: 'white', backgroundColor: '#1f2937' }}>📝 /sim/signup (RESOURCE_EXHAUSTION)</option>
              </select>
            </div>
            
            <div className="flex items-end">
              {!simulationActive ? (
                <button
                  onClick={handleStartSimulation}
                  disabled={!simulatedEndpoint}
                  className="w-full px-6 py-2 bg-success-600 hover:bg-success-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  ▶️ Start Auto-Detection
                </button>
              ) : (
                <button
                  onClick={handleStopSimulation}
                  className="w-full px-6 py-2 bg-danger-600 hover:bg-danger-700 text-white font-medium rounded-lg transition-colors"
                >
                  ⏹️ Stop Simulation
                </button>
              )}
            </div>
            
            <div className="flex items-end">
              <div className={`w-full px-4 py-2 rounded-lg ${simulationActive ? 'bg-success-900/30 border-success-500' : 'bg-dark-700 border-dark-600'} border`}>
                <div className="text-sm text-dark-muted">Status</div>
                <div className={`text-lg font-bold ${simulationActive ? 'text-success-500' : 'text-dark-muted'}`}>
                  {simulationActive ? '● RUNNING' : '○ STOPPED'}
                </div>
              </div>
            </div>
          </div>
          
          {simulationStats && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-dark-700 rounded-lg p-3">
                <div className="text-xs text-dark-muted">Endpoint</div>
                <div className="text-sm font-bold text-warning-400">{simulationStats.simulated_endpoint}</div>
              </div>
              <div className="bg-dark-700 rounded-lg p-3">
                <div className="text-xs text-dark-muted">Detected Types</div>
                <div className="text-sm font-bold text-danger-400">
                  {simulationStats.detected_anomaly_types?.length || 0} types
                </div>
              </div>
              <div className="bg-dark-700 rounded-lg p-3">
                <div className="text-xs text-dark-muted">Episodes</div>
                <div className="text-sm font-bold text-primary-400">{simulationStats.anomalies_detected}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          title={detectionMode === 'live' ? 'Live Requests' : 'Simulated Requests'}
          value={modeStats.total_requests.toLocaleString()}
          subtitle={`${modeStats.current_window_count}/${modeStats.window_size} in current window`}
          color="blue"
          icon={detectionMode === 'live' ? '🎯' : '🎬'}
        />
        
        <StatCard
          title="Windows Processed"
          value={modeStats.windows_processed.toLocaleString()}
          subtitle="10 requests per window"
          color="purple"
          icon="📊"
        />
        
        <StatCard
          title="Anomalies Detected"
          value={modeStats.anomalies_detected.toLocaleString()}
          subtitle={`${modeStats.windows_processed > 0 ? ((modeStats.anomalies_detected / modeStats.windows_processed) * 100).toFixed(1) : 0}% detection rate`}
          color="red"
          icon="⚠️"
        />
        
        <StatCard
          title="Avg Response Time"
          value={`${stats?.avg_response_time?.toFixed(0) || 0}ms`}
          subtitle="Current window average"
          color="green"
          icon="⚡"
        />
        
        <StatCard
          title="Error Rate"
          value={`${stats?.error_rate?.toFixed(1) || 0}%`}
          subtitle="4xx/5xx errors"
          color={stats?.error_rate && stats.error_rate > 50 ? 'red' : 'yellow'}
          icon={stats?.error_rate && stats.error_rate > 50 ? '🚨' : '⚡'}
        />
      </div>

      {/* Mode Information */}
      <div className="bg-dark-800 rounded-lg p-4 border border-dark-600">
        <div className="flex items-start space-x-3">
          <div className="text-2xl">
            {detectionMode === 'live' ? '🎯' : '🎬'}
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white mb-1">
              {detectionMode === 'live' ? 'LIVE MODE Active' : 'SIMULATION MODE Active'}
            </h3>
            <p className="text-sm text-dark-muted">
              {detectionMode === 'live' 
                ? '✓ Monitoring real API endpoints (login, payment, search, profile)'
                : `✓ Auto-detection simulation on ${simulatedEndpoint} endpoint - ML models determine anomaly types`}
            </p>
            <p className="text-sm text-dark-muted mt-1">
              ✓ Sliding window: 10 requests → ML inference → Hybrid detection (Rules + 4 ML models)
            </p>
            <p className="text-sm text-dark-muted mt-1">
              ✓ Features: request_rate, unique_endpoints, method_ratio, payload_size, error_rate, param_repetition, user_agent_entropy, latency
            </p>
          </div>
        </div>
      </div>

      {/* Live Mode Testing Panel */}
      {detectionMode === 'live' && (
        <>
          <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h2 className="text-xl font-bold text-white">
                  🧪 Test Whitelisted Endpoints
                </h2>
                <p className="text-sm text-dark-muted mt-1">
                  Click any button to send a test request. Only these 6 endpoints are tracked in LIVE mode.
                </p>
              </div>
              <button
                onClick={async () => {
                  try {
                    const result = await apiService.triggerDetection();
                    if (result.anomaly_detected) {
                      toast.success(`Anomaly detected: ${result.anomaly_type}`);
                    } else {
                      toast.success('No anomalies detected in current window');
                    }
                    loadData();
                  } catch (error) {
                    toast.error('Failed to trigger detection');
                  }
                }}
                className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
              >
                🔍 Trigger Detection
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <button
                onClick={() => testEndpoint('/login', 'POST')}
                className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                🔐 Login
              </button>
              <button
                onClick={() => testEndpoint('/signup', 'POST')}
                className="px-4 py-3 bg-green-600 hover:bg-green-700 text-white font-medium rounded-lg transition-colors"
              >
                ✍️ Signup
              </button>
              <button
                onClick={() => testEndpoint('/search?query=test', 'GET')}
                className="px-4 py-3 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition-colors"
              >
                🔍 Search
              </button>
              <button
                onClick={() => testEndpoint('/profile?user_id=test', 'GET')}
                className="px-4 py-3 bg-yellow-600 hover:bg-yellow-700 text-white font-medium rounded-lg transition-colors"
              >
                👤 Profile
              </button>
              <button
                onClick={() => testEndpoint('/payment', 'POST')}
                className="px-4 py-3 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
              >
                💳 Payment
              </button>
              <button
                onClick={() => testEndpoint('/logout', 'POST')}
                className="px-4 py-3 bg-gray-600 hover:bg-gray-700 text-white font-medium rounded-lg transition-colors"
              >
                🚪 Logout
              </button>
            </div>
          </div>
        </>
      )}

      {/* Per-Endpoint Breakdown (LIVE mode only) */}
      {detectionMode === 'live' && stats?.endpoint_counts && (
        <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
          <h2 className="text-xl font-bold text-white mb-4">
            📊 Per-Endpoint Request Breakdown (Whitelisted Only)
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {Object.entries(stats.endpoint_counts).map(([endpoint, count]) => (
              <div key={endpoint} className="bg-dark-700 rounded-lg p-4 border border-dark-600">
                <div className="text-sm text-dark-muted mb-1">{endpoint}</div>
                <div className="text-2xl font-bold text-white">{count.toLocaleString()}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-dark-muted mt-4">
            ℹ️ Only whitelisted endpoints are tracked: /login, /signup, /search, /profile, /payment, /logout
          </p>
        </div>
      )}

      {/* Analytics Charts - Bottom Section */}
      {anomalies.length > 0 && (
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-white mb-6">📊 Anomaly Analytics</h2>
          <Charts anomalies={anomalies} />
        </div>
      )}
    </div>
  );
};

export default DashboardEnhanced;
