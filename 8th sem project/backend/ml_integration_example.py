"""
Integration Example: ML Anomaly Detection with Existing System

This script demonstrates how to integrate the ML anomaly detection module
with your existing traffic monitoring backend.

Features demonstrated:
1. Loading models
2. Making predictions for network traffic
3. Making predictions for HTTP requests
4. IP blocking based on predictions
5. Tracking statistics
6. Integration with existing anomaly detection
"""

import numpy as np
import pandas as pd
from typing import Dict, Any
import sys
import os

# Import the ML anomaly detector
from ml_anomaly_detection import MLAnomalyDetector, load_models
from autoencoder_wrapper import create_autoencoder_detector

# Import existing system components (if available)
try:
    from anomaly_detection import AnomalyDetector
    EXISTING_DETECTOR_AVAILABLE = True
except ImportError:
    EXISTING_DETECTOR_AVAILABLE = False
    print("Note: Existing anomaly detector not imported")


class EnhancedAnomalyDetectionSystem:
    """
    Enhanced anomaly detection combining:
    - Existing rule-based detection
    - ML-based detection (CIC IDS 2017 + CSIC 2010)
    """
    
    def __init__(self, models_dir: str = None):
        """
        Initialize enhanced detection system.
        
        Args:
            models_dir: Path to models directory
        """
        print("="*70)
        print("INITIALIZING ENHANCED ANOMALY DETECTION SYSTEM")
        print("="*70 + "\n")
        
        # Load ML detector
        self.ml_detector = MLAnomalyDetector(models_dir)
        self.ml_models_loaded = self.ml_detector.load_models()
        
        # Load existing rule-based detector (if available)
        if EXISTING_DETECTOR_AVAILABLE:
            self.rule_detector = AnomalyDetector()
            print("✓ Rule-based detector loaded")
        else:
            self.rule_detector = None
            print("ℹ Rule-based detector not available")
        
        print("\n" + "="*70)
        print("SYSTEM READY")
        print("="*70 + "\n")
    
    def detect_network_anomaly(
        self, 
        network_features: Dict[str, float],
        use_ml: bool = True,
        use_rules: bool = True
    ) -> Dict[str, Any]:
        """
        Detect network traffic anomaly using combined approach.
        
        Args:
            network_features: Dictionary of network traffic features
            use_ml: Whether to use ML detection
            use_rules: Whether to use rule-based detection
        
        Returns:
            Combined detection results
        """
        results = {
            'ml_detection': None,
            'rule_detection': None,
            'combined_decision': False,
            'confidence': 0.0,
            'method': []
        }
        
        # ML-based detection
        if use_ml and self.ml_models_loaded:
            try:
                # Convert features dict to array
                # Note: Order of features must match training data
                feature_array = np.array(list(network_features.values())).reshape(1, -1)
                
                ml_result = self.ml_detector.predict_anomaly(
                    feature_array, 
                    protocol='network'
                )
                results['ml_detection'] = ml_result
                
                if ml_result['is_anomaly']:
                    results['combined_decision'] = True
                    results['confidence'] = max(results['confidence'], ml_result['confidence'])
                    results['method'].append('ML')
                    
            except Exception as e:
                print(f"Warning: ML detection failed: {e}")
        
        # Rule-based detection
        if use_rules and self.rule_detector is not None:
            try:
                rule_result = self.rule_detector.detect(network_features)
                results['rule_detection'] = rule_result
                
                # Check if any anomalies detected
                if rule_result.get('is_anomaly', False):
                    results['combined_decision'] = True
                    # Combine confidences (take max)
                    rule_confidence = rule_result.get('confidence', 0.5)
                    results['confidence'] = max(results['confidence'], rule_confidence)
                    results['method'].append('Rule-based')
                    
            except Exception as e:
                print(f"Warning: Rule-based detection failed: {e}")
        
        return results
    
    def detect_http_anomaly(
        self, 
        http_features: Dict[str, float],
        use_ml: bool = True
    ) -> Dict[str, Any]:
        """
        Detect HTTP request anomaly using ML models.
        
        Args:
            http_features: Dictionary of HTTP request features
            use_ml: Whether to use ML detection
        
        Returns:
            Detection results
        """
        results = {
            'ml_detection': None,
            'combined_decision': False,
            'confidence': 0.0,
            'method': []
        }
        
        if use_ml and self.ml_models_loaded:
            try:
                # Convert features to array
                feature_array = np.array(list(http_features.values())).reshape(1, -1)
                
                ml_result = self.ml_detector.predict_anomaly(
                    feature_array,
                    protocol='http'
                )
                results['ml_detection'] = ml_result
                
                if ml_result['is_anomaly']:
                    results['combined_decision'] = True
                    results['confidence'] = ml_result['confidence']
                    results['method'].append('ML-HTTP')
                    
            except Exception as e:
                print(f"Warning: HTTP ML detection failed: {e}")
        
        return results
    
    def process_request(
        self,
        ip: str,
        features: Dict[str, float],
        protocol: str = 'network',
        block_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Process a request and decide whether to block the IP.
        
        Args:
            ip: Source IP address
            features: Request features
            protocol: 'network' or 'http'
            block_threshold: Confidence threshold for blocking
        
        Returns:
            Processing results including blocking decision
        """
        # Detect anomaly
        if protocol == 'network':
            detection = self.detect_network_anomaly(features)
        else:
            detection = self.detect_http_anomaly(features)
        
        # Check if IP should be blocked
        blocking_result = None
        if detection['ml_detection'] is not None:
            blocking_result = self.ml_detector.check_and_block_ip(
                ip,
                detection['ml_detection'],
                threshold=block_threshold
            )
        
        return {
            'ip': ip,
            'protocol': protocol,
            'detection': detection,
            'blocking': blocking_result,
            'timestamp': pd.Timestamp.now()
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        ml_stats = self.ml_detector.get_statistics()
        
        return {
            'ml_stats': ml_stats,
            'ml_models_loaded': self.ml_models_loaded,
            'rule_detector_available': self.rule_detector is not None
        }


def example_network_traffic_detection():
    """
    Example: Detecting network traffic anomalies
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: NETWORK TRAFFIC ANOMALY DETECTION")
    print("="*70 + "\n")
    
    # Initialize system
    system = EnhancedAnomalyDetectionSystem()
    
    # Simulate network traffic features
    # Note: These are dummy features - replace with actual network metrics
    network_features = {
        'packet_count': 1500,
        'byte_count': 150000,
        'duration': 60,
        'avg_packet_size': 100,
        'flow_rate': 25,
        'protocol_type': 6,  # TCP
        'src_port': 45678,
        'dst_port': 80,
        'flags': 2,
        'connection_state': 1
    }
    
    # Process request
    result = system.process_request(
        ip='192.168.1.100',
        features=network_features,
        protocol='network',
        block_threshold=0.7
    )
    
    print(f"IP: {result['ip']}")
    print(f"Protocol: {result['protocol']}")
    print(f"Anomaly detected: {result['detection']['combined_decision']}")
    print(f"Confidence: {result['detection']['confidence']:.2%}")
    print(f"Detection method(s): {', '.join(result['detection']['method']) if result['detection']['method'] else 'None'}")
    
    if result['detection']['ml_detection']:
        ml = result['detection']['ml_detection']
        print(f"\nML Detection Details:")
        print(f"  Models voted: {ml['num_models_voted']}")
        print(f"  Ensemble prediction: {ml['ensemble_prediction']}")
        print(f"  Error rate: {ml['error_rate']:.4f}")
        print(f"  Failure probability: {ml['failure_probability']:.4f}")
    
    if result['blocking']:
        print(f"\nBlocking Decision:")
        print(f"  Should block: {result['blocking']['should_block']}")
        print(f"  Is blocked: {result['blocking']['is_blocked']}")
        print(f"  Reason: {result['blocking']['reason']}")
        print(f"  Action: {result['blocking']['action_taken']}")


def example_http_anomaly_detection():
    """
    Example: Detecting HTTP request anomalies
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: HTTP REQUEST ANOMALY DETECTION")
    print("="*70 + "\n")
    
    # Initialize system
    system = EnhancedAnomalyDetectionSystem()
    
    # Simulate HTTP request features
    # Note: These are dummy features - replace with actual HTTP metrics
    http_features = {
        'content_length': 512,
        'num_special_chars': 15,
        'url_length': 120,
        'num_parameters': 3,
        'request_method': 1,  # POST
        'has_script_tags': 0,
        'has_sql_keywords': 0,
        'entropy': 3.5,
        'suspicious_patterns': 0,
        'payload_size': 512
    }
    
    # Process request
    result = system.process_request(
        ip='192.168.1.200',
        features=http_features,
        protocol='http',
        block_threshold=0.6
    )
    
    print(f"IP: {result['ip']}")
    print(f"Protocol: {result['protocol']}")
    print(f"Anomaly detected: {result['detection']['combined_decision']}")
    print(f"Confidence: {result['detection']['confidence']:.2%}")
    
    if result['detection']['ml_detection']:
        ml = result['detection']['ml_detection']
        print(f"\nHTTP ML Detection Details:")
        print(f"  Individual predictions: {ml['individual_predictions']}")
        print(f"  Models voted: {ml['num_models_voted']}")


def example_batch_processing():
    """
    Example: Processing multiple requests and tracking statistics
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: BATCH PROCESSING AND STATISTICS")
    print("="*70 + "\n")
    
    # Initialize system
    system = EnhancedAnomalyDetectionSystem()
    
    # Simulate multiple requests
    requests = [
        {'ip': '192.168.1.10', 'protocol': 'network', 'features': {f'f{i}': np.random.randn() for i in range(10)}},
        {'ip': '192.168.1.20', 'protocol': 'network', 'features': {f'f{i}': np.random.randn() * 3 for i in range(10)}},
        {'ip': '192.168.1.30', 'protocol': 'http', 'features': {f'f{i}': np.random.randn() for i in range(10)}},
        {'ip': '192.168.1.40', 'protocol': 'network', 'features': {f'f{i}': np.random.randn() for i in range(10)}},
        {'ip': '192.168.1.10', 'protocol': 'network', 'features': {f'f{i}': np.random.randn() * 5 for i in range(10)}},
    ]
    
    print(f"Processing {len(requests)} requests...\n")
    
    results = []
    for req in requests:
        result = system.process_request(
            ip=req['ip'],
            features=req['features'],
            protocol=req['protocol']
        )
        results.append(result)
        
        print(f"  {req['ip']} ({req['protocol']}): ", end='')
        if result['detection']['combined_decision']:
            print(f"ANOMALY (confidence: {result['detection']['confidence']:.2%})")
        else:
            print("NORMAL")
    
    # Display statistics
    print("\n" + "-"*70)
    print("SYSTEM STATISTICS")
    print("-"*70)
    stats = system.get_system_stats()
    print(f"ML Models loaded: {stats['ml_models_loaded']}")
    print(f"Total IPs seen: {stats['ml_stats']['total_ips_seen']}")
    print(f"Blocked IPs: {stats['ml_stats']['blocked_ips_count']}")
    print(f"Total predictions: {stats['ml_stats']['total_predictions']}")
    print(f"Anomaly predictions: {stats['ml_stats']['anomaly_predictions']}")
    print(f"Anomaly rate: {stats['ml_stats']['anomaly_rate']:.2%}")
    
    # Show blocked IPs
    blocked_ips = system.ml_detector.get_blocked_ips()
    if blocked_ips:
        print(f"\nBlocked IPs: {', '.join(blocked_ips)}")
    else:
        print(f"\nNo IPs currently blocked")


def example_standalone_functions():
    """
    Example: Using standalone functions
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: STANDALONE FUNCTIONS")
    print("="*70 + "\n")
    
    # Load models using standalone function
    detector = load_models()
    
    if detector.cic_models:
        print("Creating dummy data for testing...")
        
        # Create dummy network data
        dummy_data = np.random.randn(1, 10)
        
        # Predict
        print("\nMaking prediction...")
        result = detector.predict_anomaly(dummy_data, protocol='network')
        
        print(f"Anomaly: {result['is_anomaly']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Models voted: {result['num_models_voted']}")
        
        # Test error rate calculation
        print("\nTesting error rate calculation...")
        y_true = np.array([0, 0, 1, 1, 0, 1, 0, 0])
        y_pred = np.array([0, 1, 1, 0, 0, 1, 0, 0])
        error_rate = detector.calculate_error_rate(y_true, y_pred)
        print(f"Error rate: {error_rate:.2%}")
        
        # Test failure probability calculation
        print("\nTesting failure probability calculation...")
        y_pred_window = np.array([0, 0, 1, 1, 1, 0, 1, 1, 0, 1])
        failure_prob = detector.calculate_failure_probability(y_pred_window)
        print(f"Failure probability: {failure_prob:.2%}")
    else:
        print("No models loaded - skipping prediction tests")


if __name__ == "__main__":
    """
    Run all examples
    """
    print("\n" + "="*70)
    print("ML ANOMALY DETECTION - INTEGRATION EXAMPLES")
    print("="*70)
    
    # Run examples
    try:
        example_network_traffic_detection()
    except Exception as e:
        print(f"Error in example 1: {e}")
    
    try:
        example_http_anomaly_detection()
    except Exception as e:
        print(f"Error in example 2: {e}")
    
    try:
        example_batch_processing()
    except Exception as e:
        print(f"Error in example 3: {e}")
    
    try:
        example_standalone_functions()
    except Exception as e:
        print(f"Error in example 4: {e}")
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70 + "\n")
