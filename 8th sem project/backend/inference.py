import joblib
import numpy as np
import os
from typing import Dict, Optional


class MLInferenceEngine:
    """
    Real-time ML inference engine that loads trained models and performs predictions.
    
    Ensemble approach combining:
    1. Isolation Forest (anomaly detection)
    2. K-Means (usage clustering)
    3. Random Forest (failure prediction)
    
    Final risk score is a weighted combination of all three models.
    """
    
    def __init__(self):
        self.models_loaded = False
        self.isolation_forest = None
        self.isolation_scaler = None
        self.kmeans = None
        self.random_forest = None
        self.bot_cluster = None
        
        self.load_models()
    
    def load_models(self):
        """
        Load all trained models from disk.
        Falls back to training if models don't exist.
        """
        models_dir = os.path.join(os.path.dirname(__file__), 'models')
        
        if not os.path.exists(models_dir):
            print("Models not found. Training new models...")
            from train_models import train_all_models
            train_all_models()
        
        try:
            self.isolation_forest = joblib.load(os.path.join(models_dir, 'isolation_forest.pkl'))
            self.isolation_scaler = joblib.load(os.path.join(models_dir, 'isolation_scaler.pkl'))
            self.kmeans = joblib.load(os.path.join(models_dir, 'kmeans.pkl'))
            self.random_forest = joblib.load(os.path.join(models_dir, 'random_forest.pkl'))
            
            with open(os.path.join(models_dir, 'bot_cluster.txt'), 'r') as f:
                self.bot_cluster = int(f.read().strip())
            
            self.models_loaded = True
            print("All models loaded successfully!")
            
        except Exception as e:
            print(f"Error loading models: {e}")
            print("Training new models...")
            from train_models import train_all_models
            models = train_all_models()
            self.isolation_forest = models['isolation_forest']
            self.isolation_scaler = models['isolation_scaler']
            self.kmeans = models['kmeans']
            self.random_forest = models['random_forest']
            self.bot_cluster = models['bot_cluster']
            self.models_loaded = True
    
    def predict(self, features: Dict) -> Dict:
        """
        Perform real-time inference on incoming feature vector.
        
        Args:
            features: Dictionary containing:
                - req_count
                - error_rate
                - avg_response_time
                - max_response_time
                - payload_mean
                - unique_endpoints
                - repeat_rate
                - status_entropy
        
        Returns:
            Dictionary with:
                - anomaly_score: Raw anomaly score from Isolation Forest
                - is_anomaly: Boolean indicating if anomaly detected
                - usage_cluster: Cluster assignment (0=normal, 1=heavy, 2=bot)
                - failure_probability: Probability of failure [0, 1]
                - risk_score: Final ensemble risk score [0, 1]
                - priority: Risk priority level (LOW, MEDIUM, HIGH)
        """
        if not self.models_loaded:
            raise RuntimeError("Models not loaded")
        
        # Map features to match training data format
        # Training uses: request_rate, unique_endpoint_count, method_ratio, avg_payload_size,
        #                error_rate, repeated_parameter_ratio, user_agent_entropy, 
        #                avg_response_time, max_response_time
        feature_vector = np.array([[
            features.get('req_count', features.get('request_rate', 10)),  # request_rate
            features.get('unique_endpoints', features.get('unique_endpoint_count', 5)),  # unique_endpoint_count
            features.get('repeat_rate', features.get('method_ratio', 0.5)),  # method_ratio (using repeat_rate as proxy)
            features.get('payload_mean', features.get('avg_payload_size', 200)),  # avg_payload_size
            features['error_rate'],  # error_rate (exists in both)
            features.get('repeat_rate', features.get('repeated_parameter_ratio', 0.3)),  # repeated_parameter_ratio
            features.get('status_entropy', features.get('user_agent_entropy', 0.5)),  # user_agent_entropy
            features['avg_response_time'],  # avg_response_time (exists in both)
            features['max_response_time']  # max_response_time (exists in both)
        ]])
        
        X_scaled = self.isolation_scaler.transform(feature_vector)
        anomaly_score_raw = self.isolation_forest.decision_function(X_scaled)[0]
        is_anomaly = self.isolation_forest.predict(X_scaled)[0] == -1
        
        anomaly_score_normalized = self._normalize_anomaly_score(anomaly_score_raw)
        
        usage_cluster = self.kmeans.predict(feature_vector)[0]
        
        failure_proba = self.random_forest.predict_proba(feature_vector)[0]
        failure_probability = failure_proba[1] if len(failure_proba) > 1 else 0.0
        
        is_bot = 1.0 if usage_cluster == self.bot_cluster else 0.0
        
        risk_score = self._calculate_ensemble_risk(
            anomaly_score_normalized,
            failure_probability,
            is_bot
        )
        
        priority = self._determine_priority(risk_score)
        
        return {
            'anomaly_score': float(anomaly_score_raw),
            'is_anomaly': bool(is_anomaly),
            'usage_cluster': int(usage_cluster),
            'failure_probability': float(failure_probability),
            'risk_score': float(risk_score),
            'priority': priority
        }
    
    def _normalize_anomaly_score(self, score: float) -> float:
        """
        Normalize Isolation Forest anomaly score to [0, 1] range.
        
        Isolation Forest returns negative scores for anomalies.
        We normalize to 0-1 where higher = more anomalous.
        """
        normalized = -score
        normalized = max(0.0, min(1.0, (normalized + 0.5) / 1.0))
        return normalized
    
    def _calculate_ensemble_risk(
        self, 
        anomaly_score: float, 
        failure_prob: float, 
        is_bot: float
    ) -> float:
        """
        Calculate ensemble risk score using weighted combination.
        
        Weights:
        - 45% anomaly detection (unusual behavior patterns)
        - 35% failure prediction (service degradation)
        - 20% bot detection (automated abuse)
        
        This weighting prioritizes anomaly detection while still
        considering failure risk and bot behavior.
        """
        risk = (
            0.45 * anomaly_score +
            0.35 * failure_prob +
            0.20 * is_bot
        )
        
        return max(0.0, min(1.0, risk))
    
    def _determine_priority(self, risk_score: float) -> str:
        """
        Determine priority level based on risk score.
        
        Thresholds:
        - >= 0.8: HIGH (immediate attention required)
        - 0.5 - 0.8: MEDIUM (monitor closely)
        - < 0.5: LOW (normal operation)
        """
        if risk_score >= 0.8:
            return "HIGH"
        elif risk_score >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"


# Initialize inference engine (will be set in app.py after database initialization)
inference_engine = None
