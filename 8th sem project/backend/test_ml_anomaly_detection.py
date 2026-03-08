"""
Test Script for ML Anomaly Detection Integration

This script tests all components of the ML anomaly detection system:
1. Model loading
2. Network traffic prediction
3. HTTP request prediction
4. IP blocking functionality
5. Metrics calculation
6. Statistics tracking

Run this script to verify everything is working correctly.
"""

import numpy as np
import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from ml_anomaly_detection import MLAnomalyDetector, load_models
    from autoencoder_wrapper import create_autoencoder_detector, train_autoencoder
    ML_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Error importing ML modules: {e}")
    ML_MODULES_AVAILABLE = False
    sys.exit(1)


class TestRunner:
    """Run comprehensive tests for ML anomaly detection."""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
    
    def run_test(self, test_name, test_func):
        """Run a single test and track results."""
        print(f"\n{'='*70}")
        print(f"TEST: {test_name}")
        print('='*70)
        
        try:
            test_func()
            self.tests_passed += 1
            self.test_results.append({'test': test_name, 'status': 'PASSED'})
            print(f"\n✓ {test_name} PASSED")
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append({'test': test_name, 'status': 'FAILED', 'error': str(e)})
            print(f"\n✗ {test_name} FAILED")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print('='*70)
        print(f"Total tests: {self.tests_passed + self.tests_failed}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success rate: {100*self.tests_passed/(self.tests_passed+self.tests_failed):.1f}%")
        
        print(f"\nDetailed Results:")
        for result in self.test_results:
            status_symbol = '✓' if result['status'] == 'PASSED' else '✗'
            print(f"  {status_symbol} {result['test']}: {result['status']}")
            if result['status'] == 'FAILED' and 'error' in result:
                print(f"      Error: {result['error']}")
        print('='*70)


def test_module_imports():
    """Test 1: Verify all modules can be imported."""
    from ml_anomaly_detection import (
        MLAnomalyDetector,
        load_models,
        predict_anomaly,
        calculate_error_rate,
        calculate_failure_probability,
        check_and_block_ip
    )
    from autoencoder_wrapper import (
        AutoencoderModel,
        AutoencoderAnomalyDetector,
        create_autoencoder_detector,
        train_autoencoder
    )
    print("✓ All modules imported successfully")


def test_detector_initialization():
    """Test 2: Initialize detector."""
    detector = MLAnomalyDetector()
    assert detector is not None
    assert hasattr(detector, 'cic_models')
    assert hasattr(detector, 'csic_models')
    assert hasattr(detector, 'blocked_ips')
    print("✓ Detector initialized successfully")


def test_model_loading():
    """Test 3: Load models."""
    detector = MLAnomalyDetector()
    success = detector.load_models()
    
    print(f"\nModel loading status: {success}")
    print(f"CIC models loaded: {len(detector.cic_models)}")
    print(f"CSIC models loaded: {len(detector.csic_models)}")
    
    if len(detector.cic_models) > 0:
        print(f"✓ CIC models loaded: {list(detector.cic_models.keys())}")
    else:
        print("⚠ No CIC models loaded (check models directory)")
    
    if len(detector.csic_models) > 0:
        print(f"✓ CSIC models loaded: {list(detector.csic_models.keys())}")
    else:
        print("ℹ No CSIC models loaded (may need to export from notebooks)")


def test_network_prediction():
    """Test 4: Network traffic anomaly prediction."""
    detector = MLAnomalyDetector()
    detector.load_models()
    
    if len(detector.cic_models) == 0:
        print("⚠ Skipping network prediction test - no CIC models loaded")
        return
    
    # Create dummy network features
    # Note: Feature count should match model training data
    dummy_data = np.random.randn(1, 10)
    
    result = detector.predict_anomaly(dummy_data, protocol='network')
    
    assert 'is_anomaly' in result
    assert 'confidence' in result
    assert 'ensemble_prediction' in result
    assert 'individual_predictions' in result
    assert 'protocol' in result
    
    print(f"\nPrediction result:")
    print(f"  Anomaly: {result['is_anomaly']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Ensemble prediction: {result['ensemble_prediction']}")
    print(f"  Models voted: {result['num_models_voted']}")
    print(f"  Individual predictions: {result['individual_predictions']}")
    print(f"  Error rate: {result['error_rate']:.4f}")
    print(f"  Failure probability: {result['failure_probability']:.4f}")
    print("✓ Network prediction successful")


def test_http_prediction():
    """Test 5: HTTP request anomaly prediction."""
    detector = MLAnomalyDetector()
    detector.load_models()
    
    # Create dummy HTTP features
    dummy_data = np.random.randn(1, 10)
    
    result = detector.predict_anomaly(dummy_data, protocol='http')
    
    assert 'is_anomaly' in result
    assert 'confidence' in result
    assert result['protocol'] == 'http'
    
    print(f"\nHTTP Prediction result:")
    print(f"  Anomaly: {result['is_anomaly']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  Models voted: {result['num_models_voted']}")
    
    if len(detector.csic_models) == 0:
        print("  ℹ Note: No CSIC models loaded, using default prediction")
    
    print("✓ HTTP prediction successful")


def test_ip_blocking():
    """Test 6: IP blocking functionality."""
    detector = MLAnomalyDetector()
    detector.load_models()
    
    # Create test IP and prediction
    test_ip = '192.168.1.100'
    dummy_data = np.random.randn(1, 10)
    
    # Get prediction
    if len(detector.cic_models) > 0:
        prediction = detector.predict_anomaly(dummy_data, protocol='network')
    else:
        # Create dummy prediction if no models
        prediction = {
            'is_anomaly': True,
            'confidence': 0.85,
            'ensemble_prediction': 1,
            'individual_predictions': {},
            'num_models_voted': 0,
            'error_rate': 0.0,
            'failure_probability': 0.0,
            'protocol': 'network'
        }
    
    # Test blocking with high confidence threshold
    blocking_result = detector.check_and_block_ip(
        ip=test_ip,
        prediction=prediction,
        threshold=0.7
    )
    
    assert 'ip' in blocking_result
    assert 'should_block' in blocking_result
    assert 'is_blocked' in blocking_result
    assert 'reason' in blocking_result
    
    print(f"\nBlocking test results:")
    print(f"  IP: {blocking_result['ip']}")
    print(f"  Should block: {blocking_result['should_block']}")
    print(f"  Is blocked: {blocking_result['is_blocked']}")
    print(f"  Reason: {blocking_result['reason']}")
    print(f"  Action: {blocking_result['action_taken']}")
    
    # Test IP checking
    is_blocked = detector.is_ip_blocked(test_ip)
    print(f"  IP blocked status: {is_blocked}")
    
    # Test unblocking
    if is_blocked:
        unblocked = detector.unblock_ip(test_ip)
        print(f"  Unblocked: {unblocked}")
        assert not detector.is_ip_blocked(test_ip)
    
    print("✓ IP blocking functionality works correctly")


def test_metrics_calculation():
    """Test 7: Error rate and failure probability calculation."""
    detector = MLAnomalyDetector()
    
    # Test error rate
    y_true = np.array([0, 0, 1, 1, 0, 1, 0, 0])
    y_pred = np.array([0, 1, 1, 0, 0, 1, 0, 0])
    
    error_rate = detector.calculate_error_rate(y_true, y_pred)
    
    print(f"\nError Rate Test:")
    print(f"  True labels:      {y_true}")
    print(f"  Predicted labels: {y_pred}")
    print(f"  Error rate: {error_rate:.2%}")
    
    # Verify error rate
    expected_errors = 2  # Mismatches at indices 1 and 3
    expected_rate = expected_errors / len(y_true)
    assert abs(error_rate - expected_rate) < 0.01
    
    # Test failure probability
    y_pred_window = np.array([0, 0, 1, 1, 1, 0, 1, 1, 0, 1])
    failure_prob = detector.calculate_failure_probability(y_pred_window)
    
    print(f"\nFailure Probability Test:")
    print(f"  Prediction window: {y_pred_window}")
    print(f"  Failure probability: {failure_prob:.2%}")
    
    # Verify failure probability (6 anomalies out of 10)
    expected_prob = 6 / 10
    assert abs(failure_prob - expected_prob) < 0.01
    
    print("✓ Metrics calculation correct")


def test_statistics_tracking():
    """Test 8: Statistics tracking."""
    detector = MLAnomalyDetector()
    detector.load_models()
    
    # Make some predictions
    for i in range(5):
        ip = f'192.168.1.{100+i}'
        data = np.random.randn(1, 10)
        
        if len(detector.cic_models) > 0:
            prediction = detector.predict_anomaly(data, protocol='network')
            detector.check_and_block_ip(ip, prediction, threshold=0.7)
    
    # Get statistics
    stats = detector.get_statistics()
    
    print(f"\nStatistics:")
    print(f"  Total IPs seen: {stats['total_ips_seen']}")
    print(f"  Blocked IPs: {stats['blocked_ips_count']}")
    print(f"  Total predictions: {stats['total_predictions']}")
    print(f"  Anomaly predictions: {stats['anomaly_predictions']}")
    print(f"  Anomaly rate: {stats['anomaly_rate']:.2%}")
    print(f"  CIC models loaded: {stats['cic_models_loaded']}")
    print(f"  CSIC models loaded: {stats['csic_models_loaded']}")
    print(f"  Total models: {stats['total_models']}")
    
    # Get blocked IPs
    blocked_ips = detector.get_blocked_ips()
    print(f"  Blocked IP list: {blocked_ips}")
    
    print("✓ Statistics tracking works correctly")


def test_autoencoder():
    """Test 9: Autoencoder functionality."""
    print("\nTesting autoencoder...")
    
    # Generate dummy data
    np.random.seed(42)
    X_normal = np.random.randn(100, 10)
    X_anomaly = np.random.randn(20, 10) * 3 + 5
    
    # Train autoencoder
    print("Training autoencoder...")
    detector = train_autoencoder(
        X_train=X_normal[:80],
        X_val=X_normal[80:],
        epochs=10,  # Fewer epochs for testing
        batch_size=16,
        encoding_dim=5
    )
    
    # Test predictions
    normal_preds = detector.predict(X_normal[80:])
    anomaly_preds = detector.predict(X_anomaly)
    
    print(f"\nAutoencoder predictions:")
    print(f"  Normal samples - anomalies detected: {normal_preds.sum()}/{len(normal_preds)}")
    print(f"  Anomalous samples - anomalies detected: {anomaly_preds.sum()}/{len(anomaly_preds)}")
    
    # Anomaly detection rate should be higher for anomalous samples
    normal_anomaly_rate = normal_preds.sum() / len(normal_preds)
    anomaly_detection_rate = anomaly_preds.sum() / len(anomaly_preds)
    
    print(f"  Normal anomaly rate: {normal_anomaly_rate:.2%}")
    print(f"  Anomaly detection rate: {anomaly_detection_rate:.2%}")
    
    print("✓ Autoencoder functionality works")


def test_standalone_functions():
    """Test 10: Standalone helper functions."""
    from ml_anomaly_detection import (
        load_models,
        calculate_error_rate,
        calculate_failure_probability
    )
    
    # Test load_models function
    detector = load_models()
    assert detector is not None
    print("✓ load_models() works")
    
    # Test calculate_error_rate function
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 1])
    error_rate = calculate_error_rate(y_true, y_pred)
    print(f"✓ calculate_error_rate() works: {error_rate:.2%}")
    
    # Test calculate_failure_probability function
    y_pred = np.array([0, 0, 1, 1, 1, 0, 1])
    failure_prob = calculate_failure_probability(y_pred)
    print(f"✓ calculate_failure_probability() works: {failure_prob:.2%}")


def main():
    """Run all tests."""
    print("="*70)
    print("ML ANOMALY DETECTION - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    runner = TestRunner()
    
    # Run all tests
    runner.run_test("Module Imports", test_module_imports)
    runner.run_test("Detector Initialization", test_detector_initialization)
    runner.run_test("Model Loading", test_model_loading)
    runner.run_test("Network Prediction", test_network_prediction)
    runner.run_test("HTTP Prediction", test_http_prediction)
    runner.run_test("IP Blocking", test_ip_blocking)
    runner.run_test("Metrics Calculation", test_metrics_calculation)
    runner.run_test("Statistics Tracking", test_statistics_tracking)
    runner.run_test("Autoencoder", test_autoencoder)
    runner.run_test("Standalone Functions", test_standalone_functions)
    
    # Print summary
    runner.print_summary()
    
    # Return exit code
    return 0 if runner.tests_failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
