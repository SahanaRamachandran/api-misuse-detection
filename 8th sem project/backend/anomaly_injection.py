"""
Deterministic Per-Endpoint Anomaly Injection System
Each endpoint gets exactly ONE specific anomaly type assigned.
"""
from enum import Enum
from typing import Dict, Tuple
from datetime import datetime, timedelta
import random


class AnomalyType(Enum):
    """Predefined anomaly types for injection."""
    LATENCY_SPIKE = "latency_spike"
    ERROR_SPIKE = "error_spike"
    TIMEOUT = "timeout"
    TRAFFIC_BURST = "traffic_burst"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class Severity(Enum):
    """Severity levels in strict hierarchy."""
    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


# DETERMINISTIC MAPPING: Each endpoint gets exactly ONE anomaly type
# Includes both live and simulation endpoints
ENDPOINT_ANOMALY_MAP = {
    '/login': AnomalyType.ERROR_SPIKE,
    '/payment': AnomalyType.LATENCY_SPIKE,
    '/search': AnomalyType.TRAFFIC_BURST,
    '/profile': AnomalyType.TIMEOUT,
    '/signup': AnomalyType.RESOURCE_EXHAUSTION,
    '/logout': AnomalyType.ERROR_SPIKE,
    # Simulation endpoints (same mapping)
    '/sim/login': AnomalyType.ERROR_SPIKE,
    '/sim/payment': AnomalyType.LATENCY_SPIKE,
    '/sim/search': AnomalyType.TRAFFIC_BURST,
    '/sim/profile': AnomalyType.TIMEOUT,
    '/sim/signup': AnomalyType.RESOURCE_EXHAUSTION,
}


# Anomaly injection parameters per type
ANOMALY_CONFIGS = {
    AnomalyType.LATENCY_SPIKE: {
        'response_time_multiplier': 5.0,  # 5x normal response time
        'duration_seconds': 120,
        'severity': Severity.HIGH,
        'impact_score': 0.75,
        'failure_probability': 0.15,
        'description': 'Response times are 5x higher than baseline'
    },
    AnomalyType.ERROR_SPIKE: {
        'error_rate_threshold': 0.40,  # 40% error rate
        'duration_seconds': 90,
        'severity': Severity.CRITICAL,
        'impact_score': 0.90,
        'failure_probability': 0.60,
        'description': 'Error rate exceeds 40% - immediate action required'
    },
    AnomalyType.TIMEOUT: {
        'timeout_threshold_ms': 5000,  # 5 second timeout
        'duration_seconds': 150,
        'severity': Severity.HIGH,
        'impact_score': 0.80,
        'failure_probability': 0.50,
        'description': 'Requests timing out after 5+ seconds'
    },
    AnomalyType.TRAFFIC_BURST: {
        'request_multiplier': 10.0,  # 10x normal traffic
        'duration_seconds': 60,
        'severity': Severity.MEDIUM,
        'impact_score': 0.60,
        'failure_probability': 0.25,
        'description': 'Traffic volume is 10x above normal baseline'
    },
    AnomalyType.RESOURCE_EXHAUSTION: {
        'payload_multiplier': 8.0,  # 8x normal payload
        'duration_seconds': 180,
        'severity': Severity.CRITICAL,
        'impact_score': 0.95,
        'failure_probability': 0.70,
        'description': 'Memory/bandwidth exhaustion from oversized requests'
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
    
    # Apply anomaly-specific modifications
    if anomaly_type == AnomalyType.LATENCY_SPIKE:
        modified_log['response_time_ms'] *= config['response_time_multiplier']
    
    elif anomaly_type == AnomalyType.ERROR_SPIKE:
        # Force errors
        modified_log['status_code'] = random.choice([500, 503, 504, 429])
    
    elif anomaly_type == AnomalyType.TIMEOUT:
        modified_log['response_time_ms'] = config['timeout_threshold_ms'] + random.uniform(100, 1000)
    
    elif anomaly_type == AnomalyType.TRAFFIC_BURST:
        # Traffic burst handled at request generation level
        # Just mark the log
        pass
    
    elif anomaly_type == AnomalyType.RESOURCE_EXHAUSTION:
        modified_log['payload_size'] = int(modified_log.get('payload_size', 1000) * config['payload_multiplier'])
    
    # Add anomaly metadata
    modified_log['_injected_anomaly'] = {
        'type': anomaly_type.value,
        'severity': config['severity'].name,
        'impact_score': config['impact_score'],
        'failure_probability': config['failure_probability']
    }
    
    return modified_log
