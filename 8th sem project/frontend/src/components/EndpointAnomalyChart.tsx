import React, { useEffect, useState } from 'react';
import { BarChart, Bar, LineChart, Line, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface AnomalyHistory {
  id: number;
  timestamp: string;
  endpoint: string;
  anomaly_type: string;
  detected_type: string;
  risk_score: number;
  priority: string;
  method: string;
  window_id: number;
  emergency_rank: number;
  is_correctly_detected: boolean;
}

interface EndpointBreakdown {
  endpoint: string;
  count: number;
  avg_risk: number;
  max_risk: number;
  anomaly_types: Record<string, number>;
}

interface RiskTimelineItem {
  timestamp: string;
  risk_score: number;
  endpoint: string;
  anomaly_type: string;
  priority: string;
}

interface EndpointAnomalyChartProps {
  detectionMode: 'live' | 'simulation';
}

const EndpointAnomalyChart: React.FC<EndpointAnomalyChartProps> = ({ detectionMode }) => {
  const [endpointData, setEndpointData] = useState<EndpointBreakdown[]>([]);
  const [riskTimeline, setRiskTimeline] = useState<RiskTimelineItem[]>([]);
  const [anomalyTypeDistribution, setAnomalyTypeDistribution] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnomalyHistory = async () => {
      if (detectionMode !== 'simulation') {
        setLoading(false);
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/simulation/anomaly-history?limit=200');
        const data = await response.json();

        setEndpointData(data.endpoint_breakdown || []);
        setRiskTimeline(data.risk_timeline || []);

        // Convert anomaly type distribution to chart format
        const typeData = Object.entries(data.anomaly_type_distribution || {}).map(([type, count]) => ({
          type,
          count: count as number,
          color: getAnomalyTypeColor(type)
        }));
        setAnomalyTypeDistribution(typeData);

        setLoading(false);
      } catch (error) {
        console.error('Error fetching anomaly history:', error);
        setLoading(false);
      }
    };

    fetchAnomalyHistory();
    
    // Refresh every 3 seconds during simulation
    const interval = setInterval(fetchAnomalyHistory, 3000);
    return () => clearInterval(interval);
  }, [detectionMode]);

  const getAnomalyTypeColor = (type: string): string => {
    const colors: Record<string, string> = {
      'RATE_SPIKE': '#ef4444',
      'PAYLOAD_ABUSE': '#f59e0b',
      'ERROR_BURST': '#dc2626',
      'PARAM_REPETITION': '#8b5cf6',
      'ENDPOINT_FLOOD': '#06b6d4',
      'NORMAL': '#10b981'
    };
    return colors[type] || '#6b7280';
  };

  const getRiskColor = (risk: number): string => {
    if (risk >= 0.8) return '#ef4444'; // Red
    if (risk >= 0.6) return '#f59e0b'; // Orange
    if (risk >= 0.4) return '#eab308'; // Yellow
    return '#10b981'; // Green
  };

  if (detectionMode !== 'simulation') {
    return (
      <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
        <h2 className="text-xl font-bold text-white mb-4">📊 Endpoint Anomaly Analysis</h2>
        <p className="text-dark-muted">Switch to SIMULATION mode to view endpoint-specific anomaly charts</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
        <h2 className="text-xl font-bold text-white mb-4">📊 Endpoint Anomaly Analysis</h2>
        <p className="text-dark-muted">Loading anomaly data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Endpoint Breakdown Chart */}
      <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
        <h2 className="text-xl font-bold text-white mb-4">📊 Anomalies by Virtual Endpoint</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={endpointData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="endpoint" 
              stroke="#9ca3af" 
              style={{ fontSize: '12px' }}
              angle={-15}
              textAnchor="end"
              height={80}
            />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: '1px solid #374151', 
                borderRadius: '8px',
                color: '#fff'
              }}
              formatter={(value: any, name: string) => {
                if (name === 'avg_risk' || name === 'max_risk') {
                  return [Number(value).toFixed(4), name.replace('_', ' ').toUpperCase()];
                }
                return [value, name.toUpperCase()];
              }}
            />
            <Legend />
            <Bar dataKey="count" fill="#3b82f6" name="Anomaly Count" />
            <Bar dataKey="avg_risk" fill="#f59e0b" name="Avg Risk Score" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Risk Score Timeline */}
      <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
        <h2 className="text-xl font-bold text-white mb-4">🚨 Risk Score Timeline (Last 50)</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={riskTimeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="timestamp" 
              stroke="#9ca3af" 
              style={{ fontSize: '10px' }}
              tickFormatter={(value) => new Date(new Date(value).getTime() + (5*60+30)*60000).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}
            />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} domain={[0, 1]} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: '1px solid #374151', 
                borderRadius: '8px',
                color: '#fff'
              }}
              labelFormatter={(value) => new Date(new Date(value).getTime() + (5*60+30)*60000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) + ' IST'}
              formatter={(value: any, name: string, props: any) => {
                if (name === 'risk_score') {
                  return [
                    Number(value).toFixed(4),
                    `Risk Score (${props.payload.endpoint} - ${props.payload.anomaly_type})`
                  ];
                }
                return [value, name];
              }}
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="risk_score" 
              stroke="#ef4444" 
              strokeWidth={2} 
              name="Risk Score"
              dot={{ r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Anomaly Type Distribution */}
      <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
        <h2 className="text-xl font-bold text-white mb-4">🎯 Anomaly Type Distribution</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={anomalyTypeDistribution}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="type" 
              stroke="#9ca3af" 
              style={{ fontSize: '12px' }}
              angle={-15}
              textAnchor="end"
              height={80}
            />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#1f2937', 
                border: '1px solid #374151', 
                borderRadius: '8px',
                color: '#fff'
              }}
            />
            <Bar dataKey="count" name="Detections">
              {anomalyTypeDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        
        {/* Legend */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-2">
          {anomalyTypeDistribution.map((item) => (
            <div key={item.type} className="flex items-center gap-2">
              <div 
                className="w-4 h-4 rounded" 
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-dark-muted">
                {item.type}: <span className="font-bold text-white">{item.count}</span>
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Top Risk Endpoints Summary */}
      <div className="bg-dark-800 rounded-lg p-6 border border-dark-600">
        <h2 className="text-xl font-bold text-white mb-4">⚠️ Top Risk Endpoints</h2>
        <div className="space-y-3">
          {endpointData
            .sort((a, b) => b.max_risk - a.max_risk)
            .slice(0, 5)
            .map((ep, index) => (
              <div key={ep.endpoint} className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="text-2xl font-bold text-dark-muted">#{index + 1}</div>
                  <div>
                    <div className="font-bold text-white">{ep.endpoint}</div>
                    <div className="text-xs text-dark-muted">
                      {ep.count} anomalies detected
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div 
                    className="text-2xl font-bold" 
                    style={{ color: getRiskColor(ep.max_risk) }}
                  >
                    {ep.max_risk.toFixed(4)}
                  </div>
                  <div className="text-xs text-dark-muted">Max Risk</div>
                </div>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default EndpointAnomalyChart;
