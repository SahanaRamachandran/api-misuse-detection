"""
Real-Time Inference Middleware for FastAPI

Performs anomaly detection on incoming API requests in real-time:
- Loads robust model + scaler at startup
- Computes features from request metadata
- Predicts anomaly probability
- Logs anomaly_score, predicted_label, risk_score
- Saves anomalies to anomalies_log.json
- Target inference latency: <15ms
- Non-blocking (does not stop request execution)

Usage with FastAPI:
    from realtime_inference import RealTimeInferenceMiddleware
    app.add_middleware(RealTimeInferenceMiddleware)
"""

import time
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict, deque
import asyncio
import warnings
warnings.filterwarnings('ignore')


class FeatureExtractor:
    """
    Extract features from API request metadata in real-time.
    """
    
    def __init__(self, window_seconds: int = 60):
        """
        Initialize feature extractor.
        
        Args:
            window_seconds: Time window for aggregating request stats
        """
        self.window_seconds = window_seconds
        
        # Sliding window storage (IP -> request history)
        self.request_history = defaultdict(lambda: deque(maxlen=1000))
        
        # Feature names (must match training data)
        self.feature_names = [
            'request_rate',
            'unique_endpoint_count',
            'method_ratio',
            'avg_payload_size',
            'error_rate',
            'repeated_parameter_ratio',
            'user_agent_entropy',
            'avg_response_time',
            'max_response_time'
        ]
    
    def update_history(
        self,
        ip_address: str,
        request_data: Dict[str, Any]
    ) -> None:
        """
        Update request history for an IP.
        
        Args:
            ip_address: Client IP address
            request_data: Dictionary with request metadata
        """
        request_data['timestamp'] = time.time()
        self.request_history[ip_address].append(request_data)
    
    def _compute_entropy(self, values: list) -> float:
        """Compute Shannon entropy."""
        if not values:
            return 0.0
        
        unique, counts = np.unique(values, return_counts=True)
        probabilities = counts / counts.sum()
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        return float(entropy)
    
    def extract_features(
        self,
        ip_address: str,
        current_request: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Extract features for a single request based on recent history.
        
        Args:
            ip_address: Client IP address
            current_request: Current request metadata
            
        Returns:
            DataFrame with single row of features
        """
        # Get recent requests within time window
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        history = self.request_history[ip_address]
        recent_requests = [r for r in history if r['timestamp'] >= cutoff_time]
        
        # Add current request to recent
        recent_requests.append(current_request)
        
        if not recent_requests:
            # Return default features if no history
            features = {name: 0.0 for name in self.feature_names}
            return pd.DataFrame([features])
        
        # Extract features
        n_requests = len(recent_requests)
        
        # request_rate: requests per second
        time_span = max(1.0, current_time - min(r['timestamp'] for r in recent_requests))
        request_rate = n_requests / time_span
        
        # unique_endpoint_count
        endpoints = [r.get('endpoint', '/') for r in recent_requests]
        unique_endpoint_count = len(set(endpoints))
        
        # method_ratio: ratio of different HTTP methods
        methods = [r.get('method', 'GET') for r in recent_requests]
        unique_methods = len(set(methods))
        method_ratio = unique_methods / max(1, len(methods)) * 10  # Scale for consistency
        
        # avg_payload_size
        payloads = [r.get('payload_size', 0) for r in recent_requests]
        avg_payload_size = np.mean(payloads) if payloads else 0.0
        
        # error_rate: fraction of 4xx/5xx responses
        status_codes = [r.get('status_code', 200) for r in recent_requests]
        error_count = sum(1 for code in status_codes if code >= 400)
        error_rate = error_count / max(1, len(status_codes))
        
        # repeated_parameter_ratio
        endpoint_counts = defaultdict(int)
        for endpoint in endpoints:
            endpoint_counts[endpoint] += 1
        repeated_count = sum(1 for count in endpoint_counts.values() if count > 1)
        repeated_parameter_ratio = repeated_count / max(1, len(endpoint_counts))
        
        # user_agent_entropy
        user_agents = [r.get('user_agent', '') for r in recent_requests]
        user_agent_entropy = self._compute_entropy(user_agents) if user_agents else 0.0
        
        # avg_response_time
        response_times = [r.get('response_time_ms', 0) for r in recent_requests]
        avg_response_time = np.mean(response_times) if response_times else 0.0
        
        # max_response_time
        max_response_time = np.max(response_times) if response_times else 0.0
        
        features = {
            'request_rate': request_rate,
            'unique_endpoint_count': unique_endpoint_count,
            'method_ratio': method_ratio,
            'avg_payload_size': avg_payload_size,
            'error_rate': error_rate,
            'repeated_parameter_ratio': repeated_parameter_ratio,
            'user_agent_entropy': user_agent_entropy,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time
        }
        
        return pd.DataFrame([features])


class RealTimeInferenceEngine:
    """
    Real-time anomaly detection inference engine.
    """
    
    def __init__(
        self,
        model_path: str = 'models/robust_random_forest.pkl',
        scaler_path: str = 'models/robust_random_forest_scaler.pkl',
        anomaly_threshold: float = 0.7,
        log_path: str = 'evaluation_results/inference/anomalies_log.json'
    ):
        """
        Initialize inference engine.
        
        Args:
            model_path: Path to trained model
            scaler_path: Path to feature scaler
            anomaly_threshold: Probability threshold for anomaly classification
            log_path: Path to anomaly log file
        """
        self.model_path = Path(model_path)
        self.scaler_path = Path(scaler_path)
        self.anomaly_threshold = anomaly_threshold
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load model and scaler
        self.model = None
        self.scaler = None
        self.load_model()
        
        # Feature extractor
        self.feature_extractor = FeatureExtractor(window_seconds=60)
        
        # Performance tracking
        self.inference_times = deque(maxlen=1000)
    
    def load_model(self) -> None:
        """Load trained model and scaler."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        if not self.scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found: {self.scaler_path}")
        
        self.model = joblib.load(self.model_path)
        self.scaler = joblib.load(self.scaler_path)
        
        print(f"[OK] Loaded model: {self.model_path.name}")
        print(f"[OK] Loaded scaler: {self.scaler_path.name}")
    
    def predict_anomaly(
        self,
        ip_address: str,
        request_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict anomaly probability for a request.
        
        Args:
            ip_address: Client IP address
            request_metadata: Request metadata dictionary
            
        Returns:
            Prediction results dictionary
        """
        start_time = time.time()
        
        # Extract features
        X = self.feature_extractor.extract_features(ip_address, request_metadata)
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0, 1]
        
        # Compute risk score (0-1 scale)
        risk_score = probability
        
        # Inference time
        inference_time_ms = (time.time() - start_time) * 1000
        self.inference_times.append(inference_time_ms)
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': ip_address,
            'predicted_label': int(prediction),
            'anomaly_score': float(probability),
            'risk_score': float(risk_score),
            'is_anomaly': bool(probability >= self.anomaly_threshold),
            'inference_time_ms': float(inference_time_ms),
            'features': X.iloc[0].to_dict()
        }
        
        # Update history (for next prediction)
        self.feature_extractor.update_history(ip_address, request_metadata)
        
        return result
    
    def log_anomaly(self, result: Dict[str, Any]) -> None:
        """
        Log anomaly to JSON file.
        
        Args:
            result: Prediction result dictionary
        """
        if not result['is_anomaly']:
            return
        
        # Load existing log
        if self.log_path.exists():
            with open(self.log_path, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {'anomalies': []}
        
        # Append new anomaly
        log_data['anomalies'].append(result)
        log_data['last_updated'] = datetime.utcnow().isoformat()
        log_data['total_anomalies'] = len(log_data['anomalies'])
        
        # Save
        with open(self.log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get inference performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.inference_times:
            return {'message': 'No inferences performed yet'}
        
        times = list(self.inference_times)
        
        return {
            'mean_inference_time_ms': np.mean(times),
            'median_inference_time_ms': np.median(times),
            'p95_inference_time_ms': np.percentile(times, 95),
            'p99_inference_time_ms': np.percentile(times, 99),
            'max_inference_time_ms': np.max(times),
            'total_inferences': len(times)
        }


# FastAPI Middleware (optional - for FastAPI integration)
try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
    
    class RealTimeInferenceMiddleware(BaseHTTPMiddleware):
        """
        FastAPI middleware for real-time anomaly detection.
        """
        
        def __init__(self, app, **kwargs):
            super().__init__(app)
            self.inference_engine = RealTimeInferenceEngine(**kwargs)
        
        async def dispatch(self, request: Request, call_next):
            # Get client IP
            ip_address = request.client.host
            
            # Request metadata
            request_metadata = {
                'endpoint': request.url.path,
                'method': request.method,
                'payload_size': int(request.headers.get('content-length', 0)),
                'user_agent': request.headers.get('user-agent', ''),
                'timestamp': time.time()
            }
            
            # Process request (non-blocking)
            response = await call_next(request)
            
            # Add response metadata
            request_metadata['status_code'] = response.status_code
            request_metadata['response_time_ms'] = 0  # Would need timing logic
            
            # Run inference (asynchronous)
            result = await asyncio.to_thread(
                self.inference_engine.predict_anomaly,
                ip_address,
                request_metadata
            )
            
            # Log if anomaly
            if result['is_anomaly']:
                await asyncio.to_thread(self.inference_engine.log_anomaly, result)
            
            # Add custom header with anomaly score
            response.headers['X-Anomaly-Score'] = str(result['anomaly_score'])
            
            return response

except ImportError:
    print("[WARN] FastAPI/Starlette not installed. Middleware disabled.")
    RealTimeInferenceMiddleware = None


def demo_realtime_inference():
    """
    Demo: Real-time inference on simulated requests.
    """
    print("="*80)
    print("REAL-TIME INFERENCE DEMO")
    print("="*80)
    
    # Initialize engine
    try:
        engine = RealTimeInferenceEngine(
            model_path='models/robust_random_forest.pkl',
            scaler_path='models/robust_random_forest_scaler.pkl',
            anomaly_threshold=0.7
        )
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("Please train robust models first using train_robust_models.py")
        return
    
    print("\n=== Simulating API Requests ===\n")
    
    # Simulate normal requests
    for i in range(10):
        request = {
            'endpoint': f'/api/endpoint_{i % 3}',
            'method': 'GET',
            'payload_size': np.random.randint(10, 100),
            'user_agent': 'Mozilla/5.0',
            'status_code': 200,
            'response_time_ms': np.random.uniform(50, 150)
        }
        
        result = engine.predict_anomaly('192.168.1.100', request)
        
        print(f"Request {i+1}: Anomaly Score = {result['anomaly_score']:.4f}, "
              f"Anomaly = {result['is_anomaly']}, "
              f"Inference Time = {result['inference_time_ms']:.2f}ms")
    
    # Simulate anomalous requests (high rate)
    print("\n=== Simulating Anomalous Burst ===\n")
    
    for i in range(50):
        request = {
            'endpoint': '/api/sensitive',
            'method': 'POST',
            'payload_size': np.random.randint(500, 1000),
            'user_agent': 'bot/1.0',
            'status_code': 403 if i % 3 == 0 else 200,
            'response_time_ms': np.random.uniform(200, 400)
        }
        
        result = engine.predict_anomaly('192.168.1.100', request)
        
        if result['is_anomaly']:
            print(f"[ANOMALY] Request {i+1}: Score = {result['anomaly_score']:.4f}, "
                  f"Risk = {result['risk_score']:.4f}")
            engine.log_anomaly(result)
    
    # Performance stats
    print("\n" + "="*80)
    print("PERFORMANCE STATISTICS")
    print("="*80)
    
    stats = engine.get_performance_stats()
    print(f"Total inferences:     {stats['total_inferences']}")
    print(f"Mean latency:         {stats['mean_inference_time_ms']:.2f} ms")
    print(f"Median latency:       {stats['median_inference_time_ms']:.2f} ms")
    print(f"95th percentile:      {stats['p95_inference_time_ms']:.2f} ms")
    print(f"99th percentile:      {stats['p99_inference_time_ms']:.2f} ms")
    print(f"Max latency:          {stats['max_inference_time_ms']:.2f} ms")
    
    print("\n" + "="*80)
    print("REAL-TIME INFERENCE COMPLETE")
    print("="*80)
    print(f"Anomaly log: {engine.log_path}")


if __name__ == "__main__":
    demo_realtime_inference()
