"""
Deterministic Anomaly Detection System
Uses strict thresholds and logic to detect anomalies, not random chance.
"""
from typing import Dict, List, Optional
from anomaly_injection import AnomalyType, Severity


class AnomalyDetector:
    """Security-focused anomaly detection for SQL Injection, DDoS, and XSS attacks."""
    
    def detect(self, features: Dict) -> Dict:
        """
        Detect SECURITY ATTACKS ONLY using deterministic logic.
        Returns detection result with anomaly details.
        """
        endpoint = features.get('endpoint', 'unknown')
        
        # Calculate detection metrics
        req_count = features.get('req_count', 0)
        
        # Detect security attacks only
        detections = []
        
        # 1. SQL Injection Detection
        # Check for SQL patterns in query parameters or malicious pattern flag
        has_sql_pattern = features.get('malicious_pattern') == 'SQL_INJECTION'
        sql_keywords = features.get('sql_keywords_count', 0)
        if has_sql_pattern or sql_keywords > 3:
            confidence = 0.95 if has_sql_pattern else min(0.85, 0.5 + sql_keywords * 0.1)
            detections.append({
                'anomaly_type': AnomalyType.SQL_INJECTION.value,
                'severity': Severity.CRITICAL.name,
                'confidence': confidence,
                'metric_value': sql_keywords,
                'threshold': 3
            })
        
        # 2. DDoS Attack Detection
        # Very high traffic from multiple IPs with sustained pattern
        request_rate = features.get('request_count', req_count)
        unique_ips = features.get('unique_ips', 1)
        if request_rate > 200 or (req_count > 100 and unique_ips > 50):
            ratio = request_rate / 200
            confidence = min(0.95, 0.65 + (ratio - 1.0) * 0.2)
            detections.append({
                'anomaly_type': AnomalyType.DDOS_ATTACK.value,
                'severity': Severity.CRITICAL.name,
                'confidence': confidence,
                'metric_value': request_rate,
                'threshold': 200
            })
        
        # 3. XSS Attack Detection
        # Check for XSS patterns in query parameters or malicious pattern flag
        has_xss_pattern = features.get('malicious_pattern') == 'XSS_ATTACK'
        xss_keywords = features.get('xss_keywords_count', 0)
        if has_xss_pattern or xss_keywords > 2:
            confidence = 0.90 if has_xss_pattern else min(0.80, 0.5 + xss_keywords * 0.15)
            detections.append({
                'anomaly_type': AnomalyType.XSS_ATTACK.value,
                'severity': Severity.HIGH.name,
                'confidence': confidence,
                'metric_value': xss_keywords,
                'threshold': 2
            })
        
        # 4. Brute Force Detection
        # High repeated requests from same IP to auth endpoints with high failure rate
        failed_logins = features.get('failed_logins_count', 0)
        has_brute_pattern = features.get('malicious_pattern') == 'BRUTE_FORCE'
        if has_brute_pattern or failed_logins >= 5:
            confidence = 0.93 if has_brute_pattern else min(0.88, 0.55 + failed_logins * 0.07)
            detections.append({
                'anomaly_type': AnomalyType.BRUTE_FORCE.value,
                'severity': Severity.CRITICAL.name,
                'confidence': confidence,
                'metric_value': failed_logins,
                'threshold': 5
            })
        
        # 5. Unauthorized Access Detection
        # Requests with invalid tokens, forbidden paths, or suspicious auth headers
        auth_failures = features.get('auth_failure_count', 0)
        has_unauth_pattern = features.get('malicious_pattern') == 'UNAUTHORIZED_ACCESS'
        if has_unauth_pattern or auth_failures >= 3:
            confidence = 0.87 if has_unauth_pattern else min(0.82, 0.50 + auth_failures * 0.12)
            detections.append({
                'anomaly_type': AnomalyType.UNAUTHORIZED_ACCESS.value,
                'severity': Severity.HIGH.name,
                'confidence': confidence,
                'metric_value': auth_failures,
                'threshold': 3
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
