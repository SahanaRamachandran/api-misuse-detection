import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import toast from 'react-hot-toast';
import {
  RiskScoreTimeline,
  AnomaliesByEndpoint,
  AnomalyTypeDistribution,
  SeverityDistribution,
  TopAffectedEndpoints,
  ResolutionSuggestions,
} from '../components/VisualizationGraphs';

const TIME_RANGES = [
  { label: '1 Hour', hours: 1 },
  { label: '6 Hours', hours: 6 },
  { label: '24 Hours', hours: 24 },
  { label: '7 Days', hours: 168 },
];

const ComprehensiveDashboard: React.FC = () => {
  const [simulationActive, setSimulationActive] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedHours, setSelectedHours] = useState(24);
  const { connected } = useWebSocket();

  const handleStartEnhancedSimulation = async () => {
    setLoading(true);
    try {
      const response = await apiService.startEnhancedSimulation(60, 200);
      toast.success(`🚀 Enhanced Simulation Started! Target: 200 RPS`);
      setSimulationActive(true);
      
      // Poll for stats
      const interval = setInterval(async () => {
        try {
          const stats = await apiService.getEnhancedSimulationStats();
          setStats(stats);
          
          if (!stats.active) {
            clearInterval(interval);
            setSimulationActive(false);
            toast.success('✅ Simulation Completed!');
          }
        } catch (error) {
          console.error('Error polling stats:', error);
        }
      }, 2000);
    } catch (error: any) {
      toast.error(`Failed to start: ${error.message}`);
      setSimulationActive(false);
    } finally {
      setLoading(false);
    }
  };

  const handleStopEnhancedSimulation = async () => {
    try {
      await apiService.stopEnhancedSimulation();
      toast.success('Simulation Stopped');
      setSimulationActive(false);
    } catch (error: any) {
      toast.error(`Failed to stop: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🎯 Comprehensive Analytics Dashboard
              </h1>
              <p className="text-gray-600 mt-2">
                Real-time anomaly detection, visualization, and resolution suggestions
              </p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {connected ? 'Live Connected' : 'Disconnected'}
                </span>
              </div>
              {/* Time Range Selector */}
              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                {TIME_RANGES.map((range) => (
                  <button
                    key={range.hours}
                    onClick={() => setSelectedHours(range.hours)}
                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                      selectedHours === range.hours
                        ? 'bg-purple-600 text-white shadow'
                        : 'text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
              {!simulationActive ? (
                <button
                  onClick={handleStartEnhancedSimulation}
                  disabled={loading}
                  className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 font-semibold transition-colors"
                >
                  {loading ? '🔄 Starting...' : '🚀 Start Enhanced Simulation (200+ RPS)'}
                </button>
              ) : (
                <button
                  onClick={handleStopEnhancedSimulation}
                  className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold transition-colors"
                >
                  ⏹️ Stop Simulation
                </button>
              )}
            </div>
          </div>

          {/* Stats Display */}
          {stats && simulationActive && (
            <div className="mt-6 grid grid-cols-5 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Total Requests</div>
                <div className="text-2xl font-bold text-blue-600">{stats.total_requests || 0}</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Current RPS</div>
                <div className="text-2xl font-bold text-green-600">{stats.rps?.toFixed(1) || 0}</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Anomalies Detected</div>
                <div className="text-2xl font-bold text-purple-600">{stats.anomalies_detected || 0}</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Anomalies Injected</div>
                <div className="text-2xl font-bold text-orange-600">{stats.anomalies_injected || 0}</div>
              </div>
              <div className="bg-pink-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600">Detection Rate</div>
                <div className="text-2xl font-bold text-pink-600">
                  {stats.anomalies_injected > 0 
                    ? ((stats.anomalies_detected / stats.anomalies_injected) * 100).toFixed(1) 
                    : 0}%
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Visualizations Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <RiskScoreTimeline hours={selectedHours} />
        <AnomaliesByEndpoint hours={selectedHours} />
        <AnomalyTypeDistribution hours={selectedHours} />
        <SeverityDistribution hours={selectedHours} />
      </div>

      {/* Top Affected Endpoints */}
      <div className="mb-6">
        <TopAffectedEndpoints hours={selectedHours} />
      </div>

      {/* Resolution Suggestions */}
      <div className="mb-6">
        <ResolutionSuggestions hours={selectedHours} />
      </div>

      {/* Endpoint Statistics */}
      {stats && stats.by_endpoint && (
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Endpoint Statistics (Current Simulation)</h3>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(stats.by_endpoint).map(([endpoint, endpointStats]: [string, any]) => (
              <div key={endpoint} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <div className="font-semibold text-gray-900 mb-2">{endpoint}</div>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Requests:</span>
                    <span className="font-medium">{endpointStats.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Anomalies:</span>
                    <span className="font-medium text-red-600">{endpointStats.anomalies}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Rate:</span>
                    <span className="font-medium">
                      {endpointStats.total > 0 
                        ? ((endpointStats.anomalies / endpointStats.total) * 100).toFixed(1) 
                        : 0}%
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature Info */}
      <div className="mt-6 bg-gradient-to-r from-purple-50 to-blue-50 p-6 rounded-lg border border-purple-200">
        <h3 className="text-lg font-bold text-purple-900 mb-3">✨ Dashboard Features</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="font-semibold text-purple-800">📊 Real-Time Graphs</div>
            <div className="text-purple-700">Live risk score timeline</div>
          </div>
          <div>
            <div className="font-semibold text-purple-800">🎯 Endpoint Analysis</div>
            <div className="text-purple-700">Anomalies per endpoint</div>
          </div>
          <div>
            <div className="font-semibold text-purple-800">🔍 Type Distribution</div>
            <div className="text-purple-700">Anomaly type breakdown</div>
          </div>
          <div>
            <div className="font-semibold text-purple-800">💡 Smart Suggestions</div>
            <div className="text-purple-700">Actionable resolutions</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveDashboard;
