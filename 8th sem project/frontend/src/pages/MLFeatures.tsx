import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

type DetectionMode = 'live' | 'simulation' | 'all';

interface MLStatus {
  available: boolean;
  features: {
    ensemble_scoring: boolean;
    ip_risk_tracking: boolean;
    shap_explainability: boolean;
    drift_detection: boolean;
  };
}

interface EnhancedDetectionStatus {
  available: boolean;
  enabled: boolean;
  sensitivity_mode: string;
  stats: {
    weak_signals_detected: number;
    adversarial_detected: number;
    total_enhanced_detections: number;
    detections_missed_by_basic: number;
  };
}

interface EnhancedDetectionPerformance {
  total_anomalies_detected: number;
  enhanced_detector_contributions: number;
  missed_by_basic_detector: number;
  improvement_percentage: number;
  weak_signals_caught: number;
  adversarial_attacks_detected: number;
  total_improved_detections: number;
  detection_breakdown: {
    weak_signals: number;
    adversarial_attacks: number;
    standard_anomalies: number;
  };
  estimated_detection_rates: {
    weak_signals: string;
    adversarial_attacks: string;
    obvious_attacks: string;
  };
}

interface IPRiskData {
  ip_address: string;
  risk_score: number;
  anomaly_count: number;
  total_requests: number;
  anomaly_rate: number;
  flagged: boolean;
}

interface IPRiskStats {
  total_ips: number;
  risk_distribution: {
    low: number;
    medium: number;
    high: number;
  };
  risk_score_stats: {
    mean: number;
    median: number;
    std: number;
    min: number;
    max: number;
  };
  flagged_ips: number;
}

interface MLPrediction {
  id: number;
  timestamp: string;
  endpoint: string;
  anomaly_type: string;
  severity: string;
  stored_risk_score: number;
  ml_predictions: {
    random_forest: number;
    isolation_forest: number;
    heuristic: number;
    ensemble: number;
    risk_level: string;
  };
}

const MLFeatures: React.FC = () => {
  const [detectionMode, setDetectionMode] = useState<DetectionMode>('all');
  const [mlStatus, setMLStatus] = useState<MLStatus | null>(null);
  const [enhancedStatus, setEnhancedStatus] = useState<EnhancedDetectionStatus | null>(null);
  const [enhancedPerformance, setEnhancedPerformance] = useState<EnhancedDetectionPerformance | null>(null);
  const [highRiskIPs, setHighRiskIPs] = useState<IPRiskData[]>([]);
  const [ipStats, setIPStats] = useState<IPRiskStats | null>(null);
  const [recentPredictions, setRecentPredictions] = useState<MLPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMLData();
    const interval = setInterval(fetchMLData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [detectionMode]); // Re-fetch when mode changes

  const fetchMLData = async () => {
    try {
      // Fetch ML status
      const statusRes = await axios.get(`${API_BASE}/api/ml/status`);
      setMLStatus(statusRes.data);

      // Fetch enhanced detection status
      try {
        const enhancedStatusRes = await axios.get(`${API_BASE}/api/ml/enhanced-detection/status`);
        setEnhancedStatus(enhancedStatusRes.data);
      } catch (enhErr) {
        console.error('Failed to fetch enhanced detection status:', enhErr);
      }

      // Fetch enhanced detection performance
      try {
        const enhancedPerfRes = await axios.get(`${API_BASE}/api/ml/enhanced-detection/performance`);
        setEnhancedPerformance(enhancedPerfRes.data);
      } catch (enhPerfErr) {
        console.error('Failed to fetch enhanced detection performance:', enhPerfErr);
      }

      // Fetch high-risk IPs with mode filter
      const highRiskRes = await axios.get(`${API_BASE}/api/ml/ip-risk/high-risk?mode=${detectionMode}`);
      setHighRiskIPs(highRiskRes.data.ips || []);

      // Fetch IP statistics with mode filter
      const statsRes = await axios.get(`${API_BASE}/api/ml/ip-risk/stats?mode=${detectionMode}`);
      // Only set stats if it's not a message response
      if (!statsRes.data.message) {
        setIPStats(statsRes.data);
      } else {
        setIPStats(null);
      }

      // Fetch recent ML predictions with mode filter
      try {
        const predictionsRes = await axios.get(`${API_BASE}/api/ml/recent-predictions?limit=5&mode=${detectionMode}`);
        setRecentPredictions(predictionsRes.data.predictions || []);
      } catch (predErr) {
        console.error('Failed to fetch predictions:', predErr);
        setRecentPredictions([]);
      }

      setLoading(false);
      setError(null);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  const changeSensitivity = async (mode: 'high' | 'balanced' | 'conservative') => {
    try {
      await axios.post(`${API_BASE}/api/ml/enhanced-detection/sensitivity`, { mode });
      // Refresh data to see the updated sensitivity
      await fetchMLData();
    } catch (err) {
      console.error('Failed to change sensitivity:', err);
    }
  };

  const getRiskColor = (score: number): string => {
    if (score >= 70) return 'text-red-400';
    if (score >= 30) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getRiskBadge = (score: number): string => {
    if (score >= 70) return 'bg-red-500/20 text-red-400';
    if (score >= 30) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-green-500/20 text-green-400';
  };

  // Backend now handles filtering, so we can simplify these functions
  const getFilteredHighRiskIPs = (): IPRiskData[] => {
    return highRiskIPs;
  };

  const calculateFilteredStats = (): IPRiskStats | null => {
    return ipStats;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-dark-muted">Loading ML Features...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-red-400">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h1 className="text-2xl font-bold text-dark-text mb-2">
          🤖 Advanced ML Features
        </h1>
        <p className="text-dark-muted">
          Real-time threat intelligence powered by machine learning
        </p>
      </div>

      {/* Mode Toggle */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h2 className="text-xl font-semibold text-dark-text mb-4">
          🎯 Detection Mode
        </h2>
        <div className="flex gap-4">
          <button
            onClick={() => setDetectionMode('all')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              detectionMode === 'all'
                ? 'bg-info-600 text-white shadow-lg scale-105'
                : 'bg-dark-bg text-dark-muted hover:bg-dark-border'
            }`}
          >
            🌐 All Data
          </button>
          <button
            onClick={() => setDetectionMode('live')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              detectionMode === 'live'
                ? 'bg-success-600 text-white shadow-lg scale-105'
                : 'bg-dark-bg text-dark-muted hover:bg-dark-border'
            }`}
          >
            🎯 Live Mode Only
          </button>
          <button
            onClick={() => setDetectionMode('simulation')}
            className={`px-6 py-3 rounded-lg font-semibold transition-all ${
              detectionMode === 'simulation'
                ? 'bg-purple-600 text-white shadow-lg scale-105'
                : 'bg-dark-bg text-dark-muted hover:bg-dark-border'
            }`}
          >
            🎬 Simulation Only
          </button>
        </div>
        <div className="mt-3 text-sm text-dark-muted">
          {detectionMode === 'all' && '📊 Showing ML data from both Live and Simulation modes'}
          {detectionMode === 'live' && '🎯 Showing ML data from real traffic only'}
          {detectionMode === 'simulation' && '🎬 Showing ML data from simulated traffic only'}
        </div>
      </div>

      {/* ML Status */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h2 className="text-xl font-semibold text-dark-text mb-4">
          📊 Feature Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
            <div className="flex items-center justify-between">
              <span className="text-dark-muted">Ensemble Scoring</span>
              <span className={mlStatus?.features.ensemble_scoring ? 'text-green-400' : 'text-red-400'}>
                {mlStatus?.features.ensemble_scoring ? '✅' : '❌'}
              </span>
            </div>
          </div>
          <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
            <div className="flex items-center justify-between">
              <span className="text-dark-muted">IP Risk Tracking</span>
              <span className={mlStatus?.features.ip_risk_tracking ? 'text-green-400' : 'text-red-400'}>
                {mlStatus?.features.ip_risk_tracking ? '✅' : '❌'}
              </span>
            </div>
          </div>
          <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
            <div className="flex items-center justify-between">
              <span className="text-dark-muted">SHAP Explainability</span>
              <span className={mlStatus?.features.shap_explainability ? 'text-green-400' : 'text-red-400'}>
                {mlStatus?.features.shap_explainability ? '✅' : '❌'}
              </span>
            </div>
          </div>
          <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
            <div className="flex items-center justify-between">
              <span className="text-dark-muted">Drift Detection</span>
              <span className={mlStatus?.features.drift_detection ? 'text-green-400' : 'text-red-400'}>
                {mlStatus?.features.drift_detection ? '✅' : '❌'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Detection Performance */}
      {enhancedStatus && enhancedPerformance && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-dark-text">
              ⚡ Enhanced Detection System
            </h2>
            <div className={`px-3 py-1 rounded-lg text-sm font-semibold ${
              enhancedStatus.enabled 
                ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                : 'bg-red-500/20 text-red-400 border border-red-500/30'
            }`}>
              {enhancedStatus.enabled ? '🟢 ACTIVE' : '🔴 DISABLED'}
            </div>
          </div>

          {/* Sensitivity Mode Controls */}
          <div className="mb-6">
            <div className="text-sm text-dark-muted mb-2">Sensitivity Mode</div>
            <div className="flex gap-3">
              <button
                onClick={() => changeSensitivity('high')}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                  enhancedStatus.sensitivity_mode === 'high'
                    ? 'bg-red-600 text-white shadow-lg'
                    : 'bg-dark-bg text-dark-muted hover:bg-dark-border'
                }`}
              >
                🔴 High (1.8x threshold)
              </button>
              <button
                onClick={() => changeSensitivity('balanced')}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                  enhancedStatus.sensitivity_mode === 'balanced'
                    ? 'bg-yellow-600 text-white shadow-lg'
                    : 'bg-dark-bg text-dark-muted hover:bg-dark-border'
                }`}
              >
                🟡 Balanced (2.5x threshold)
              </button>
              <button
                onClick={() => changeSensitivity('conservative')}
                className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                  enhancedStatus.sensitivity_mode === 'conservative'
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-dark-bg text-dark-muted hover:bg-dark-border'
                }`}
              >
                🔵 Conservative (4.0x threshold)
              </button>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-purple-500/10 rounded-lg p-4 border border-purple-500/30">
              <div className="text-purple-400 mb-1 text-sm font-semibold">Weak Signals Detected</div>
              <div className="text-3xl font-bold text-purple-400">
                {enhancedPerformance.weak_signals_caught}
              </div>
              <div className="text-xs text-dark-muted mt-1">
                Missed by basic detector
              </div>
            </div>
            <div className="bg-red-500/10 rounded-lg p-4 border border-red-500/30">
              <div className="text-red-400 mb-1 text-sm font-semibold">Adversarial Attacks Blocked</div>
              <div className="text-3xl font-bold text-red-400">
                {enhancedPerformance.adversarial_attacks_detected}
              </div>
              <div className="text-xs text-dark-muted mt-1">
                Bot patterns, timing attacks
              </div>
            </div>
            <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
              <div className="text-green-400 mb-1 text-sm font-semibold">Total Improvements</div>
              <div className="text-3xl font-bold text-green-400">
                {enhancedPerformance.total_improved_detections}
              </div>
              <div className="text-xs text-dark-muted mt-1">
                Enhanced vs basic detection
              </div>
            </div>
          </div>

          {/* Detection Techniques Active */}
          <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
            <div className="text-sm text-dark-muted mb-3">Active Detection Techniques</div>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <div className="flex items-center gap-2">
                <span className="text-green-400">✅</span>
                <span className="text-sm text-dark-text">Z-Score Analysis</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-400">✅</span>
                <span className="text-sm text-dark-text">Percentile Detection</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-400">✅</span>
                <span className="text-sm text-dark-text">Micro-Spike Detection</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-400">✅</span>
                <span className="text-sm text-dark-text">Trend Analysis</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-green-400">✅</span>
                <span className="text-sm text-dark-text">Adversarial Patterns</span>
              </div>
            </div>
          </div>

          {/* Improvement Percentage */}
          {enhancedPerformance.improvement_percentage > 0 && (
            <div className="mt-4 bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-lg p-4 border border-green-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-dark-muted">Detection Improvement</div>
                  <div className="text-2xl font-bold text-green-400">
                    +{enhancedPerformance.improvement_percentage.toFixed(1)}%
                  </div>
                </div>
                <div className="text-4xl">📈</div>
              </div>
              <div className="mt-2 text-xs text-dark-muted">
                Enhanced detection caught {enhancedPerformance.improvement_percentage.toFixed(1)}% more threats than basic detection
              </div>
            </div>
          )}
        </div>
      )}

      {/* IP Risk Statistics */}
      {(() => {
        const filteredStats = calculateFilteredStats();
        return filteredStats ? (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-xl font-semibold text-dark-text mb-4">
            📈 IP Risk Overview
            {detectionMode !== 'all' && (
              <span className="ml-2 text-sm text-dark-muted">
                ({detectionMode === 'live' ? 'Live Mode' : 'Simulation Mode'})
              </span>
            )}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
              <div className="text-dark-muted mb-1">Total IPs Tracked</div>
              <div className="text-2xl font-bold text-dark-text">{filteredStats.total_ips}</div>
            </div>
            <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
              <div className="text-dark-muted mb-1">High Risk IPs</div>
              <div className="text-2xl font-bold text-red-400">{filteredStats.risk_distribution.high}</div>
            </div>
            <div className="bg-dark-bg rounded-lg p-4 border border-dark-border">
              <div className="text-dark-muted mb-1">Flagged IPs</div>
              <div className="text-2xl font-bold text-yellow-400">{filteredStats.flagged_ips}</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-500/10 rounded-lg p-4 border border-green-500/30">
              <div className="text-green-400 mb-1 font-semibold">Low Risk (0-30)</div>
              <div className="text-2xl font-bold text-green-400">{filteredStats.risk_distribution.low}</div>
            </div>
            <div className="bg-yellow-500/10 rounded-lg p-4 border border-yellow-500/30">
              <div className="text-yellow-400 mb-1 font-semibold">Medium Risk (30-70)</div>
              <div className="text-2xl font-bold text-yellow-400">{filteredStats.risk_distribution.medium}</div>
            </div>
            <div className="bg-red-500/10 rounded-lg p-4 border border-red-500/30">
              <div className="text-red-400 mb-1 font-semibold">High Risk (70-100)</div>
              <div className="text-2xl font-bold text-red-400">{filteredStats.risk_distribution.high}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-xl font-semibold text-dark-text mb-4">
            📈 IP Risk Overview
          </h2>
          <div className="text-center py-8 text-dark-muted">
            No IP tracking data available yet. Start generating traffic to see statistics.
          </div>
        </div>
      );
      })()}

      {/* High Risk IPs Table */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6">
        <h2 className="text-xl font-semibold text-dark-text mb-4">
          🚨 High Risk IP Addresses
          {detectionMode !== 'all' && (
            <span className="ml-2 text-sm text-dark-muted">
              ({detectionMode === 'live' ? 'Live Mode' : 'Simulation Mode'})
            </span>
          )}
        </h2>
        {getFilteredHighRiskIPs().length === 0 ? (
          <div className="text-center py-8 text-dark-muted">
            No high-risk IPs detected
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-dark-bg border-b border-dark-border">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">
                    Risk Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">
                    Anomalies
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">
                    Total Requests
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">
                    Anomaly Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border">
                {getFilteredHighRiskIPs().map((ip, index) => (
                  <tr key={index} className="hover:bg-dark-bg transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-dark-text">
                      {ip.ip_address}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`font-bold ${getRiskColor(ip.risk_score)}`}>
                        {ip.risk_score.toFixed(1)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text">
                      {ip.anomaly_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text">
                      {ip.total_requests}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-text">
                      {(ip.anomaly_rate * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${getRiskBadge(ip.risk_score)}`}>
                        {ip.flagged ? '🚩 FLAGGED' : 'Monitored'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ML Model Predictions Breakdown */}
      {recentPredictions.length > 0 && (
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h2 className="text-xl font-semibold text-dark-text mb-4">
            🤖 Recent ML Model Predictions
            {detectionMode !== 'all' && (
              <span className="ml-2 text-sm text-dark-muted">
                ({detectionMode === 'live' ? 'Live Mode' : 'Simulation Mode'})
              </span>
            )}
          </h2>
          <div className="space-y-4">
            {recentPredictions.map((pred) => (
              <div key={pred.id} className="bg-dark-bg rounded-lg p-4 border border-dark-border">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <span className="font-mono text-sm text-info-400">{pred.endpoint}</span>
                    <div className="text-xs text-dark-muted mt-1">
                      {new Date(pred.timestamp).toLocaleString()} • {pred.anomaly_type} • {pred.severity}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-dark-muted">Ensemble Score</div>
                    <div className="text-2xl font-bold text-info-400">
                      {(pred.ml_predictions.ensemble * 100).toFixed(1)}
                    </div>
                    <div className="text-xs text-dark-muted uppercase">{pred.ml_predictions.risk_level}</div>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-purple-500/10 rounded p-3 border border-purple-500/30">
                    <div className="text-xs text-purple-400 mb-1">Random Forest</div>
                    <div className="text-lg font-bold text-purple-400">
                      {(pred.ml_predictions.random_forest * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-blue-500/10 rounded p-3 border border-blue-500/30">
                    <div className="text-xs text-blue-400 mb-1">Isolation Forest</div>
                    <div className="text-lg font-bold text-blue-400">
                      {(pred.ml_predictions.isolation_forest * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-green-500/10 rounded p-3 border border-green-500/30">
                    <div className="text-xs text-green-400 mb-1">Heuristic</div>
                    <div className="text-lg font-bold text-green-400">
                      {(pred.ml_predictions.heuristic * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feature Descriptions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-dark-text mb-3">
            🎯 Ensemble Threat Scoring
          </h3>
          <p className="text-dark-muted text-sm">
            Combines Random Forest, Isolation Forest, and heuristic rules with weighted ensemble 
            (RF: 0.4, ISO: 0.3, Heuristics: 0.3) for more accurate threat detection.
          </p>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-dark-text mb-3">
            📍 IP Risk Tracking
          </h3>
          <p className="text-dark-muted text-sm">
            Cumulative 0-100 risk scoring per IP with temporal decay. Tracks anomaly frequency, 
            severity, and request volume over a 24-hour window.
          </p>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-dark-text mb-3">
            💡 SHAP Explainability
          </h3>
          <p className="text-dark-muted text-sm">
            Provides interpretable explanations for model predictions using SHAP values. 
            Shows top-5 contributing features for each anomaly detection.
          </p>
        </div>
        <div className="bg-dark-card rounded-lg border border-dark-border p-6">
          <h3 className="text-lg font-semibold text-dark-text mb-3">
            📊 Concept Drift Detection
          </h3>
          <p className="text-dark-muted text-sm">
            Monitors distribution changes using Kolmogorov-Smirnov test (p &lt; 0.05). 
            Alerts when production data diverges from training data.
          </p>
        </div>
      </div>
    </div>
  );
};

export default MLFeatures;
