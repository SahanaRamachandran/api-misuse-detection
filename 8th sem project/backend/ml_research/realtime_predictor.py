"""
Real-Time Anomaly Predictor Module
===================================
Production-ready real-time prediction for API anomaly detection.

Features:
- Load trained models and scaler
- Accept live metrics input
- Return anomaly predictions with confidence scores
- Support both Random Forest and Isolation Forest

Author: Research Team
Date: February 2026
"""

import numpy as np
import joblib
import os
from typing import Dict, Optional, Tuple
from datetime import datetime


class RealtimeAnomalyPredictor:
    """Real-time anomaly detection predictor"""
    
    FEATURE_NAMES = [
        'avg_response_time',
        'request_count',
        'error_rate',
        'five_xx_rate',
        'four_xx_rate',
        'payload_avg_size',
        'unique_ip_count',
        'cpu_usage',
        'memory_usage'
    ]
    
    def __init__(
        self,
        models_dir: str = 'models',
        use_random_forest: bool = True,
        use_isolation_forest: bool = False
    ):
        """
        Initialize predictor
        
        Args:
            models_dir: Directory containing trained models
            use_random_forest: Whether to use Random Forest model
            use_isolation_forest: Whether to use Isolation Forest model
        """
        self.models_dir = models_dir
        self.use_random_forest = use_random_forest
        self.use_isolation_forest = use_isolation_forest
        
        # Load models and scaler
        self.scaler = None
        self.random_forest = None
        self.isolation_forest = None
        
        self._load_components()
    
    def _load_components(self):
        """Load trained models and scaler"""
        print("🔧 Initializing Real-Time Predictor...")
        
        # Load scaler (required)
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler not found: {scaler_path}")
        
        self.scaler = joblib.load(scaler_path)
        print(f"   ✓ Loaded scaler")
        
        # Load Random Forest
        if self.use_random_forest:
            rf_path = os.path.join(self.models_dir, 'random_forest.pkl')
            if os.path.exists(rf_path):
                self.random_forest = joblib.load(rf_path)
                print(f"   ✓ Loaded Random Forest model")
            else:
                print(f"   ⚠️  Random Forest model not found")
                self.use_random_forest = False
        
        # Load Isolation Forest
        if self.use_isolation_forest:
            if_path = os.path.join(self.models_dir, 'isolation_forest.pkl')
            if os.path.exists(if_path):
                self.isolation_forest = joblib.load(if_path)
                print(f"   ✓ Loaded Isolation Forest model")
            else:
                print(f"   ⚠️  Isolation Forest model not found")
                self.use_isolation_forest = False
        
        print("✅ Predictor ready!\n")
    
    def validate_input(self, metrics: Dict[str, float]) -> bool:
        """
        Validate input metrics
        
        Args:
            metrics: Dictionary of metric values
        
        Returns:
            True if valid, False otherwise
        """
        # Check all required features present
        for feature in self.FEATURE_NAMES:
            if feature not in metrics:
                print(f"❌ Missing feature: {feature}")
                return False
        
        # Check for valid ranges
        if metrics['avg_response_time'] < 0:
            print(f"❌ Invalid avg_response_time: {metrics['avg_response_time']}")
            return False
        
        if metrics['request_count'] < 0:
            print(f"❌ Invalid request_count: {metrics['request_count']}")
            return False
        
        if not (0 <= metrics['error_rate'] <= 1):
            print(f"❌ Invalid error_rate: {metrics['error_rate']} (must be 0-1)")
            return False
        
        return True
    
    def prepare_features(self, metrics: Dict[str, float]) -> np.ndarray:
        """
        Prepare features for prediction
        
        Args:
            metrics: Dictionary of metric values
        
        Returns:
            Normalized feature array
        """
        # Extract features in correct order
        features = np.array([metrics[name] for name in self.FEATURE_NAMES]).reshape(1, -1)
        
        # Normalize using fitted scaler
        features_scaled = self.scaler.transform(features)
        
        return features_scaled
    
    def predict_random_forest(self, features: np.ndarray) -> Dict:
        """
        Predict using Random Forest
        
        Args:
            features: Normalized feature array
        
        Returns:
            Dictionary with prediction results
        """
        if not self.use_random_forest or self.random_forest is None:
            return None
        
        # Prediction
        prediction = self.random_forest.predict(features)[0]
        
        # Probability scores
        proba = self.random_forest.predict_proba(features)[0]
        confidence = proba[1] if prediction == 1 else proba[0]
        anomaly_score = proba[1]  # Probability of being anomaly
        
        return {
            'model': 'Random Forest',
            'prediction': int(prediction),
            'prediction_label': 'Anomaly' if prediction == 1 else 'Normal',
            'anomaly_score': float(anomaly_score),
            'confidence': float(confidence),
            'threshold': 0.5
        }
    
    def predict_isolation_forest(self, features: np.ndarray) -> Dict:
        """
        Predict using Isolation Forest
        
        Args:
            features: Normalized feature array
        
        Returns:
            Dictionary with prediction results
        """
        if not self.use_isolation_forest or self.isolation_forest is None:
            return None
        
        # Prediction (-1 for anomaly, 1 for normal)
        prediction_raw = self.isolation_forest.predict(features)[0]
        prediction = 1 if prediction_raw == -1 else 0
        
        # Anomaly score (lower = more anomalous)
        score_raw = self.isolation_forest.score_samples(features)[0]
        # Invert and normalize to 0-1 range (higher = more anomalous)
        anomaly_score = max(0, min(1, (-score_raw + 0.5) / 2))
        
        confidence = anomaly_score if prediction == 1 else (1 - anomaly_score)
        
        return {
            'model': 'Isolation Forest',
            'prediction': int(prediction),
            'prediction_label': 'Anomaly' if prediction == 1 else 'Normal',
            'anomaly_score': float(anomaly_score),
            'confidence': float(confidence),
            'threshold': 'adaptive'
        }
    
    def predict(self, metrics: Dict[str, float]) -> Dict:
        """
        Main prediction method
        
        Args:
            metrics: Dictionary with metric values
        
        Returns:
            Dictionary with comprehensive prediction results
        """
        # Validate input
        if not self.validate_input(metrics):
            raise ValueError("Invalid input metrics")
        
        # Prepare features
        features = self.prepare_features(metrics)
        
        # Get predictions from available models
        results = {
            'timestamp': datetime.now().isoformat(),
            'input_metrics': metrics,
            'predictions': {}
        }
        
        # Random Forest prediction
        if self.use_random_forest:
            rf_result = self.predict_random_forest(features)
            results['predictions']['random_forest'] = rf_result
        
        # Isolation Forest prediction
        if self.use_isolation_forest:
            if_result = self.predict_isolation_forest(features)
            results['predictions']['isolation_forest'] = if_result
        
        # Ensemble prediction (if both models available)
        if self.use_random_forest and self.use_isolation_forest:
            rf_pred = results['predictions']['random_forest']['prediction']
            if_pred = results['predictions']['isolation_forest']['prediction']
            
            # Vote-based ensemble
            ensemble_prediction = 1 if (rf_pred + if_pred) >= 1 else 0
            
            # Average confidence
            avg_confidence = (
                results['predictions']['random_forest']['confidence'] +
                results['predictions']['isolation_forest']['confidence']
            ) / 2
            
            results['predictions']['ensemble'] = {
                'model': 'Ensemble (RF + IF)',
                'prediction': ensemble_prediction,
                'prediction_label': 'Anomaly' if ensemble_prediction == 1 else 'Normal',
                'confidence': avg_confidence
            }
        
        # Set primary prediction (use Random Forest if available, otherwise Isolation Forest)
        if self.use_random_forest:
            results['primary_prediction'] = results['predictions']['random_forest']
        elif self.use_isolation_forest:
            results['primary_prediction'] = results['predictions']['isolation_forest']
        
        return results
    
    def predict_batch(self, metrics_list: list) -> list:
        """
        Predict for multiple metric samples
        
        Args:
            metrics_list: List of metric dictionaries
        
        Returns:
            List of prediction results
        """
        return [self.predict(metrics) for metrics in metrics_list]


def create_sample_metrics() -> Dict[str, float]:
    """Create sample metrics for testing"""
    return {
        'avg_response_time': 150.5,
        'request_count': 45,
        'error_rate': 0.02,
        'five_xx_rate': 0.01,
        'four_xx_rate': 0.01,
        'payload_avg_size': 2048.0,
        'unique_ip_count': 25,
        'cpu_usage': 35.0,
        'memory_usage': 45.0
    }


def create_anomaly_metrics() -> Dict[str, float]:
    """Create anomalous metrics for testing"""
    return {
        'avg_response_time': 4500.0,  # Very high latency
        'request_count': 450,          # 10x normal traffic
        'error_rate': 0.65,            # 65% error rate
        'five_xx_rate': 0.50,          # 50% server errors
        'four_xx_rate': 0.15,          # 15% client errors
        'payload_avg_size': 15000.0,   # Large payloads
        'unique_ip_count': 150,        # Many IPs
        'cpu_usage': 85.0,             # High CPU
        'memory_usage': 92.0           # High memory
    }


def main():
    """Demonstration of real-time prediction"""
    print("="*70)
    print("🚀 REAL-TIME ANOMALY PREDICTION DEMO")
    print("="*70)
    
    # Initialize predictor
    predictor = RealtimeAnomalyPredictor(
        models_dir='models',
        use_random_forest=True,
        use_isolation_forest=True
    )
    
    # Test 1: Normal metrics
    print("\n" + "="*70)
    print("📊 Test 1: Normal Metrics")
    print("="*70)
    
    normal_metrics = create_sample_metrics()
    print("\nInput Metrics:")
    for key, value in normal_metrics.items():
        print(f"  {key:<20s}: {value}")
    
    result = predictor.predict(normal_metrics)
    
    print("\n🔍 Prediction Results:")
    for model_name, pred in result['predictions'].items():
        print(f"\n  {pred['model']}:")
        print(f"    Prediction: {pred['prediction_label']}")
        print(f"    Anomaly Score: {pred['anomaly_score']:.4f}")
        print(f"    Confidence: {pred['confidence']:.4f}")
    
    # Test 2: Anomalous metrics
    print("\n" + "="*70)
    print("⚠️  Test 2: Anomalous Metrics")
    print("="*70)
    
    anomaly_metrics = create_anomaly_metrics()
    print("\nInput Metrics:")
    for key, value in anomaly_metrics.items():
        print(f"  {key:<20s}: {value}")
    
    result = predictor.predict(anomaly_metrics)
    
    print("\n🔍 Prediction Results:")
    for model_name, pred in result['predictions'].items():
        print(f"\n  {pred['model']}:")
        print(f"    Prediction: {pred['prediction_label']}")
        print(f"    Anomaly Score: {pred['anomaly_score']:.4f}")
        print(f"    Confidence: {pred['confidence']:.4f}")
    
    print("\n" + "="*70)
    print("✅ Demo Complete!")
    print("="*70)
    
    print("\n📘 Usage Example:")
    print("""
    from realtime_predictor import RealtimeAnomalyPredictor
    
    # Initialize
    predictor = RealtimeAnomalyPredictor(models_dir='models')
    
    # Prepare metrics
    metrics = {
        'avg_response_time': 150.5,
        'request_count': 45,
        'error_rate': 0.02,
        'five_xx_rate': 0.01,
        'four_xx_rate': 0.01,
        'payload_avg_size': 2048.0,
        'unique_ip_count': 25,
        'cpu_usage': 35.0,
        'memory_usage': 45.0
    }
    
    # Predict
    result = predictor.predict(metrics)
    print(result['primary_prediction'])
    """)


if __name__ == '__main__':
    main()
