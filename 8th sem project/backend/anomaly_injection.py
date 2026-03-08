"""
Deterministic Per-Endpoint Anomaly Injection System
Each endpoint gets exactly ONE specific anomaly type assigned.
"""
from enum import Enum
from typing import Dict, Tuple
from datetime import datetime, timedelta
import random


class AnomalyType(Enum):
    """Security attack types for detection."""
    SQL_INJECTION = "sql_injection"
    DDOS_ATTACK = "ddos_attack"
    XSS_ATTACK = "xss_attack"


class Severity(Enum):
    """Severity levels in strict hierarchy."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


# DETERMINISTIC MAPPING: Each endpoint gets exactly ONE anomaly type
# SIMULATION MODE FOCUSED ON SECURITY ATTACKS: SQL Injection, DDoS, XSS
ENDPOINT_ANOMALY_MAP = {
    # Live endpoints (kept for compatibility)
    '/login': AnomalyType.SQL_INJECTION,
    '/payment': AnomalyType.SQL_INJECTION,
    '/search': AnomalyType.DDOS_ATTACK,
    '/profile': AnomalyType.XSS_ATTACK,
    '/signup': AnomalyType.SQL_INJECTION,
    '/logout': AnomalyType.XSS_ATTACK,
    '/api/users': AnomalyType.DDOS_ATTACK,
    '/api/data': AnomalyType.XSS_ATTACK,
    '/api/posts': AnomalyType.SQL_INJECTION,
    '/api/comments': AnomalyType.XSS_ATTACK,
    # Simulation endpoints - PRIMARY SECURITY ATTACKS ONLY
    '/sim/login': AnomalyType.SQL_INJECTION,
    '/sim/payment': AnomalyType.SQL_INJECTION,
    '/sim/search': AnomalyType.DDOS_ATTACK,
    '/sim/profile': AnomalyType.XSS_ATTACK,
    '/sim/signup': AnomalyType.SQL_INJECTION,
    '/sim/logout': AnomalyType.XSS_ATTACK,
    '/sim/api/users': AnomalyType.DDOS_ATTACK,
    '/sim/api/data': AnomalyType.XSS_ATTACK,
    '/sim/api/posts': AnomalyType.SQL_INJECTION,
    '/sim/api/comments': AnomalyType.XSS_ATTACK,
}


# Anomaly injection parameters per type - SECURITY ATTACKS ONLY
ANOMALY_CONFIGS = {
    AnomalyType.SQL_INJECTION: {
        'malicious_payload_probability': 0.85,  # 85% chance of SQL injection in request
        'duration_seconds': 100,
        'severity': Severity.CRITICAL,
        'impact_score': 0.95,
        'failure_probability': 0.80,
        'description': 'SQL injection attack detected - database compromise attempt',
        'sql_patterns': [
            "' OR '1'='1",
            "'; DROP TABLE users--",
            "' UNION SELECT NULL--",
            "admin'--",
            "1' AND '1'='1"
        ]
    },
    AnomalyType.DDOS_ATTACK: {
        'request_multiplier': 50.0,  # 50x normal traffic (DDoS scale)
        'duration_seconds': 120,
        'severity': Severity.CRITICAL,
        'impact_score': 0.98,
        'failure_probability': 0.90,
        'description': 'Distributed Denial of Service attack - service availability at risk',
        'concurrent_connections': 1000
    },
    AnomalyType.XSS_ATTACK: {
        'malicious_payload_probability': 0.75,  # 75% chance of XSS in request
        'duration_seconds': 90,
        'severity': Severity.HIGH,
        'impact_score': 0.85,
        'failure_probability': 0.65,
        'description': 'Cross-Site Scripting attack detected - client-side injection attempt',
        'xss_patterns': [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="malicious.com">',
            '<body onload=alert("XSS")>'
        ]
    }
}


class AnomalyInjector:
    """Manages deterministic anomaly injection for endpoints."""
    
    def __init__(self):
        self.active_injections: Dict[str, Dict] = {}
        self._initialize_injections()
    
    def _initialize_injections(self):
        """Initialize anomaly injections for all endpoints."""
        current_time = datetime.utcnow()
        
        for endpoint, anomaly_type in ENDPOINT_ANOMALY_MAP.items():
            config = ANOMALY_CONFIGS[anomaly_type]
            
            # Stagger start times so anomalies don't all start at once
            # This creates a more realistic scenario
            start_delay = hash(endpoint) % 30  # 0-29 seconds delay
            
            self.active_injections[endpoint] = {
                'anomaly_type': anomaly_type,
                'config': config,
                'start_time': current_time + timedelta(seconds=start_delay),
                'end_time': current_time + timedelta(seconds=start_delay + config['duration_seconds']),
                'is_active': False,
                'injection_count': 0
            }
    
    def get_anomaly_for_endpoint(self, endpoint: str) -> Tuple[AnomalyType, Dict]:
        """Get the assigned anomaly type and config for an endpoint."""
        if endpoint not in self.active_injections:
            return None, None
        
        injection = self.active_injections[endpoint]
        current_time = datetime.utcnow()
        
        # Check if anomaly should be active
        if injection['start_time'] <= current_time <= injection['end_time']:
            injection['is_active'] = True
            injection['injection_count'] += 1
            return injection['anomaly_type'], injection['config']
        
        injection['is_active'] = False
        return None, None
    
    def is_anomaly_active(self, endpoint: str) -> bool:
        """Check if anomaly is currently active for endpoint."""
        if endpoint not in self.active_injections:
            return False
        
        current_time = datetime.utcnow()
        injection = self.active_injections[endpoint]
        
        return injection['start_time'] <= current_time <= injection['end_time']
    
    def get_injection_status(self) -> Dict:
        """Get status of all injections."""
        current_time = datetime.utcnow()
        status = {}
        
        for endpoint, injection in self.active_injections.items():
            is_active = injection['start_time'] <= current_time <= injection['end_time']
            time_remaining = (injection['end_time'] - current_time).total_seconds() if is_active else 0
            
            status[endpoint] = {
                'anomaly_type': injection['anomaly_type'].value,
                'is_active': is_active,
                'time_remaining_seconds': max(0, time_remaining),
                'injection_count': injection['injection_count'],
                'severity': injection['config']['severity'].name,
                'impact_score': injection['config']['impact_score']
            }
        
        return status
    
    def reset_injections(self):
        """Reset all anomaly injections with new timings."""
        self.active_injections.clear()
        self._initialize_injections()


# Global injector instance
anomaly_injector = AnomalyInjector()


def inject_anomaly_into_log(endpoint: str, base_log: Dict) -> Dict:
    """
    Inject anomaly characteristics into a log entry.
    Returns modified log with anomaly applied if active.
    """
    anomaly_type, config = anomaly_injector.get_anomaly_for_endpoint(endpoint)
    
    if anomaly_type is None:
        return base_log
    
    modified_log = base_log.copy()
    
    # Apply anomaly-specific modifications - SECURITY ATTACKS ONLY
    if anomaly_type == AnomalyType.SQL_INJECTION:
        # Inject SQL injection patterns
        if random.random() < config['malicious_payload_probability']:
            sql_pattern = random.choice(config['sql_patterns'])
            modified_log['query_params'] = modified_log.get('query_params', '') + sql_pattern
            modified_log['payload'] = modified_log.get('payload', '') + sql_pattern
            modified_log['malicious_pattern'] = 'SQL_INJECTION'
            # May cause errors (50% chance)
            if random.random() < 0.5:
                modified_log['status_code'] = random.choice([400, 500, 403])
    
    elif anomaly_type == AnomalyType.DDOS_ATTACK:
        # Mark DDoS characteristics
        modified_log['request_count'] = int(modified_log.get('request_count', 1) * config['request_multiplier'])
        modified_log['concurrent_connections'] = config['concurrent_connections']
        # Service degradation
        modified_log['response_time_ms'] *= 3.0  # 3x slower due to overload
        if random.random() < 0.3:  # 30% of requests fail
            modified_log['status_code'] = random.choice([503, 504, 429])
    
    elif anomaly_type == AnomalyType.XSS_ATTACK:
        # Inject XSS attack patterns
        if random.random() < config['malicious_payload_probability']:
            xss_pattern = random.choice(config['xss_patterns'])
            modified_log['query_params'] = modified_log.get('query_params', '') + xss_pattern
            modified_log['payload'] = modified_log.get('payload', '') + xss_pattern
            modified_log['malicious_pattern'] = 'XSS_ATTACK'
            # Usually gets through (200) but might be blocked
            if random.random() < 0.2:
                modified_log['status_code'] = 403
    
    # Add anomaly metadata
    modified_log['_injected_anomaly'] = {
        'type': anomaly_type.value,
        'severity': config['severity'].name,
        'impact_score': config['impact_score'],
        'failure_probability': config['failure_probability']
    }
    
    return modified_log
