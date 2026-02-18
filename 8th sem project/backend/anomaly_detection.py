"""
Deterministic Anomaly Detection System
Uses strict thresholds and logic to detect anomalies, not random chance.
"""
from typing import Dict, List, Optional
from anomaly_injection import AnomalyType, Severity


class AnomalyDetector:
    """Deterministic anomaly detection based on metric thresholds."""
    
    # Baseline thresholds for normal behavior
    BASELINES = {
        'normal_response_time_ms': 200,
        'normal_error_rate': 0.05,
        'normal_req_per_minute': 10,
        'normal_payload_size': 1500,
    }
    
    # Detection thresholds (multipliers of baseline)
    THRESHOLDS = {
        'latency_spike_multiplier': 3.0,      # 3x normal response time
        'error_spike_threshold': 0.25,         # 25% error rate
        'timeout_threshold_ms': 4000,          # 4 seconds
        'traffic_burst_multiplier': 5.0,       # 5x normal traffic
        'resource_exhaustion_multiplier': 5.0  # 5x normal payload
    }
    
    def detect(self, features: Dict) -> Dict:
        """
        Detect anomalies using deterministic logic.
        Returns detection result with anomaly details.
        """
        endpoint = features.get('endpoint', 'unknown')
        
        # Calculate detection metrics
        avg_response = features.get('avg_response_time', 0)
        error_rate = features.get('error_rate', 0)
        req_count = features.get('req_count', 0)
        payload_mean = features.get('payload_mean', 0)
        
        # Detect each anomaly type
        detections = []
        
        # 1. Latency Spike Detection
        if avg_response > self.BASELINES['normal_response_time_ms'] * self.THRESHOLDS['latency_spike_multiplier']:
            # Normalize confidence: higher excess = higher confidence (0.5-1.0 range)
            ratio = avg_response / (self.BASELINES['normal_response_time_ms'] * self.THRESHOLDS['latency_spike_multiplier'])
            confidence = min(1.0, 0.5 + (ratio - 1.0) * 0.3)  # Scaled confidence
            detections.append({
                'anomaly_type': AnomalyType.LATENCY_SPIKE.value,
                'severity': Severity.HIGH.name,
                'confidence': confidence,
                'metric_value': avg_response,
                'threshold': self.BASELINES['normal_response_time_ms'] * self.THRESHOLDS['latency_spike_multiplier']
            })
        
        # 2. Error Spike Detection
        if error_rate > self.THRESHOLDS['error_spike_threshold']:
            severity = Severity.CRITICAL if error_rate > 0.40 else Severity.HIGH
            ratio = error_rate / self.THRESHOLDS['error_spike_threshold']
            confidence = min(1.0, 0.6 + (ratio - 1.0) * 0.25)  # Scaled confidence
            detections.append({
                'anomaly_type': AnomalyType.ERROR_SPIKE.value,
                'severity': severity.name,
                'confidence': confidence,
                'metric_value': error_rate,
                'threshold': self.THRESHOLDS['error_spike_threshold']
            })
        
        # 3. Timeout Detection
        max_response = features.get('max_response_time', 0)
        if max_response > self.THRESHOLDS['timeout_threshold_ms']:
            ratio = max_response / self.THRESHOLDS['timeout_threshold_ms']
            confidence = min(1.0, 0.55 + (ratio - 1.0) * 0.28)  # Scaled confidence
            detections.append({
                'anomaly_type': AnomalyType.TIMEOUT.value,
                'severity': Severity.HIGH.name,
                'confidence': confidence,
                'metric_value': max_response,
                'threshold': self.THRESHOLDS['timeout_threshold_ms']
            })
        
        # 4. Traffic Burst Detection
        if req_count > self.BASELINES['normal_req_per_minute'] * self.THRESHOLDS['traffic_burst_multiplier']:
            ratio = req_count / (self.BASELINES['normal_req_per_minute'] * self.THRESHOLDS['traffic_burst_multiplier'])
            confidence = min(1.0, 0.45 + (ratio - 1.0) * 0.2)  # Lower confidence for traffic burst
            detections.append({
                'anomaly_type': AnomalyType.TRAFFIC_BURST.value,
                'severity': Severity.MEDIUM.name,
                'confidence': confidence,
                'metric_value': req_count,
                'threshold': self.BASELINES['normal_req_per_minute'] * self.THRESHOLDS['traffic_burst_multiplier']
            })
        
        # 5. Resource Exhaustion Detection
        if payload_mean > self.BASELINES['normal_payload_size'] * self.THRESHOLDS['resource_exhaustion_multiplier']:
            ratio = payload_mean / (self.BASELINES['normal_payload_size'] * self.THRESHOLDS['resource_exhaustion_multiplier'])
            confidence = min(1.0, 0.65 + (ratio - 1.0) * 0.25)  # Higher confidence for resource issues
            detections.append({
                'anomaly_type': AnomalyType.RESOURCE_EXHAUSTION.value,
                'severity': Severity.CRITICAL.name,
                'confidence': confidence,
                'metric_value': payload_mean,
                'threshold': self.BASELINES['normal_payload_size'] * self.THRESHOLDS['resource_exhaustion_multiplier']
            })
        
        # If multiple anomalies detected, pick the most severe
        if detections:
            # Sort by severity rank
            severity_rank = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
            detections.sort(key=lambda x: severity_rank.get(x['severity'], 0), reverse=True)
            primary_detection = detections[0]
            
            return {
                'is_anomaly': True,
                'anomaly_type': primary_detection['anomaly_type'],
                'severity': primary_detection['severity'],
                'confidence': primary_detection['confidence'],
                'all_detections': detections,
                'failure_probability': self._calculate_failure_probability(primary_detection),
                'impact_score': self._calculate_impact_score(primary_detection, features)
            }
        
        return {
            'is_anomaly': False,
            'anomaly_type': None,
            'severity': 'LOW',
            'confidence': 0.0,
            'all_detections': [],
            'failure_probability': 0.0,
            'impact_score': 0.0
        }
    
    def _calculate_failure_probability(self, detection: Dict) -> float:
        """Calculate failure probability based on severity and confidence."""
        severity_scores = {'CRITICAL': 0.85, 'HIGH': 0.60, 'MEDIUM': 0.35, 'LOW': 0.10}
        base_prob = severity_scores.get(detection['severity'], 0.10)
        confidence = detection.get('confidence', 0.5)
        
        return min(1.0, base_prob * confidence)
    
    def _calculate_impact_score(self, detection: Dict, features: Dict) -> float:
        """Calculate impact score based on anomaly type and metrics."""
        severity_scores = {'CRITICAL': 0.75, 'HIGH': 0.55, 'MEDIUM': 0.35, 'LOW': 0.15}
        base_impact = severity_scores.get(detection['severity'], 0.15)
        
        # Adjust based on request volume (more requests = higher impact)
        req_count = features.get('req_count', 1)
        volume_factor = min(1.3, 1.0 + (req_count / 200))
        
        # Adjust based on error rate severity
        error_rate = features.get('error_rate', 0)
        error_factor = 1.0 + min(0.3, error_rate)  # Up to +30% for high errors
        
        # Adjust based on response time (slower = higher impact)
        avg_response = features.get('avg_response_time', 0)
        response_factor = 1.0 + min(0.2, avg_response / 1000)  # Up to +20% for slow responses
        
        # Combine all factors
        total_impact = base_impact * volume_factor * error_factor * response_factor
        
        return min(1.0, total_impact)


# Global detector instance
anomaly_detector = AnomalyDetector()
