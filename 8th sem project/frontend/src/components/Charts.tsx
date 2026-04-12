import React from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Anomaly } from '../types';

interface ChartsProps {
  anomalies: Anomaly[];
}

const Charts: React.FC<ChartsProps> = ({ anomalies }) => {
  // Risk Score Timeline - Last 50 anomalies
  const riskOverTimeData = anomalies.slice(0, 50).reverse().map((a, index) => ({
    index: index + 1,
    time: new Date(new Date(a.timestamp).getTime() + (5*60+30)*60000).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }),    // IST
    risk: parseFloat((a.risk_score * 1000).toFixed(2)), // Scale for better visibility
    failure: parseFloat((a.failure_probability * 100).toFixed(1)),
  }));

  // Anomalies by Virtual Endpoint
  const endpointCounts = anomalies.reduce((acc, a) => {
    acc[a.endpoint] = (acc[a.endpoint] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const anomaliesByEndpoint = Object.entries(endpointCounts)
    .map(([endpoint, count]) => ({
      endpoint: endpoint.replace('/sim/', ''), // Clean endpoint name
      fullEndpoint: endpoint,
      count,
    }))
    .sort((a, b) => b.count - a.count);

  // Anomaly Type Distribution (from root cause)
  const typeCounts = anomalies.reduce((acc, a) => {
    const rootCause = a.root_cause_analysis?.root_cause || 'Unknown';
    acc[rootCause] = (acc[rootCause] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const typeDistribution = Object.entries(typeCounts).map(([name, value]) => ({
    name,
    value,
  }));

  // Priority Distribution with accurate counts
  const priorityCounts = anomalies.reduce((acc, a) => {
    acc[a.priority] = (acc[a.priority] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const priorityDistribution = [
    { name: 'CRITICAL', value: priorityCounts['CRITICAL'] || 0, color: '#dc2626' },
    { name: 'HIGH', value: priorityCounts['HIGH'] || 0, color: '#ef4444' },
    { name: 'MEDIUM', value: priorityCounts['MEDIUM'] || 0, color: '#f59e0b' },
    { name: 'LOW', value: priorityCounts['LOW'] || 0, color: '#10b981' },
  ].filter(item => item.value > 0); // Only show non-zero priorities

  // Top Risk Endpoints
  const topRiskEndpoints = anomalies
    .reduce((acc, a) => {
      if (!acc[a.endpoint]) {
        acc[a.endpoint] = { endpoint: a.endpoint.replace('/sim/', ''), totalRisk: 0, count: 0 };
      }
      acc[a.endpoint].totalRisk += a.risk_score;
      acc[a.endpoint].count += 1;
      return acc;
    }, {} as Record<string, { endpoint: string; totalRisk: number; count: number }>);

  const topRiskData = Object.values(topRiskEndpoints)
    .map(item => ({
      endpoint: item.endpoint,
      avgRisk: parseFloat((item.totalRisk / item.count).toFixed(3)),
      count: item.count,
    }))
    .sort((a, b) => b.avgRisk - a.avgRisk)
    .slice(0, 5);

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      {/* Risk Score Timeline (Last 50) */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-dark-text">📈 Risk Score Timeline (Last 50)</h3>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={riskOverTimeData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f4a" />
            <XAxis dataKey="index" stroke="#9ca3af" style={{ fontSize: '12px' }} label={{ value: 'Sequence', position: 'insideBottom', offset: -5 }} />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1f3a', border: '1px solid #2a2f4a', borderRadius: '8px' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Legend />
            <Line type="monotone" dataKey="risk" stroke="#3b82f6" strokeWidth={2} name="Risk Score (×1000)" dot={false} />
            <Line type="monotone" dataKey="failure" stroke="#ef4444" strokeWidth={2} name="Failure %" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Anomalies by Virtual Endpoint */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-dark-text">📊 Anomalies by Virtual Endpoint</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={anomaliesByEndpoint}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f4a" />
            <XAxis dataKey="endpoint" stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <YAxis stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1f3a', border: '1px solid #2a2f4a', borderRadius: '8px' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Bar dataKey="count" fill="#3b82f6" name="Anomaly Count" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Anomaly Type Distribution */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-dark-text">🎯 Anomaly Type Distribution</h3>
        <ResponsiveContainer width="100%" height={350}>
          <PieChart>
            <Pie
              data={typeDistribution}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={100}
              fill="#8884d8"
              dataKey="value"
            >
              {typeDistribution.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1f3a', border: '1px solid #2a2f4a', borderRadius: '8px' }}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Top Risk Endpoints */}
      <div className="bg-dark-card rounded-lg border border-dark-border p-6 shadow-lg">
        <h3 className="text-lg font-semibold mb-4 text-dark-text">⚠️ Top Risk Endpoints</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={topRiskData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2f4a" />
            <XAxis type="number" stroke="#9ca3af" style={{ fontSize: '12px' }} />
            <YAxis type="category" dataKey="endpoint" stroke="#9ca3af" style={{ fontSize: '12px' }} width={80} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1a1f3a', border: '1px solid #2a2f4a', borderRadius: '8px' }}
              labelStyle={{ color: '#e5e7eb' }}
            />
            <Bar dataKey="avgRisk" fill="#ef4444" name="Avg Risk Score" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Charts;
