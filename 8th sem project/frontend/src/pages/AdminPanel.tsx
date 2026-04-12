import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE = 'http://localhost:8000';

interface BlockedIP {
  ip: string;
  total_requests: number;
  anomaly_count: number;
  avg_risk: number;
  last_seen: string;
}

interface IPProfile {
  ip: string;
  total_requests: number;
  anomaly_count: number;
  avg_risk: number;
  last_seen: string;
  blocked: boolean;
  is_simulation?: boolean;
}

const AdminPanel: React.FC = () => {
  const [blockedIPs, setBlockedIPs] = useState<BlockedIP[]>([]);
  const [allProfiles, setAllProfiles] = useState<IPProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [unblocking, setUnblocking] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'blocked' | 'all'>('blocked');
  const [runningDemo, setRunningDemo] = useState(false);

  const fetchBlockedIPs = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/security/realtime/blocked-ips`);
      setBlockedIPs(response.data.blocked_ips || []);
    } catch (error) {
      console.error('Error fetching blocked IPs:', error);
    }
  };

  const fetchAllProfiles = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/security/realtime/status`);
      if (response.data.ip_profiles) {
        const profiles = Object.entries(response.data.ip_profiles).map(([ip, profile]: [string, any]) => ({
          ip,
          total_requests: profile.total_requests,
          anomaly_count: profile.anomaly_count,
          avg_risk: profile.avg_risk,
          last_seen: profile.last_seen,
          blocked: profile.blocked,
          is_simulation: profile.is_simulation
        }));
        // Sort by anomaly count descending
        profiles.sort((a, b) => b.anomaly_count - a.anomaly_count);
        setAllProfiles(profiles);
      }
    } catch (error) {
      console.error('Error fetching IP profiles:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    await Promise.all([fetchBlockedIPs(), fetchAllProfiles()]);
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const handleUnblock = async (ip: string) => {
    setUnblocking(ip);
    try {
      await axios.post(`${API_BASE}/api/security/realtime/unblock/${ip}`);
      toast.success(`Successfully unblocked IP: ${ip}`);
      await fetchData();
    } catch (error: any) {
      console.error('Error unblocking IP:', error);
      toast.error(error.response?.data?.detail || 'Failed to unblock IP');
    } finally {
      setUnblocking(null);
    }
  };

  const getRiskColor = (risk: number) => {
    if (risk >= 0.8) return 'text-red-500';
    if (risk >= 0.6) return 'text-orange-500';
    if (risk >= 0.4) return 'text-yellow-500';
    return 'text-green-500';
  };

  const getRiskBadge = (risk: number) => {
    if (risk >= 0.8) return 'bg-red-500/20 text-red-500';
    if (risk >= 0.6) return 'bg-orange-500/20 text-orange-500';
    if (risk >= 0.4) return 'bg-yellow-500/20 text-yellow-500';
    return 'bg-green-500/20 text-green-500';
  };

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return 'N/A';
    return new Date(new Date(timestamp).getTime() + (5*60+30)*60000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) + ' IST';
  };

  const runBlockingDemo = async () => {
    setRunningDemo(true);
    toast.loading('🎬 Running IP blocking demonstration...', { id: 'demo' });

    try {
      // Run a quick simulation that will trigger blocking
      // Uses /sim/login which generates SQL injection attacks
      // SQL injection uses concentrated IPs (SIM-1 to SIM-30) = same IPs make multiple requests
      // 70% anomaly rate means ~35 anomalies in 50 requests
      // With ~30 unique IPs, several IPs will hit the 5-anomaly blocking threshold
      const response = await axios.post(
        `${API_BASE}/simulation/start`,
        null,
        {
          params: {
            simulated_endpoint: '/sim/login',  // SQL injection endpoint (concentrated IPs)
            duration_seconds: 15,  // Run for 15 seconds
            requests_per_window: 50  // 50 requests = ~35 anomalies at 70% rate
          }
        }
      );
      
      // Show progress message
      toast.loading('⚙️ Generating malicious traffic from concentrated IPs...', { id: 'demo' });
      
      // Wait for simulation to complete
      setTimeout(() => {
        toast.success('✅ Demo completed! IPs with 5+ anomalies have been auto-blocked.', { id: 'demo' });
        fetchData();
        setSelectedTab('blocked');
      }, 16000);  // Wait 16 seconds (simulation duration + buffer)
      
    } catch (error) {
      console.error('Error running demo:', error);
      toast.error('❌ Failed to run demo. Check if backend is running.', { id: 'demo' });
    } finally {
      setTimeout(() => setRunningDemo(false), 16000);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-text">IP Security Management</h1>
          <p className="text-dark-muted mt-1">
            Monitor and manage IP addresses - Auto-blocks after 5 anomalies
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={runBlockingDemo}
            disabled={runningDemo}
            className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          >
            {runningDemo ? '⏳ Running Demo...' : '🎬 Demo IP Blocking'}
          </button>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              autoRefresh
                ? 'bg-green-500/20 text-green-500 border border-green-500'
                : 'bg-dark-border text-dark-muted border border-dark-border'
            }`}
          >
            {autoRefresh ? '🔄 Auto-Refresh ON' : '⏸️ Auto-Refresh OFF'}
          </button>
          <button
            onClick={fetchData}
            disabled={loading}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {loading ? '⏳ Refreshing...' : '🔄 Refresh Now'}
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-red-500/10 to-red-600/10 border border-red-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-400 text-sm font-medium">Blocked IPs</p>
              <p className="text-3xl font-bold text-red-500 mt-1">{blockedIPs.length}</p>
            </div>
            <div className="text-4xl">🚫</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-400 text-sm font-medium">Tracked IPs</p>
              <p className="text-3xl font-bold text-blue-500 mt-1">{allProfiles.length}</p>
            </div>
            <div className="text-4xl">👁️</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border border-yellow-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-yellow-400 text-sm font-medium">At Risk (4+ anomalies)</p>
              <p className="text-3xl font-bold text-yellow-500 mt-1">
                {allProfiles.filter(p => p.anomaly_count >= 4 && !p.blocked).length}
              </p>
            </div>
            <div className="text-4xl">⚠️</div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/30 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-400 text-sm font-medium">Clean IPs</p>
              <p className="text-3xl font-bold text-green-500 mt-1">
                {allProfiles.filter(p => p.anomaly_count === 0).length}
              </p>
            </div>
            <div className="text-4xl">✅</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-border">
        <button
          onClick={() => setSelectedTab('blocked')}
          className={`px-6 py-3 font-medium transition-colors relative ${
            selectedTab === 'blocked'
              ? 'text-primary-500'
              : 'text-dark-muted hover:text-dark-text'
          }`}
        >
          🚫 Blocked IPs ({blockedIPs.length})
          {selectedTab === 'blocked' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"></div>
          )}
        </button>
        <button
          onClick={() => setSelectedTab('all')}
          className={`px-6 py-3 font-medium transition-colors relative ${
            selectedTab === 'all'
              ? 'text-primary-500'
              : 'text-dark-muted hover:text-dark-text'
          }`}
        >
          📊 All Tracked IPs ({allProfiles.length})
          {selectedTab === 'all' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"></div>
          )}
        </button>
      </div>

      {/* Content based on selected tab */}
      {selectedTab === 'blocked' && (
        <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
          <div className="p-4 bg-red-500/10 border-b border-red-500/30">
            <h2 className="text-xl font-bold text-red-500 flex items-center gap-2">
              🚫 Blocked IP Addresses
            </h2>
            <p className="text-sm text-red-400 mt-1">
              These IPs have been automatically blocked due to suspicious activity (5+ anomalies)
            </p>
          </div>

          {loading ? (
            <div className="p-8 text-center text-dark-muted">
              <div className="inline-block animate-spin text-4xl">⏳</div>
              <p className="mt-2">Loading blocked IPs...</p>
            </div>
          ) : blockedIPs.length === 0 ? (
            <div className="p-8 text-center text-dark-muted">
              <div className="text-6xl mb-4">✅</div>
              <p className="text-lg">No blocked IPs</p>
              <p className="text-sm mt-1">All IPs are currently allowed</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-dark-border/30">
                  <tr>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">IP Address</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Anomalies</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Total Requests</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Avg Risk</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Last Seen</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {blockedIPs.map((ip) => (
                    <tr key={ip.ip} className="border-b border-dark-border/50 hover:bg-dark-border/20 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-mono text-dark-text bg-dark-bg px-2 py-1 rounded">
                          {ip.ip}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-3 py-1 bg-red-500/20 text-red-500 rounded-full text-sm font-semibold">
                          {ip.anomaly_count}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-dark-text">{ip.total_requests}</td>
                      <td className="py-3 px-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskBadge(ip.avg_risk)}`}>
                          {(ip.avg_risk * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-dark-muted text-sm">{formatTimestamp(ip.last_seen)}</td>
                      <td className="py-3 px-4">
                        <button
                          onClick={() => handleUnblock(ip.ip)}
                          disabled={unblocking === ip.ip}
                          className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {unblocking === ip.ip ? '⏳ Unblocking...' : '✅ Unblock'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'all' && (
        <div className="bg-dark-card rounded-lg border border-dark-border overflow-hidden">
          <div className="p-4 bg-primary-500/10 border-b border-primary-500/30">
            <h2 className="text-xl font-bold text-primary-500 flex items-center gap-2">
              📊 All Tracked IP Addresses
            </h2>
            <p className="text-sm text-primary-400 mt-1">
              Real-time IP tracking with automatic blocking at 5 anomalies
            </p>
          </div>

          {loading ? (
            <div className="p-8 text-center text-dark-muted">
              <div className="inline-block animate-spin text-4xl">⏳</div>
              <p className="mt-2">Loading IP profiles...</p>
            </div>
          ) : allProfiles.length === 0 ? (
            <div className="p-8 text-center text-dark-muted">
              <div className="text-6xl mb-4">📭</div>
              <p className="text-lg">No tracked IPs</p>
              <p className="text-sm mt-1">No traffic has been detected yet</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-dark-border/30">
                  <tr>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">IP Address</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Anomalies</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Total Requests</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Avg Risk</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Last Seen</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-dark-muted">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {allProfiles.map((profile) => (
                    <tr key={profile.ip} className="border-b border-dark-border/50 hover:bg-dark-border/20 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-dark-text bg-dark-bg px-2 py-1 rounded">
                            {profile.ip}
                          </span>
                          {profile.is_simulation && (
                            <span className="px-2 py-0.5 bg-purple-500/20 text-purple-500 rounded text-xs font-medium">
                              SIM
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        {profile.blocked ? (
                          <span className="px-3 py-1 bg-red-500/20 text-red-500 rounded-full text-sm font-semibold">
                            🚫 Blocked
                          </span>
                        ) : profile.anomaly_count >= 4 ? (
                          <span className="px-3 py-1 bg-yellow-500/20 text-yellow-500 rounded-full text-sm font-semibold">
                            ⚠️ At Risk
                          </span>
                        ) : (
                          <span className="px-3 py-1 bg-green-500/20 text-green-500 rounded-full text-sm font-semibold">
                            ✅ Active
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          profile.anomaly_count >= 5 
                            ? 'bg-red-500/20 text-red-500' 
                            : profile.anomaly_count >= 4
                            ? 'bg-yellow-500/20 text-yellow-500'
                            : 'bg-green-500/20 text-green-500'
                        }`}>
                          {profile.anomaly_count} / {profile.total_requests}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-dark-text">{profile.total_requests}</td>
                      <td className="py-3 px-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getRiskBadge(profile.avg_risk)}`}>
                          {(profile.avg_risk * 100).toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3 px-4 text-dark-muted text-sm">{formatTimestamp(profile.last_seen)}</td>
                      <td className="py-3 px-4">
                        {profile.blocked ? (
                          <button
                            onClick={() => handleUnblock(profile.ip)}
                            disabled={unblocking === profile.ip}
                            className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {unblocking === profile.ip ? '⏳ Unblocking...' : '✅ Unblock'}
                          </button>
                        ) : (
                          <span className="text-dark-muted text-sm">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Info Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
          <h3 className="text-blue-400 font-semibold mb-2">ℹ️ How It Works</h3>
          <ul className="text-sm text-blue-300 space-y-1">
            <li>✓ All incoming requests are tracked by IP address automatically</li>
            <li>✓ Anomalies are detected using ML models (XGBoost + Autoencoder)</li>
            <li>✓ When an IP exceeds <strong>5 anomalies</strong>, it gets automatically blocked</li>
            <li>✓ Blocked IPs receive a 403 Forbidden response on all subsequent requests</li>
            <li>✓ Administrators can manually unblock IPs using the buttons above</li>
            <li>✓ Both live and simulation IPs can be blocked for demonstration</li>
          </ul>
        </div>

        <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-4">
          <h3 className="text-purple-400 font-semibold mb-2">🎬 How Demo IP Blocking Works</h3>
          <ul className="text-sm text-purple-300 space-y-1">
            <li><strong>1. Simulates SQL Injection Attack:</strong> Generates malicious login attempts at /sim/login endpoint</li>
            <li><strong>2. Concentrated IP Pool:</strong> Uses only 30 unique IPs (SIM-1 to SIM-30) - same IPs attack repeatedly</li>
            <li><strong>3. High Anomaly Rate:</strong> 70% of requests contain SQL injection patterns (e.g., OR '1'='1)</li>
            <li><strong>4. Auto-Blocking Trigger:</strong> When any IP reaches 5 anomalies, it's automatically blocked</li>
            <li><strong>5. Result:</strong> Several IPs will be blocked within 15 seconds due to repeated attacks</li>
            <li><strong>6. Verification:</strong> Check "Blocked IPs" tab to see auto-blocked malicious IPs</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
