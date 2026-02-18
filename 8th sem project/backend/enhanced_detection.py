"""
Enhanced Anomaly Detection System

Improves detection of weak signals and adversarial attacks through:
1. Adaptive thresholds based on traffic patterns
2. Multi-window temporal analysis
3. Statistical anomaly scoring
4. Behavioral baseline learning
5. Ensemble voting with increased sensitivity

Goal: Increase weak signal detection from 60-70% to 85-90%
      Increase adversarial detection from 40-60% to 70-80%
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import deque, defaultdict
from scipy import stats
import warnings
warnings.filterwarnings('ignore')


class EnhancedAnomalyDetector:
    """
    Advanced anomaly detection with adaptive sensitivity for weak signals.
    """
    
    def __init__(self, sensitivity_mode: str = 'balanced'):
        """
        Initialize enhanced detector.
        
        Args:
            sensitivity_mode: 'high' (catch more), 'balanced', 'conservative' (fewer false positives)
        """
        self.sensitivity_mode = sensitivity_mode
        
        # Adaptive thresholds - more sensitive than basic detector
        self.thresholds = self._get_thresholds(sensitivity_mode)
        
        # Baseline learning - tracks normal behavior per endpoint
        self.baselines = defaultdict(lambda: {
            'response_times': deque(maxlen=1000),
            'error_rates': deque(maxlen=100),
            'payload_sizes': deque(maxlen=1000),
            'request_intervals': deque(maxlen=500),
            'last_update': None
        })
        
        # Multi-window temporal analysis
        self.temporal_windows = {
            'short': deque(maxlen=10),   # Last 10 seconds
            'medium': deque(maxlen=60),  # Last minute
            'long': deque(maxlen=300)    # Last 5 minutes
        }
        
        # Adversarial pattern detection
        self.adversarial_patterns = {
            'timing_patterns': deque(maxlen=100),
            'payload_patterns': deque(maxlen=100),
            'error_sequences': deque(maxlen=50)
        }
        
    def _get_thresholds(self, mode: str) -> Dict:
        """Get sensitivity-adjusted thresholds."""
        base_thresholds = {
            'conservative': {
                'latency_multiplier': 4.0,      # Only flag 4x+ latency
                'error_rate': 0.35,             # 35%+ errors
                'payload_multiplier': 6.0,      # 6x payload
                'z_score': 3.0,                 # 3 std deviations
                'micro_spike_threshold': 0.15,  # 15% micro-changes
            },
            'balanced': {
                'latency_multiplier': 2.5,      # Flag 2.5x+ latency
                'error_rate': 0.20,             # 20%+ errors
                'payload_multiplier': 4.0,      # 4x payload
                'z_score': 2.5,                 # 2.5 std deviations
                'micro_spike_threshold': 0.10,  # 10% micro-changes
            },
            'high': {
                'latency_multiplier': 1.8,      # Flag 1.8x+ latency (WEAK SIGNALS)
                'error_rate': 0.12,             # 12%+ errors (WEAK SIGNALS)
                'payload_multiplier': 2.5,      # 2.5x payload
                'z_score': 2.0,                 # 2 std deviations (more sensitive)
                'micro_spike_threshold': 0.08,  # 8% micro-changes
            }
        }
        return base_thresholds.get(mode, base_thresholds['balanced'])
    
    def update_baseline(self, endpoint: str, features: Dict) -> None:
        """
        Update learned baseline for an endpoint.
        Critical for detecting subtle deviations.
        """
        baseline = self.baselines[endpoint]
        
        # Track normal behavior
        if features.get('avg_response_time'):
            baseline['response_times'].append(features['avg_response_time'])
        
        if features.get('error_rate') is not None:
            baseline['error_rates'].append(features['error_rate'])
        
        if features.get('payload_mean'):
            baseline['payload_sizes'].append(features['payload_mean'])
        
        baseline['last_update'] = datetime.utcnow()
    
    def detect_weak_signal(self, endpoint: str, features: Dict) -> Dict:
        """
        Detect subtle anomalies using statistical analysis.
        
        IMPROVEMENT: Uses Z-score, percentile analysis, and trend detection
        Target: 85-90% detection for weak signals
        """
        baseline = self.baselines[endpoint]
        detections = []
        
        # 1. Z-Score Analysis (statistical deviation)
        if len(baseline['response_times']) >= 30:
            response_times = list(baseline['response_times'])
            mean_rt = np.mean(response_times)
            std_rt = np.std(response_times)
            
            current_rt = features.get('avg_response_time', 0)
            
            if std_rt > 0:
                z_score = abs((current_rt - mean_rt) / std_rt)
                
                # Flag if beyond threshold
                if z_score > self.thresholds['z_score']:
                    confidence = min(0.95, 0.50 + (z_score / 10))
                    detections.append({
                        'type': 'subtle_latency_deviation',
                        'severity': 'MEDIUM' if z_score > 3 else 'LOW',
                        'confidence': confidence,
                        'evidence': f'Z-score: {z_score:.2f}, {z_score}σ from baseline',
                        'metric': 'response_time',
                        'current': current_rt,
                        'baseline_mean': mean_rt,
                        'baseline_std': std_rt
                    })
        
        # 2. Percentile-Based Detection (outlier detection)
        if len(baseline['response_times']) >= 50:
            response_times = list(baseline['response_times'])
            p95 = np.percentile(response_times, 95)
            p99 = np.percentile(response_times, 99)
            
            current_rt = features.get('avg_response_time', 0)
            
            if current_rt > p99:
                detections.append({
                    'type': 'extreme_outlier',
                    'severity': 'HIGH',
                    'confidence': 0.85,
                    'evidence': f'Above 99th percentile (p99={p99:.1f}ms)',
                    'metric': 'response_time',
                    'current': current_rt
                })
            elif current_rt > p95:
                detections.append({
                    'type': 'moderate_outlier',
                    'severity': 'MEDIUM',
                    'confidence': 0.70,
                    'evidence': f'Above 95th percentile (p95={p95:.1f}ms)',
                    'metric': 'response_time',
                    'current': current_rt
                })
        
        # 3. Micro-Spike Detection (small but significant changes)
        if len(baseline['error_rates']) >= 20:
            error_rates = list(baseline['error_rates'])
            baseline_error = np.mean(error_rates)
            current_error = features.get('error_rate', 0)
            
            # Detect small increases
            if current_error > baseline_error * (1 + self.thresholds['micro_spike_threshold']):
                increase_pct = ((current_error - baseline_error) / (baseline_error + 0.001)) * 100
                detections.append({
                    'type': 'micro_error_spike',
                    'severity': 'MEDIUM' if increase_pct > 25 else 'LOW',
                    'confidence': min(0.80, 0.55 + (increase_pct / 200)),
                    'evidence': f'Error rate +{increase_pct:.1f}% from baseline',
                    'metric': 'error_rate',
                    'current': current_error,
                    'baseline': baseline_error
                })
        
        # 4. Trend Analysis (gradual degradation)
        if len(baseline['response_times']) >= 50:
            recent_window = list(baseline['response_times'])[-20:]
            older_window = list(baseline['response_times'])[-50:-30]
            
            if len(older_window) >= 10 and len(recent_window) >= 10:
                recent_mean = np.mean(recent_window)
                older_mean = np.mean(older_window)
                
                # Detect upward trend
                if recent_mean > older_mean * 1.15:  # 15% increase
                    detections.append({
                        'type': 'gradual_degradation',
                        'severity': 'MEDIUM',
                        'confidence': 0.75,
                        'evidence': f'Response time trending up: {older_mean:.1f}ms → {recent_mean:.1f}ms',
                        'metric': 'trend_analysis',
                        'increase_pct': ((recent_mean - older_mean) / older_mean) * 100
                    })
        
        return self._consolidate_detections(detections)
    
    def detect_adversarial(self, features: Dict, metadata: Dict = None) -> Dict:
        """
        Detect adversarial attacks designed to evade detection.
        
        IMPROVEMENT: Pattern analysis, timing analysis, behavioral fingerprinting
        Target: 70-80% detection for adversarial attacks
        """
        detections = []
        metadata = metadata or {}
        
        # 1. Timing Pattern Analysis (bots have regular intervals)
        request_interval = metadata.get('request_interval', 0)
        if request_interval > 0:
            self.adversarial_patterns['timing_patterns'].append(request_interval)
            
            if len(self.adversarial_patterns['timing_patterns']) >= 10:
                intervals = list(self.adversarial_patterns['timing_patterns'])
                std_dev = np.std(intervals)
                
                # Very regular intervals = bot behavior
                if std_dev < 0.1:  # Less than 100ms variation
                    detections.append({
                        'type': 'bot_timing_pattern',
                        'severity': 'HIGH',
                        'confidence': 0.78,
                        'evidence': f'Highly regular intervals (std={std_dev:.2f}s)',
                        'metric': 'timing_regularity'
                    })
        
        # 2. Payload Size Consistency (crafted attacks have consistent payloads)
        payload_size = features.get('payload_mean', 0)
        if payload_size > 0:
            self.adversarial_patterns['payload_patterns'].append(payload_size)
            
            if len(self.adversarial_patterns['payload_patterns']) >= 15:
                payloads = list(self.adversarial_patterns['payload_patterns'])
                payload_variance = np.var(payloads)
                
                # Suspiciously consistent payloads
                if payload_variance < 100:  # Very low variance
                    detections.append({
                        'type': 'consistent_payload_attack',
                        'severity': 'MEDIUM',
                        'confidence': 0.72,
                        'evidence': f'Abnormally consistent payload sizes (var={payload_variance:.1f})',
                        'metric': 'payload_consistency'
                    })
        
        # 3. Error Sequence Analysis (scanning creates error patterns)
        error_rate = features.get('error_rate', 0)
        self.adversarial_patterns['error_sequences'].append(error_rate)
        
        if len(self.adversarial_patterns['error_sequences']) >= 10:
            errors = list(self.adversarial_patterns['error_sequences'])
            
            # Count error spikes
            threshold = 0.15
            spike_count = sum(1 for e in errors if e > threshold)
            
            # Multiple error spikes = scanning/probing
            if spike_count >= 5:
                detections.append({
                    'type': 'scanning_pattern',
                    'severity': 'HIGH',
                    'confidence': 0.82,
                    'evidence': f'{spike_count}/10 windows with elevated errors',
                    'metric': 'error_pattern'
                })
        
        # 4. Just-Below-Threshold Attacks (adversarial evasion)
        # These stay JUST under detection thresholds
        avg_response = features.get('avg_response_time', 0)
        error_rate = features.get('error_rate', 0)
        
        # Check if metrics are suspiciously close to thresholds
        latency_threshold = 200 * self.thresholds['latency_multiplier']
        error_threshold = self.thresholds['error_rate']
        
        suspicious_proximity = 0
        
        if 0.85 * latency_threshold < avg_response < 0.98 * latency_threshold:
            suspicious_proximity += 1
        
        if 0.85 * error_threshold < error_rate < 0.98 * error_threshold:
            suspicious_proximity += 1
        
        if suspicious_proximity >= 2:
            detections.append({
                'type': 'threshold_evasion',
                'severity': 'HIGH',
                'confidence': 0.75,
                'evidence': 'Multiple metrics hovering just below detection thresholds',
                'metric': 'evasion_pattern'
            })
        
        # 5. User-Agent Entropy (bots have low entropy)
        ua_entropy = features.get('user_agent_entropy', 2.0)
        if ua_entropy < 0.8:
            detections.append({
                'type': 'low_entropy_user_agent',
                'severity': 'MEDIUM',
                'confidence': 0.68,
                'evidence': f'Low user-agent diversity (entropy={ua_entropy:.2f})',
                'metric': 'user_agent'
            })
        
        return self._consolidate_detections(detections)
    
    def detect_combined(self, endpoint: str, features: Dict, metadata: Dict = None) -> Dict:
        """
        Combined detection using all enhancement techniques.
        
        Returns best detection result from all methods.
        """
        # Run all detection methods
        weak_signal_result = self.detect_weak_signal(endpoint, features)
        adversarial_result = self.detect_adversarial(features, metadata)
        
        # Update baseline for future comparisons
        if not weak_signal_result['is_anomaly'] and not adversarial_result['is_anomaly']:
            self.update_baseline(endpoint, features)
        
        # Combine results - return highest severity
        if weak_signal_result['is_anomaly'] or adversarial_result['is_anomaly']:
            # Choose detection with higher confidence
            if weak_signal_result.get('confidence', 0) >= adversarial_result.get('confidence', 0):
                return weak_signal_result
            else:
                return adversarial_result
        
        return {'is_anomaly': False, 'confidence': 0.0}
    
    def _consolidate_detections(self, detections: List[Dict]) -> Dict:
        """Consolidate multiple detections into single result."""
        if not detections:
            return {
                'is_anomaly': False,
                'confidence': 0.0,
                'all_detections': []
            }
        
        # Sort by severity and confidence
        severity_order = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        detections.sort(
            key=lambda x: (severity_order.get(x['severity'], 0), x['confidence']),
            reverse=True
        )
        
        primary = detections[0]
        
        return {
            'is_anomaly': True,
            'anomaly_type': primary['type'],
            'severity': primary['severity'],
            'confidence': primary['confidence'],
            'evidence': primary['evidence'],
            'metric': primary.get('metric', 'unknown'),
            'all_detections': detections
        }
    
    def set_sensitivity(self, mode: str) -> None:
        """Dynamically adjust sensitivity."""
        if mode in ['high', 'balanced', 'conservative']:
            self.sensitivity_mode = mode
            self.thresholds = self._get_thresholds(mode)
            print(f"[ENHANCED DETECTOR] Sensitivity set to: {mode}")


# Demo function
if __name__ == "__main__":
    print("=" * 80)
    print("ENHANCED ANOMALY DETECTION - WEAK SIGNAL & ADVERSARIAL DETECTION")
    print("=" * 80)
    
    detector = EnhancedAnomalyDetector(sensitivity_mode='high')
    
    # Test 1: Weak Signal Detection
    print("\n[TEST 1] Weak Signal Detection")
    print("-" * 80)
    
    # Build baseline with normal traffic
    for i in range(50):
        normal_features = {
            'avg_response_time': np.random.normal(200, 20),
            'error_rate': np.random.normal(0.05, 0.02),
            'payload_mean': np.random.normal(1500, 100)
        }
        detector.update_baseline('/api/users', normal_features)
    
    # Test subtle anomaly (only 30% slower)
    weak_signal = {
        'avg_response_time': 260,  # 30% increase - SUBTLE!
        'error_rate': 0.08,        # Small increase
        'payload_mean': 1600
    }
    
    result = detector.detect_weak_signal('/api/users', weak_signal)
    print(f"Weak Signal Detection: {result.get('is_anomaly', False)}")
    if result['is_anomaly']:
        print(f"  Type: {result['anomaly_type']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Evidence: {result['evidence']}")
    
    # Test 2: Adversarial Detection
    print("\n[TEST 2] Adversarial Attack Detection")
    print("-" * 80)
    
    # Simulate bot with regular timing
    for i in range(15):
        metadata = {'request_interval': 1.0}  # Exactly 1 second apart
        features = {
            'avg_response_time': 280,
            'error_rate': 0.18,  # Just below 20% threshold
            'payload_mean': 1200,
            'user_agent_entropy': 0.3  # Low diversity
        }
        result = detector.detect_adversarial(features, metadata)
    
    if result.get('is_anomaly'):
        print(f"Adversarial Detection: DETECTED")
        print(f"  Type: {result['anomaly_type']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Evidence: {result['evidence']}")
    
    print("\n" + "=" * 80)
    print("✅ Enhanced detection ready!")
    print("   - Weak signal detection: Z-score + percentile + trend analysis")
    print("   - Adversarial detection: Timing patterns + payload consistency")
    print("=" * 80)
