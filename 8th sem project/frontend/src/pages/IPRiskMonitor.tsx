import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = 'http://localhost:8000';

interface IPProfile {
  total_requests: number;
  anomaly_count: number;
  avg_risk: number;
  last_seen: string;
  blocked: boolean;
  is_simulation?: boolean;
}

interface SecurityStatus {
  total_ips: number;
  blocked_ips_count: number;
  total_requests: number;
  total_anomalies: number;
  ip_profiles: Record<string, IPProfile>;
  blocked_ips: string[];
}

const IPRiskMonitor: React.FC = () => {
  const [status, setStatus] = useState<SecurityStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/security/realtime/status`);
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching security status:', error);
      if (loading) {
        // Only show error toast on initial load
        toast.error('Failed to load IP security data');
      }
    }
  };

  const unblockIP = async (ip: string) => {
    try {
      await axios.post(`${API_BASE}/api/security/realtime/unblock/${ip}`);
      toast.success(`✅ IP ${ip} unblocked successfully`);
      fetchStatus(); // Refresh data
    } catch (error) {
      console.error('Error unblocking IP:', error);
      toast.error(`❌ Failed to unblock IP ${ip}`);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchStatus();
      setLoading(false);
    };
    
    loadData();
    
    let interval: number | null = null;
    if (autoRefresh) {
      interval = setInterval(fetchStatus, 3000) as unknown as number; // Refresh every 3 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getRiskBadge = (risk: number) => {
    if (risk > 0.7) return 'bg-red-500/20 text-red-400 border-red-500/50';
    if (risk > 0.4) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
    return 'bg-green-500/20 text-green-400 border-green-500/50';
  };

  const getAnomalyBadge = (count: number) => {
    if (count >= 5) return 'bg-red-500/20 text-red-400 border-red-500/50';
    if (count >= 4) return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
    if (count >= 2) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
    return 'bg-green-500/20 text-green-400 border-green-500/50';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-dark-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500" />
      </div>
    );
  }

  const atRiskIPs = status ? Object.entries(status.ip_profiles).filter(([_, profile]) => 
    profile.anomaly_count >= 4 && !profile.blocked
  ).length : 0;

  const cleanIPs = status ? Object.entries(status.ip_profiles).filter(([_, profile]) => 
    !profile.blocked && profile.anomaly_count === 0
  ).length : 0;

  return (
    <div className="min-h-screen bg-dark-bg p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-dark-text mb-2">🔒 IP Security Monitor</h1>
            <p className="text-dark-muted">Real-time IP tracking with automated threat blocking (≥5 anomalies)</p>
          </div>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 text-dark-muted cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4 rounded border-dark-border bg-dark-card text-primary-500 focus:ring-primary-500 focus:ring-offset-dark-bg"
              />
              <span className="text-sm">Auto-Refresh</span>
            </label>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span className="text-green-400 text-sm font-medium">Live</span>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-dark-card border border-primary-500 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-dark-muted mb-1">Total IPs Tracked</p>
                <p className="text-3xl font-bold text-dark-text">
                  {status?.total_ips || 0}
                </p>
                <p className="text-xs text-dark-muted mt-1">{status?.total_requests || 0} total requests</p>
              </div>
              <div className="text-4xl">👥</div>
            </div>
          </div>

          <div className="bg-dark-card border border-danger-500 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-dark-muted mb-1">Blocked IPs</p>
                <p className="text-3xl font-bold text-danger-500">
                  {status?.blocked_ips_count || 0}
                </p>
                <p className="text-xs text-dark-muted mt-1">Auto-blocked threats</p>
              </div>
              <div className="text-4xl">🚫</div>
            </div>
          </div>

          <div className="bg-dark-card border border-warning-500 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-dark-muted mb-1">At Risk (4+ anomalies)</p>
                <p className="text-3xl font-bold text-warning-500">
                  {atRiskIPs}
                </p>
                <p className="text-xs text-dark-muted mt-1">Close to blocking</p>
              </div>
              <div className="text-4xl">⚠️</div>
            </div>
          </div>

          <div className="bg-dark-card border border-success-500 rounded-lg p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-dark-muted mb-1">Clean IPs</p>
                <p className="text-3xl font-bold text-success-500">
                  {cleanIPs}
                </p>
                <p className="text-xs text-dark-muted mt-1">Zero anomalies</p>
              </div>
              <div className="text-4xl">✅</div>
            </div>
          </div>
        </div>

        {/* Blocked IPs Section */}
        {status && status.blocked_ips.length > 0 && (
          <div className="bg-dark-card border border-danger-500 rounded-lg p-6">
            <h2 className="text-xl font-bold text-dark-text mb-4 flex items-center gap-2">
              <span>🚫</span> Blocked IP Addresses
            </h2>
            <div className="space-y-2">
              {status.blocked_ips.map(ip => {
                const profile = status.ip_profiles[ip];
                return (
                  <div key={ip} className="flex items-center justify-between p-4 bg-danger-500/10 border border-danger-500/30 rounded-lg">
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">⛔</span>
                      <div>
                        <span className="font-mono font-bold text-danger-400 block">{ip}</span>
                        {profile && (
                          <span className="text-xs text-dark-muted">
                            Anomalies: {profile.anomaly_count} | Requests: {profile.total_requests} | 
                            Avg Risk: {(profile.avg_risk * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => unblockIP(ip)}
                      className="px-4 py-2 bg-success-500 hover:bg-success-600 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      ✅ Unblock
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* All IP Profiles Table */}
        <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-dark-border">
            <h2 className="text-xl font-bold text-dark-text flex items-center gap-2">
              <span>📊</span> All Tracked IP Addresses
            </h2>
            <p className="text-sm text-dark-muted mt-1">Real-time monitoring of all IP activity</p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-dark-border">
              <thead className="bg-dark-bg">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">IP Address</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">Requests</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">Anomalies</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">Avg Risk</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">Last Seen</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-dark-muted uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-border">
                {status && Object.entries(status.ip_profiles)
                  .sort(([, a], [, b]) => b.anomaly_count - a.anomaly_count || b.avg_risk - a.avg_risk)
                  .map(([ip, profile]) => (
                    <tr key={ip} className={`hover:bg-dark-bg/50 transition-colors ${profile.blocked ? 'bg-danger-500/5' : ''}`}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-sm font-semibold text-dark-text">{ip}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-muted">
                        {profile.total_requests}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getAnomalyBadge(profile.anomaly_count)}`}>
                          {profile.anomaly_count} {profile.anomaly_count >= 4 ? '⚠️' : ''}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getRiskBadge(profile.avg_risk)}`}>
                          {(profile.avg_risk * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-muted">
                        {new Date(new Date(profile.last_seen).getTime() + (5*60+30)*60000).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })} IST
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-dark-muted">
                        {profile.is_simulation ? (
                          <span className="px-2 py-1 bg-purple-500/20 text-purple-400 border border-purple-500/50 rounded text-xs font-medium">
                            SIMULATION
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/50 rounded text-xs font-medium">
                            LIVE
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {profile.blocked ? (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-danger-500/20 text-danger-400 border border-danger-500/50">
                            🚫 BLOCKED
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-500/20 text-success-400 border border-success-500/50">
                            ✓ ACTIVE
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Info Panel */}
        <div className="bg-primary-500/10 border border-primary-500/30 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-primary-400 mb-2">ℹ️ How IP Blocking Works</h3>
          <ul className="text-sm text-primary-300 space-y-1">
            <li>✓ All incoming requests are tracked by IP address in real-time</li>
            <li>✓ ML models (XGBoost + Autoencoder) analyze each request for anomalies</li>
            <li>✓ When an IP exceeds <strong>5 anomalies</strong>, it's automatically blocked</li>
            <li>✓ Blocked IPs receive a 403 Forbidden response on all subsequent requests</li>
            <li>✓ Administrators can manually unblock IPs using the buttons above</li>
            <li>✓ Both live and simulation traffic is tracked separately</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default IPRiskMonitor;
