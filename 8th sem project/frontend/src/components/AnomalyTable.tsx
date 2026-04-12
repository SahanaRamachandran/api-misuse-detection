import React, { useState, useEffect } from 'react';
import { Anomaly } from '../types';

interface AnomalyTableProps {
  anomalies: Anomaly[];
  title?: string;
}

interface EndpointSuggestion {
  suggestion: string;
  severity: string;
  category: string;
}

const AnomalyTable: React.FC<AnomalyTableProps> = ({ anomalies, title = 'Recent Anomalies with Resolution Suggestions' }) => {
  const [endpointSuggestions, setEndpointSuggestions] = useState<Record<string, EndpointSuggestion[]>>({});

  // Fetch endpoint-specific suggestions for each unique endpoint
  useEffect(() => {
    const fetchSuggestions = async () => {
      const uniqueEndpoints = [...new Set(anomalies.map(a => a.endpoint))];
      const suggestionsMap: Record<string, EndpointSuggestion[]> = {};

      for (const endpoint of uniqueEndpoints) {
        try {
          const response = await fetch(`http://localhost:8000/simulation/start?simulated_endpoint=${endpoint}&duration_seconds=1&requests_per_window=1&anomaly_mode=mixed`, {
            method: 'POST'
          });
          if (response.ok) {
            const result = await response.json();
            suggestionsMap[endpoint] = result.suggestions || [];
          }
        } catch (error) {
          console.error(`Error fetching suggestions for ${endpoint}:`, error);
        }
      }
      setEndpointSuggestions(suggestionsMap);
    };

    if (anomalies.length > 0) {
      fetchSuggestions();
    }
  }, [anomalies]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH':
        return 'text-danger-500 bg-danger-500/20';
      case 'MEDIUM':
        return 'text-warning-500 bg-warning-500/20';
      case 'LOW':
        return 'text-success-500 bg-success-500/20';
      default:
        return 'text-dark-muted bg-dark-border';
    }
  };

  const getClusterName = (cluster: number) => {
    switch (cluster) {
      case 0:
        return 'Normal';
      case 1:
        return 'Heavy';
      case 2:
        return 'Bot-like';
      default:
        return 'Unknown';
    }
  };

  const getSuggestionPriorityColor = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return 'bg-red-600 text-white';
      case 'HIGH':
        return 'bg-orange-600 text-white';
      case 'MEDIUM':
        return 'bg-yellow-600 text-white';
      case 'LOW':
        return 'bg-blue-600 text-white';
      default:
        return 'bg-gray-600 text-white';
    }
  };

  return (
    <div className="bg-dark-card rounded-lg border border-dark-border p-6">
      <h2 className="text-xl font-bold mb-4 text-dark-text">{title}</h2>
      
      {anomalies.length === 0 ? (
        <div className="text-center py-8 text-dark-muted">
          No anomalies detected yet
        </div>
      ) : (
        <div className="space-y-6">
          {anomalies.map((anomaly) => (
            <div key={anomaly.id} className="bg-dark-800 rounded-lg border border-dark-border overflow-hidden">
              {/* Anomaly Header */}
              <div className="bg-dark-700 px-6 py-4 border-b border-dark-border">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className={`px-3 py-1 rounded text-sm font-bold ${getPriorityColor(anomaly.priority)}`}>
                      {anomaly.priority}
                    </span>
                    <span className="text-lg font-mono text-primary-400">
                      {anomaly.endpoint}
                    </span>
                    <span className="px-2 py-1 rounded bg-dark-border text-dark-text text-xs">
                      {anomaly.method}
                    </span>
                    {anomaly.is_anomaly && (
                      <span className="text-danger-500 font-semibold">⚠️ ANOMALY</span>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-dark-muted">
                      {new Date(new Date(anomaly.timestamp).getTime() + (5*60+30)*60000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' })}
                    </div>
                    <div className="text-lg font-bold text-white">
                      Risk: {anomaly.risk_score.toFixed(3)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-6 py-4 border-b border-dark-border">
                <div>
                  <div className="text-xs text-dark-muted">Failure Probability</div>
                  <div className="text-lg font-bold text-white">{(anomaly.failure_probability * 100).toFixed(1)}%</div>
                </div>
                <div>
                  <div className="text-xs text-dark-muted">Usage Cluster</div>
                  <div className="text-lg font-bold text-white">{getClusterName(anomaly.usage_cluster)}</div>
                </div>
                <div>
                  <div className="text-xs text-dark-muted">Avg Response Time</div>
                  <div className="text-lg font-bold text-white">{anomaly.avg_response_time.toFixed(0)}ms</div>
                </div>
                <div>
                  <div className="text-xs text-dark-muted">Error Rate</div>
                  <div className="text-lg font-bold text-white">{(anomaly.error_rate * 100).toFixed(1)}%</div>
                </div>
              </div>

              {/* Resolution Suggestions Section - ALWAYS VISIBLE */}
              {anomaly.root_cause_analysis && (
                <div className="px-6 py-6 bg-gradient-to-br from-dark-900 to-dark-800">
                  {/* Root Cause Header */}
                  <div className="flex items-center justify-between mb-6 pb-4 border-b border-primary-500/30">
                    <div>
                      <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        🔍 Root Cause Analysis
                      </h3>
                      <p className="text-sm text-dark-muted mt-1">
                        Advanced diagnostics and actionable resolution steps
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-danger-400">
                        {anomaly.root_cause_analysis.root_cause}
                      </div>
                      <div className="text-sm text-dark-muted">
                        Confidence: {(anomaly.root_cause_analysis.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* Detailed Metrics Summary */}
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
                    <div className="bg-dark-700/50 rounded-lg p-3 border border-dark-border">
                      <div className="text-xs text-dark-muted mb-1">Error Rate</div>
                      <div className="text-lg font-bold text-danger-400">
                        {(anomaly.root_cause_analysis.metrics_summary.error_rate * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-dark-700/50 rounded-lg p-3 border border-dark-border">
                      <div className="text-xs text-dark-muted mb-1">Avg Response</div>
                      <div className="text-lg font-bold text-warning-400">
                        {anomaly.root_cause_analysis.metrics_summary.avg_response_time_ms.toFixed(0)}ms
                      </div>
                    </div>
                    <div className="bg-dark-700/50 rounded-lg p-3 border border-dark-border">
                      <div className="text-xs text-dark-muted mb-1">Request Count</div>
                      <div className="text-lg font-bold text-primary-400">
                        {anomaly.root_cause_analysis.metrics_summary.req_count}
                      </div>
                    </div>
                    <div className="bg-dark-700/50 rounded-lg p-3 border border-dark-border">
                      <div className="text-xs text-dark-muted mb-1">Repeat Rate</div>
                      <div className="text-lg font-bold text-warning-400">
                        {(anomaly.root_cause_analysis.metrics_summary.repeat_rate * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="bg-dark-700/50 rounded-lg p-3 border border-dark-border">
                      <div className="text-xs text-dark-muted mb-1">Cluster Type</div>
                      <div className="text-lg font-bold text-primary-400">
                        {getClusterName(anomaly.root_cause_analysis.metrics_summary.usage_cluster)}
                      </div>
                    </div>
                    <div className="bg-dark-700/50 rounded-lg p-3 border border-dark-border">
                      <div className="text-xs text-dark-muted mb-1">Failure Prob</div>
                      <div className="text-lg font-bold text-danger-400">
                        {(anomaly.root_cause_analysis.metrics_summary.failure_probability * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>

                  {/* Conditions Met */}
                  {anomaly.root_cause_analysis.conditions_met.length > 0 && (
                    <div className="mb-6 bg-warning-900/20 border border-warning-500/30 rounded-lg p-4">
                      <div className="text-sm font-semibold text-warning-400 mb-3 flex items-center gap-2">
                        ⚡ Detected Conditions ({anomaly.root_cause_analysis.conditions_met.length})
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {anomaly.root_cause_analysis.conditions_met.map((condition, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1.5 rounded-full bg-warning-600/30 text-warning-300 text-sm font-medium border border-warning-500/40"
                          >
                            {condition.replace(/_/g, ' ').toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Resolution Suggestions - Endpoint-Specific */}
                  <div>
                    <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      💡 Endpoint-Specific Suggestions for {anomaly.endpoint}
                    </h4>
                    {endpointSuggestions[anomaly.endpoint] && endpointSuggestions[anomaly.endpoint].length > 0 ? (
                      <div className="space-y-3">
                        {endpointSuggestions[anomaly.endpoint].map((suggestion, idx) => (
                          <div
                            key={idx}
                            className={`p-4 rounded-lg border-l-4 ${
                              suggestion.severity === 'CRITICAL' ? 'bg-danger-900/20 border-danger-500' :
                              suggestion.severity === 'HIGH' ? 'bg-warning-900/20 border-warning-500' :
                              suggestion.severity === 'MEDIUM' ? 'bg-yellow-900/20 border-yellow-500' :
                              'bg-blue-900/20 border-blue-500'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className={`px-2 py-1 text-xs font-bold rounded ${
                                    suggestion.severity === 'CRITICAL' ? 'bg-danger-600 text-white' :
                                    suggestion.severity === 'HIGH' ? 'bg-warning-600 text-white' :
                                    suggestion.severity === 'MEDIUM' ? 'bg-yellow-600 text-white' :
                                    'bg-blue-600 text-white'
                                  }`}>
                                    {suggestion.severity}
                                  </span>
                                  <span className="text-xs text-dark-muted px-2 py-1 bg-dark-700 rounded">
                                    {suggestion.category}
                                  </span>
                                </div>
                                <p className="text-white">{suggestion.suggestion}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-dark-muted text-sm bg-dark-700 rounded-lg p-4">
                        Loading endpoint-specific suggestions...
                      </div>
                    )}
                  </div>

                  {/* Generic Resolution Suggestions - Keep as fallback */}
                  {anomaly.root_cause_analysis.resolution_suggestions.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        🔧 Generic Resolution Steps ({anomaly.root_cause_analysis.resolution_suggestions.length})
                      </h4>
                      <div className="space-y-3">
                        {anomaly.root_cause_analysis.resolution_suggestions.map((suggestion, idx) => (
                          <div
                            key={idx}
                            className="bg-dark-700/80 rounded-lg p-5 border-l-4 border-primary-500 hover:bg-dark-700 transition-all hover:shadow-lg hover:shadow-primary-500/10"
                          >
                            <div className="flex items-start gap-4">
                              <div className="flex-shrink-0 mt-1">
                                <div className="text-3xl">
                                  {idx === 0 ? '🎯' : idx === 1 ? '⚡' : idx === 2 ? '🔧' : '💪'}
                                </div>
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-3 mb-2">
                                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${getSuggestionPriorityColor(suggestion.priority)}`}>
                                    {suggestion.priority}
                                  </span>
                                  <span className="text-sm font-semibold text-primary-400 uppercase tracking-wide">
                                    {suggestion.category}
                                  </span>
                                </div>
                                <div className="text-lg font-bold text-white mb-2">
                                  {suggestion.action}
                                </div>
                                <div className="text-sm text-dark-muted leading-relaxed">
                                  {suggestion.detail}
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Implementation Guidance */}
                  <div className="mt-6 bg-blue-900/20 border border-blue-500/30 rounded-lg p-5">
                    <div className="flex items-start gap-3">
                      <div className="text-3xl flex-shrink-0">ℹ️</div>
                      <div className="flex-1">
                        <div className="text-base font-semibold text-blue-400 mb-2">
                          📋 Implementation Guidance
                        </div>
                        <div className="text-sm text-dark-muted leading-relaxed">
                          These suggestions are <strong className="text-blue-300">prioritized based on root cause severity</strong> and system impact.
                          Implement <span className="text-red-400 font-bold">CRITICAL</span> and <span className="text-orange-400 font-bold">HIGH</span> priority 
                          actions <strong className="text-blue-300">immediately</strong> to mitigate the anomaly. 
                          Consult your infrastructure team for deployment-specific adjustments.
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AnomalyTable;
