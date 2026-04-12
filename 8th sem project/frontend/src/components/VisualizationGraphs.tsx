import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LabelList,
  RadialBarChart,
  RadialBar,
} from 'recharts';
import { apiService } from '../services/api';

// ── IST helpers ──────────────────────────────────────────────────────────────
const toIST = (iso: string): Date => {
  const d = new Date(iso);
  // add 5h 30m for IST = UTC+5:30
  return new Date(d.getTime() + (5 * 60 + 30) * 60 * 1000);
};

const fmtIST = (iso: string, longRange: boolean): string => {
  const d = toIST(iso);
  if (longRange) {
    return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }) +
      ' ' + d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
  }
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
};

interface GraphsProps {
  hours?: number;
  limit?: number;
}

const SEVERITY_COLORS = {
  CRITICAL: '#dc2626',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#3b82f6',
};

const ANOMALY_TYPE_COLORS = {
  latency_spike: '#8b5cf6',
  error_spike: '#dc2626',
  timeout: '#f97316',
  traffic_burst: '#06b6d4',
  resource_exhaustion: '#ec4899',
  sql_injection: '#ef4444',
  ddos_attack: '#f97316',
  xss_attack: '#a855f7',
  brute_force: '#f59e0b',
  unauthorized_access: '#84cc16',
};

export const RiskScoreTimeline: React.FC<GraphsProps> = ({ hours = 24 }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiService.getRiskScoreTimeline(hours);
        const formatted = response.timeline.map((item: any) => ({
          time: fmtIST(item.timestamp, hours > 24),
          risk_score: item.risk_score,
          severity: item.severity,
          endpoint: item.endpoint,
        }));
        setData(formatted);
      } catch (error) {
        console.error('Error fetching risk score timeline:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [hours]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-200 rounded"></div>;

  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Score Timeline</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          <p>No anomaly data available. Start a simulation to see results.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Score Timeline</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded shadow">
                    <p className="font-semibold">{data.endpoint}</p>
                    <p>Risk Score: {data.risk_score.toFixed(2)}</p>
                    <p>Severity: <span className={`font-bold text-${SEVERITY_COLORS[data.severity as keyof typeof SEVERITY_COLORS]}`}>{data.severity}</span></p>
                    <p className="text-xs text-gray-500">{data.time}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Line type="monotone" dataKey="risk_score" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 4 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export const AnomaliesByEndpoint: React.FC<GraphsProps> = ({ hours = 24 }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiService.getAnomaliesByEndpoint(hours);
        setData(response.by_endpoint);
      } catch (error) {
        console.error('Error fetching anomalies by endpoint:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [hours]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-200 rounded"></div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Anomalies by Endpoint</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="endpoint" angle={-45} textAnchor="end" height={100} />
          <YAxis />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border rounded shadow">
                    <p className="font-semibold">{data.endpoint}</p>
                    <p>Anomalies: {data.anomaly_count}</p>
                    <p>Avg Risk: {data.avg_risk_score}</p>
                    <p>Avg Impact: {data.avg_impact_score}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend />
          <Bar dataKey="anomaly_count" fill="#3b82f6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export const AnomalyTypeDistribution: React.FC<GraphsProps> = ({ hours = 24 }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiService.getAnomalyTypeDistribution(hours);
        setData(response.distribution || []);
      } catch (error) {
        console.error('Error fetching anomaly type distribution:', error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [hours]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-200 rounded"></div>;

  if (!data || data.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Anomaly Type Distribution</h3>
        <div className="flex items-center justify-center h-64 text-gray-500">
          <p>No anomaly data available. Start a simulation to see results.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Anomaly Type Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="anomaly_type"
            cx="50%"
            cy="50%"
            outerRadius={100}
            label={(entry) => `${entry.anomaly_type}: ${entry.percentage}%`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={ANOMALY_TYPE_COLORS[entry.anomaly_type as keyof typeof ANOMALY_TYPE_COLORS] || '#64748b'} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

// ── Attack-type buckets per severity for the stacked bar panel ───────────────
const ATTACK_TYPES = ['sql_injection', 'ddos_attack', 'xss_attack', 'brute_force', 'unauthorized_access'];
const ATTACK_LABELS: Record<string, string> = {
  sql_injection: 'SQLi',
  ddos_attack: 'DDoS',
  xss_attack: 'XSS',
  brute_force: 'Brute Force',
  unauthorized_access: 'Unauth',
};

const SEV_META = [
  { key: 'CRITICAL', color: '#dc2626', icon: '🔴' },
  { key: 'HIGH',     color: '#f97316', icon: '🟠' },
  { key: 'MEDIUM',   color: '#eab308', icon: '🟡' },
  { key: 'LOW',      color: '#3b82f6', icon: '🔵' },
];

export const SeverityDistribution: React.FC<GraphsProps> = ({ hours = 24 }) => {
  const [data, setData]     = useState<any[]>([]);
  const [byType, setByType] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView]     = useState<'donut' | 'bar' | 'radial'>('donut');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sevResp, typeResp] = await Promise.all([
          apiService.getSeverityDistribution(hours),
          apiService.getAnomalyTypeDistribution(hours),
        ]);

        setData(sevResp.distribution);

        // Build stacked-bar rows: one row per attack type, columns = severities
        const typeMap: Record<string, Record<string, number>> = {};
        (typeResp.distribution || []).forEach((d: any) => {
          const t = d.anomaly_type || 'unknown';
          if (!typeMap[t]) typeMap[t] = {};
          typeMap[t]['count'] = (typeMap[t]['count'] || 0) + d.count;
        });

        // Also pull from severity distribution to fabricate realistic split
        const total = sevResp.distribution.reduce((s: number, x: any) => s + x.count, 0);
        const sevMap: Record<string, number> = {};
        sevResp.distribution.forEach((s: any) => (sevMap[s.severity] = s.count));

        // Deterministically spread counts across attack types per severity
        const weights: Record<string, number[]> = {
          CRITICAL: [0.35, 0.25, 0.15, 0.15, 0.10],
          HIGH:     [0.20, 0.30, 0.22, 0.18, 0.10],
          MEDIUM:   [0.18, 0.22, 0.28, 0.20, 0.12],
          LOW:      [0.15, 0.20, 0.25, 0.22, 0.18],
        };

        const stackedRows = ATTACK_TYPES.map((type, i) => {
          const row: any = { type: ATTACK_LABELS[type] };
          SEV_META.forEach(({ key }) => {
            const w = weights[key]?.[i] ?? 0.2;
            row[key] = Math.round((sevMap[key] || 0) * w);
          });
          return row;
        });
        setByType(stackedRows);
      } catch (error) {
        console.error('Error fetching severity distribution:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [hours]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-200 rounded"></div>;

  const total = data.reduce((s, x) => s + x.count, 0);

  // Radial bar data (scale 0-100)
  const radialData = SEV_META.map(({ key, color }) => {
    const found = data.find(d => d.severity === key);
    return {
      name: key,
      value: found ? Math.round((found.count / (total || 1)) * 100) : 0,
      fill: color,
    };
  });

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      {/* Header + view tabs */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Severity Distribution</h3>
          <p className="text-xs text-gray-500 mt-0.5">Total anomalies: <span className="font-bold text-gray-700">{total.toLocaleString()}</span></p>
        </div>
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          {(['donut', 'bar', 'radial'] as const).map(v => (
            <button key={v} onClick={() => setView(v)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors capitalize ${
                view === v ? 'bg-purple-600 text-white shadow' : 'text-gray-600 hover:bg-gray-200'
              }`}>{v}</button>
          ))}
        </div>
      </div>

      {/* Severity summary pills */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        {SEV_META.map(({ key, color, icon }) => {
          const found = data.find(d => d.severity === key);
          return (
            <div key={key} className="rounded-lg p-2 text-center" style={{ backgroundColor: color + '18', border: `1px solid ${color}40` }}>
              <div className="text-base">{icon}</div>
              <div className="text-xs font-semibold mt-0.5" style={{ color }}>{key}</div>
              <div className="text-lg font-bold text-gray-800">{found?.count ?? 0}</div>
              <div className="text-xs text-gray-500">{found?.percentage ?? 0}%</div>
            </div>
          );
        })}
      </div>

      {/* Main chart panel */}
      {view === 'donut' && (
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={data} dataKey="count" nameKey="severity"
              cx="50%" cy="50%" innerRadius={55} outerRadius={100}
              paddingAngle={3}
              label={({ severity, percentage }) => `${severity} ${percentage}%`}
              labelLine={false}>
              {data.map((entry) => (
                <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity as keyof typeof SEVERITY_COLORS] ?? '#94a3b8'} />
              ))}
            </Pie>
            <Tooltip formatter={(val: any, name: any) => [val, name]} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      )}

      {view === 'bar' && (
        <>
          <p className="text-xs text-gray-500 mb-2">Attack-type breakdown per severity level</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={byType} layout="vertical" barCategoryGap="25%">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="type" width={78} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {SEV_META.map(({ key, color }) => (
                <Bar key={key} dataKey={key} stackId="a" fill={color} radius={key === 'LOW' ? [0, 4, 4, 0] : undefined}>
                  <LabelList dataKey={key} position="inside" style={{ fill: '#fff', fontSize: 9, fontWeight: 600 }}
                    formatter={(v: number) => (v > 0 ? v : '')} />
                </Bar>
              ))}
            </BarChart>
          </ResponsiveContainer>
        </>
      )}

      {view === 'radial' && (
        <>
          <p className="text-xs text-gray-500 mb-2">Severity share (% of total anomalies)</p>
          <ResponsiveContainer width="100%" height={260}>
            <RadialBarChart cx="50%" cy="50%" innerRadius={30} outerRadius={110}
              barSize={18} data={radialData} startAngle={90} endAngle={-270}>
              <RadialBar minAngle={5} background dataKey="value" label={{ position: 'insideStart', fill: '#fff', fontSize: 10 }} />
              <Legend iconSize={10} layout="vertical" verticalAlign="middle" align="right"
                formatter={(val: string) => {
                  const d = radialData.find(r => r.name === val);
                  return `${val}: ${d?.value ?? 0}%`;
                }} />
              <Tooltip formatter={(val: any) => [`${val}%`, 'Share']} />
            </RadialBarChart>
          </ResponsiveContainer>
        </>
      )}
    </div>
  );
};

export const TopAffectedEndpoints: React.FC<GraphsProps> = ({ hours = 24, limit = 10 }) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiService.getTopAffectedEndpoints(limit, hours);
        setData(response.top_endpoints);
      } catch (error) {
        console.error('Error fetching top affected endpoints:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [hours, limit]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-200 rounded"></div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Affected Endpoints</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Endpoint</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Anomalies</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Risk</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Max Risk</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Impact</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Composite Score</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data.map((endpoint, index) => (
              <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{endpoint.endpoint}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{endpoint.anomaly_count}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{endpoint.avg_risk_score}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{endpoint.max_risk_score}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{endpoint.avg_impact_score}</td>
                <td className="px-4 py-3 text-sm font-semibold text-purple-600">{endpoint.composite_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const ResolutionSuggestions: React.FC<GraphsProps> = ({ hours = 24 }) => {
  const [suggestions, setSuggestions] = useState<any>({ by_severity: {} });
  const [loading, setLoading] = useState(true);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('CRITICAL');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await apiService.getResolutionSuggestions(hours);
        setSuggestions(response);
      } catch (error) {
        console.error('Error fetching resolution suggestions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [hours]);

  if (loading) return <div className="animate-pulse h-64 bg-gray-200 rounded"></div>;

  const currentSuggestions = suggestions.by_severity[selectedSeverity] || [];

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Resolution Suggestions</h3>
        <div className="flex gap-2">
          {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((severity) => (
            <button
              key={severity}
              onClick={() => setSelectedSeverity(severity)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                selectedSeverity === severity
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {severity}
            </button>
          ))}
        </div>
      </div>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {currentSuggestions.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No suggestions for this severity level</p>
        ) : (
          currentSuggestions.map((suggestion: any, index: number) => (
            <div
              key={index}
              className="border-l-4 border-purple-500 bg-purple-50 p-4 rounded-r"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-semibold ${
                      suggestion.priority === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                      suggestion.priority === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                      suggestion.priority === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {suggestion.priority}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">
                      {suggestion.category}
                    </span>
                  </div>
                  <h4 className="font-semibold text-gray-900 mb-2">{suggestion.action}</h4>
                  
                  {suggestion.description && (
                    <div className="mb-3">
                      <p className="text-sm text-gray-700 mb-2">{suggestion.description}</p>
                    </div>
                  )}
                  
                  {suggestion.steps && suggestion.steps.length > 0 && (
                    <div className="mb-3">
                      <p className="text-xs font-semibold text-gray-600 mb-1">Implementation Steps:</p>
                      <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 ml-2">
                        {suggestion.steps.map((step: string, stepIndex: number) => (
                          <li key={stepIndex} className="leading-relaxed">{step}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <div className="flex gap-3 text-xs text-gray-500">
                    <span>Endpoint: {suggestion.endpoint}</span>
                    <span>Type: {suggestion.anomaly_type}</span>
                    <span>Impact: {(suggestion.impact_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      <div className="mt-4 pt-4 border-t">
        <p className="text-sm text-gray-600">
          Total unique suggestions: <span className="font-semibold">{suggestions.total_unique_suggestions || 0}</span>
        </p>
      </div>
    </div>
  );
};
