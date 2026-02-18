"""
Integration Test: All ML Features Together

Tests the complete integration of all 5 advanced ML features:
1. SHAP Explainability
2. Concept Drift Detection
3. Real-Time Inference
4. Ensemble Threat Scoring
5. IP Risk Tracking

Demonstrates end-to-end workflow with performance metrics.
"""

import time
import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import all modules
from explainability import SHAPExplainer
from drift_detection import ConceptDriftDetector
from realtime_inference import RealTimeInferenceEngine, FeatureExtractor
from ensemble_scoring import EnsembleThreatScorer
from ip_risk_engine import IPRiskEngine


class IntegratedThreatDetectionSystem:
    """
    Complete integrated system combining all ML features.
    """
    
    def __init__(self):
        """Initialize all components."""
        print("="*80)
        print("INITIALIZING INTEGRATED THREAT DETECTION SYSTEM")
        print("="*80)
        
        # 1. SHAP Explainability
        print("\n[1/5] Loading SHAP Explainability...")
        self.explainer = SHAPExplainer(
            models_dir='models',
            output_dir='evaluation_results/explainability'
        )
        self.explainer.load_model('robust_random_forest')
        self.explainer.create_explainer('robust_random_forest')
        
        # 2. Drift Detection
        print("[2/5] Loading Drift Detection...")
        self.drift_detector = ConceptDriftDetector(
            reference_data_path='evaluation_results/training/kfold_test_features.csv'
        )
        
        # 3. Real-Time Inference
        print("[3/5] Loading Real-Time Inference...")
        self.inference_engine = RealTimeInferenceEngine(
            model_path='models/robust_random_forest.pkl'
        )
        
        # 4. Ensemble Threat Scoring
        print("[4/5] Loading Ensemble Scoring...")
        self.ensemble_scorer = EnsembleThreatScorer(
            models_dir='models',
            rf_model_name='robust_random_forest',
            iso_model_name='robust_isolation_forest'
        )
        
        # 5. IP Risk Tracking
        print("[5/5] Loading IP Risk Engine...")
        self.ip_risk_engine = IPRiskEngine(
            high_risk_threshold=70
        )
        
        print("\n" + "="*80)
        print("SYSTEM INITIALIZED SUCCESSFULLY")
        print("="*80)
    
    def process_request(
        self,
        ip_address: str,
        endpoint: str,
        method: str,
        payload_size: int,
        response_time: float,
        status_code: int
    ) -> dict:
        """
        Process a request through the complete pipeline.
        
        Args:
            ip_address: Source IP
            endpoint: Requested endpoint
            method: HTTP method
            payload_size: Payload size in bytes
            response_time: Response time in ms
            status_code: HTTP status code
            
        Returns:
            Complete analysis result
        """
        start_time = time.time()
        
        # Stage 1: Real-time inference
        request_metadata = {
            'endpoint': endpoint,
            'method': method,
            'payload_size': payload_size,
            'response_time': response_time,
            'status_code': status_code,
            'timestamp': time.time()
        }
        prediction = self.inference_engine.predict_anomaly(
            ip_address=ip_address,
            request_metadata=request_metadata
        )
        
        # Stage 2: Ensemble threat scoring (more accurate)
        # Convert features dict to properly ordered array
        feature_names = [
            'request_rate', 'unique_endpoint_count', 'method_ratio',
            'avg_payload_size', 'error_rate', 'repeated_parameter_ratio',
            'user_agent_entropy', 'avg_response_time', 'max_response_time'
        ]
        features_values = [prediction['features'][fname] for fname in feature_names]
        features = np.array([features_values])
        ensemble_scores = self.ensemble_scorer.compute_ensemble_score(features)
        threat_score = float(ensemble_scores[0])
        risk_level = self.ensemble_scorer.classify_risk_level(threat_score)
        
        # Stage 3: SHAP explanation (if anomaly detected)
        explanation = None
        if prediction['is_anomaly']:
            # Convert features array to DataFrame
            features_df = pd.DataFrame(features, columns=[
                'request_rate', 'unique_endpoint_count', 'method_ratio',
                'avg_payload_size', 'error_rate', 'repeated_parameter_ratio',
                'user_agent_entropy', 'avg_response_time', 'max_response_time'
            ])
            explanation = self.explainer.explain_sample(
                model_name='robust_random_forest',
                X_sample=features_df,
                sample_idx=0,
                top_k=5
            )
        
        # Stage 4: Update IP risk tracking
        ip_update = self.ip_risk_engine.update_ip_risk(
            ip_address=ip_address,
            threat_score=threat_score,
            is_anomaly=prediction['is_anomaly']
        )
        
        total_time = (time.time() - start_time) * 1000  # ms
        
        return {
            'ip_address': ip_address,
            'endpoint': endpoint,
            'is_anomaly': prediction['is_anomaly'],
            'base_anomaly_score': prediction['anomaly_score'],
            'ensemble_threat_score': threat_score,
            'risk_level': risk_level,
            'ip_risk_score': ip_update['risk_score'],
            'ip_flagged': ip_update['flagged'],
            'explanation': explanation,
            'processing_time_ms': total_time
        }
    
    def check_drift(self, current_data_path: str) -> dict:
        """
        Check for concept drift.
        
        Args:
            current_data_path: Path to current data CSV
            
        Returns:
            Drift detection results
        """
        drift_results = self.drift_detector.detect_drift(current_data_path)
        return drift_results
    
    def get_system_health(self) -> dict:
        """
        Get overall system health metrics.
        
        Returns:
            System health information
        """
        inference_stats = self.inference_engine.get_performance_stats()
        ip_stats = self.ip_risk_engine.get_statistics()
        
        health = {
            'inference_performance': inference_stats,
            'ip_tracking': ip_stats,
            'high_risk_ips': len(self.ip_risk_engine.get_high_risk_ips()),
            'status': 'healthy'
        }
        
        # Check for issues
        if 'mean_inference_time_ms' in inference_stats:
            if inference_stats['mean_inference_time_ms'] > 20:
                health['status'] = 'degraded'
                health['warning'] = 'High inference latency'
        
        return health


def test_normal_traffic():
    """Test system with normal traffic."""
    print("\n" + "="*80)
    print("TEST 1: NORMAL TRAFFIC")
    print("="*80)
    
    system = IntegratedThreatDetectionSystem()
    
    # Simulate normal requests
    normal_requests = [
        {
            'ip_address': '192.168.1.100',
            'endpoint': '/api/users',
            'method': 'GET',
            'payload_size': 256,
            'response_time': 120,
            'status_code': 200
        },
        {
            'ip_address': '192.168.1.101',
            'endpoint': '/api/products',
            'method': 'GET',
            'payload_size': 512,
            'response_time': 150,
            'status_code': 200
        },
        {
            'ip_address': '192.168.1.102',
            'endpoint': '/api/orders',
            'method': 'POST',
            'payload_size': 1024,
            'response_time': 200,
            'status_code': 201
        }
    ]
    
    results = []
    for req in normal_requests:
        result = system.process_request(**req)
        results.append(result)
        print(f"\nIP: {result['ip_address']}")
        print(f"  Anomaly: {result['is_anomaly']}")
        print(f"  Threat Score: {result['ensemble_threat_score']:.3f}")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Processing Time: {result['processing_time_ms']:.2f} ms")
    
    avg_processing_time = np.mean([r['processing_time_ms'] for r in results])
    print(f"\n[NORMAL TRAFFIC] Average Processing Time: {avg_processing_time:.2f} ms")
    
    return system


def test_attack_traffic(system: IntegratedThreatDetectionSystem):
    """Test system with attack traffic."""
    print("\n" + "="*80)
    print("TEST 2: ATTACK TRAFFIC")
    print("="*80)
    
    # Simulate SQL injection attack
    attack_requests = [
        {
            'ip_address': '172.16.0.99',
            'endpoint': "/api/users?id=1' OR '1'='1",
            'method': 'GET',
            'payload_size': 2048,
            'response_time': 500,
            'status_code': 500
        }
        for _ in range(10)  # Repeated attack
    ]
    
    results = []
    for req in attack_requests:
        result = system.process_request(**req)
        results.append(result)
    
    final_result = results[-1]
    
    print(f"\nAttack IP: {final_result['ip_address']}")
    print(f"  Anomaly Detected: {final_result['is_anomaly']}")
    print(f"  Threat Score: {final_result['ensemble_threat_score']:.3f}")
    print(f"  Risk Level: {final_result['risk_level']}")
    print(f"  IP Risk Score: {final_result['ip_risk_score']:.1f}/100")
    print(f"  IP Flagged: {final_result['ip_flagged']}")
    
    if final_result['explanation']:
        print(f"\n  Top Contributing Features:")
        for feat in final_result['explanation']['top_features']:
            print(f"    - {feat['feature']}: {feat['contribution']:.3f}")
    
    avg_processing_time = np.mean([r['processing_time_ms'] for r in results])
    print(f"\n[ATTACK TRAFFIC] Average Processing Time: {avg_processing_time:.2f} ms")


def test_drift_detection(system: IntegratedThreatDetectionSystem):
    """Test drift detection."""
    print("\n" + "="*80)
    print("TEST 3: CONCEPT DRIFT DETECTION")
    print("="*80)
    
    # Check if we have validation data
    val_path = Path('evaluation_results/training/kfold_val_features.csv')
    
    if val_path.exists():
        print(f"\nChecking drift with validation data...")
        drift_results = system.check_drift(str(val_path))
        
        print(f"\nDrift Detection Results:")
        print(f"  Overall Drift Detected: {drift_results['drift_detected']}")
        print(f"  Features with Drift: {len(drift_results['drifted_features'])}")
        
        if drift_results['drifted_features']:
            print(f"\n  Drifted Features:")
            for feat in drift_results['drifted_features'][:3]:
                print(f"    - {feat['feature']}: p-value={feat['p_value']:.4f}")
    else:
        print(f"\n[SKIP] Validation data not found: {val_path}")


def test_system_health(system: IntegratedThreatDetectionSystem):
    """Test system health monitoring."""
    print("\n" + "="*80)
    print("TEST 4: SYSTEM HEALTH MONITORING")
    print("="*80)
    
    health = system.get_system_health()
    
    print(f"\nSystem Status: {health['status'].upper()}")
    print(f"High Risk IPs: {health['high_risk_ips']}")
    
    if 'mean_inference_time_ms' in health['inference_performance']:
        print(f"\nInference Performance:")
        print(f"  Mean Latency: {health['inference_performance']['mean_inference_time_ms']:.2f} ms")
        print(f"  P95 Latency: {health['inference_performance']['p95_inference_time_ms']:.2f} ms")
        print(f"  P99 Latency: {health['inference_performance']['p99_inference_time_ms']:.2f} ms")
    
    if 'total_ips' in health['ip_tracking']:
        print(f"\nIP Tracking:")
        print(f"  Total IPs: {health['ip_tracking']['total_ips']}")
        print(f"  Risk Distribution:")
        print(f"    - Low: {health['ip_tracking']['risk_distribution']['low']}")
        print(f"    - Medium: {health['ip_tracking']['risk_distribution']['medium']}")
        print(f"    - High: {health['ip_tracking']['risk_distribution']['high']}")


def performance_benchmark():
    """Benchmark end-to-end performance."""
    print("\n" + "="*80)
    print("PERFORMANCE BENCHMARK")
    print("="*80)
    
    system = IntegratedThreatDetectionSystem()
    
    # Benchmarking parameters
    num_requests = 100
    
    print(f"\nProcessing {num_requests} requests...")
    
    processing_times = []
    
    for i in range(num_requests):
        start = time.time()
        
        result = system.process_request(
            ip_address=f'192.168.1.{i % 255}',
            endpoint='/api/test',
            method='GET',
            payload_size=512,
            response_time=150,
            status_code=200
        )
        
        elapsed = (time.time() - start) * 1000
        processing_times.append(elapsed)
    
    # Compute statistics
    print(f"\nPerformance Results ({num_requests} requests):")
    print(f"  Mean:   {np.mean(processing_times):.2f} ms")
    print(f"  Median: {np.median(processing_times):.2f} ms")
    print(f"  P95:    {np.percentile(processing_times, 95):.2f} ms")
    print(f"  P99:    {np.percentile(processing_times, 99):.2f} ms")
    print(f"  Min:    {np.min(processing_times):.2f} ms")
    print(f"  Max:    {np.max(processing_times):.2f} ms")
    
    # Target: <15ms inference (just RF/ISO, not full pipeline)
    # Full pipeline includes explanation, IP tracking, etc., so higher is expected
    print(f"\nTarget: <15ms for inference only (achieved in realtime_inference.py)")
    print(f"Full pipeline: ~{np.mean(processing_times):.1f}ms (includes all features)")


def main():
    """Run all integration tests."""
    print("\n" + "="*80)
    print("ML FEATURES INTEGRATION TEST SUITE")
    print("="*80)
    
    # Test 1: Normal traffic
    system = test_normal_traffic()
    
    # Test 2: Attack traffic
    test_attack_traffic(system)
    
    # Test 3: Drift detection
    test_drift_detection(system)
    
    # Test 4: System health
    test_system_health(system)
    
    # Performance benchmark
    performance_benchmark()
    
    print("\n" + "="*80)
    print("ALL INTEGRATION TESTS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
