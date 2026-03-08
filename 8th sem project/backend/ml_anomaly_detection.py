"""
ML-Based Anomaly Detection Integration Module

Integrates multiple ML models for comprehensive anomaly detection:
- CIC IDS 2017 models for network traffic anomalies
- CSIC 2010 HTTP models for HTTP request anomalies

Features:
- Ensemble predictions via majority voting
- Error rate and failure probability calculations
- IP blocking management
- Support for both network and HTTP protocol detection

Author: Traffic Monitoring System
Date: 2026
"""

import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Import TensorFlow/Keras for autoencoder
try:
    from tensorflow import keras
    import tensorflow as tf
    # Suppress TensorFlow warnings
    tf.get_logger().setLevel('ERROR')
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("Warning: TensorFlow not available. Autoencoder detection disabled.")


class MLAnomalyDetector:
    """
    Comprehensive ML-based anomaly detection system.
    
    Integrates multiple models:
    - CIC IDS 2017: LightGBM, LightGBMXT, CatBoost, RandomForest (Gini/Entropy), ExtraTrees
    - CSIC 2010 HTTP: XGBoost, Autoencoder
    """
    
    def __init__(self, models_dir: str = None):
        """
        Initialize the ML anomaly detector.
        
        Args:
            models_dir: Directory containing the trained models
        """
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), 'models')
        
        self.models_dir = Path(models_dir)
        self.cic_models = {}
        self.csic_models = {}
        self.scalers = {}
        self.blocked_ips = set()
        self.prediction_history = defaultdict(list)
        self.ae_threshold = 0.1  # Default autoencoder threshold
        
        # Model names for CIC IDS 2017 (network traffic)
        self.cic_model_names = [
            'LightGBM_BAG_L1',
            'LightGBMXT_BAG_L1',
            'CatBoost_BAG_L2',
            'RandomForestGini_BAG_L1',
            'RandomForestEntr_BAG_L1',
            'ExtraTreesGini_BAG_L1'
        ]
        
        print("ML Anomaly Detector initialized")
        print(f"Models directory: {self.models_dir}")
    
    def load_models(self) -> bool:
        """
        Load all ML models from disk.
        
        Returns:
            bool: True if models loaded successfully, False otherwise
        """
        try:
            # Load CIC IDS 2017 models
            cic_dir = self.models_dir / 'CIC-IDS'
            
            if not cic_dir.exists():
                print(f"Warning: CIC-IDS models directory not found: {cic_dir}")
                return False
            
            print("\n" + "="*60)
            print("LOADING CIC IDS 2017 MODELS (Network Traffic)")
            print("="*60)
            
            for model_name in self.cic_model_names:
                model_path = cic_dir / model_name / 'model.pkl'
                
                if model_path.exists():
                    try:
                        self.cic_models[model_name] = joblib.load(model_path)
                        print(f"✓ Loaded: {model_name}")
                    except Exception as e:
                        print(f"✗ Failed to load {model_name}: {e}")
                else:
                    print(f"✗ Model not found: {model_path}")
            
            # Load CSIC 2010 HTTP models
            csic_dir = self.models_dir / 'CSIC'
            
            print("\n" + "="*60)
            print("LOADING CSIC 2010 HTTP MODELS")
            print("="*60)
            
            # Try to load XGBoost model (support both naming conventions)
            xgb_paths = [
                csic_dir / 'xgboost.pkl',
                csic_dir / 'xgboost_model.pkl'
            ]
            
            xgb_loaded = False
            for xgb_path in xgb_paths:
                if xgb_path.exists() and not xgb_loaded:
                    try:
                        self.csic_models['XGBoost'] = joblib.load(xgb_path)
                        print(f"✓ Loaded: XGBoost from {xgb_path.name}")
                        xgb_loaded = True
                        break
                    except Exception as e:
                        print(f"✗ Failed to load {xgb_path.name}: {e}")
            
            if not xgb_loaded:
                print("ℹ XGBoost model not found")
                print("  Tried: xgboost.pkl, xgboost_model.pkl")
                print("  Note: Export from CSIC notebook to get the model")
            
            # Try to load Autoencoder model (.h5 file)
            # Note: Autoencoder currently not integrated - file contains only weights
            # Full model architecture needed for proper loading
            ae_path = csic_dir / 'model.weights.h5'
            if ae_path.exists() and KERAS_AVAILABLE:
                print(f"ℹ Autoencoder weights found at {ae_path.name}")
                print("  Note: Full model architecture required for integration")
                print("  XGBoost model provides HTTP anomaly detection")
                # Skipping autoencoder for now - would need full model file
                pass
            elif not KERAS_AVAILABLE:
                print("ℹ TensorFlow/Keras not available - Autoencoder disabled")
                print("  Install: pip install tensorflow")
            else:
                print("ℹ Autoencoder model file not found")
                print("  Note: Train and export from CSIC notebook if needed")
            
            print("\n" + "="*60)
            print(f"SUMMARY: {len(self.cic_models)} CIC models, {len(self.csic_models)} CSIC models loaded")
            print("="*60 + "\n")
            
            return len(self.cic_models) > 0
            
        except Exception as e:
            print(f"Error loading models: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict_anomaly(
        self, 
        data: Union[np.ndarray, pd.DataFrame, Dict], 
        protocol: str = 'network'
    ) -> Dict[str, Any]:
        """
        Predict anomaly using appropriate models based on protocol.
        
        Args:
            data: Input features (array, DataFrame, or dict)
            protocol: 'network' for CIC IDS models, 'http' for CSIC models
        
        Returns:
            Dictionary containing:
                - is_anomaly: bool
                - confidence: float (0-1)
                - individual_predictions: dict of model predictions
                - ensemble_prediction: int (0 or 1)
                - error_rate: float
                - failure_probability: float
        """
        # Convert input to numpy array
        X = self._prepare_input(data)
        
        if protocol == 'network':
            return self._predict_network_anomaly(X)
        elif protocol == 'http':
            return self._predict_http_anomaly(X)
        else:
            raise ValueError(f"Unknown protocol: {protocol}. Use 'network' or 'http'")
    
    def _prepare_input(self, data: Union[np.ndarray, pd.DataFrame, Dict]) -> np.ndarray:
        """
        Convert input data to numpy array format.
        
        Args:
            data: Input data in various formats
        
        Returns:
            numpy array
        """
        if isinstance(data, np.ndarray):
            if len(data.shape) == 1:
                return data.reshape(1, -1)
            return data
        elif isinstance(data, pd.DataFrame):
            return data.values
        elif isinstance(data, dict):
            return np.array(list(data.values())).reshape(1, -1)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    def _predict_network_anomaly(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Predict network traffic anomaly using CIC IDS 2017 models.
        Uses majority voting ensemble.
        
        Args:
            X: Input features
        
        Returns:
            Prediction results
        """
        if not self.cic_models:
            raise RuntimeError("CIC IDS models not loaded. Call load_models() first.")
        
        individual_predictions = {}
        predictions_list = []
        
        # Get predictions from each model
        for model_name, model in self.cic_models.items():
            try:
                # Most AutoGluon models have predict method returning class labels
                pred = model.predict(X)
                
                # Convert to binary (0: normal, 1: anomaly)
                if isinstance(pred, (list, np.ndarray)):
                    pred_binary = int(pred[0]) if len(pred) > 0 else 0
                else:
                    pred_binary = int(pred)
                
                individual_predictions[model_name] = pred_binary
                predictions_list.append(pred_binary)
                
            except Exception as e:
                print(f"Warning: Prediction failed for {model_name}: {e}")
                individual_predictions[model_name] = None
        
        # Ensemble via majority vote
        if predictions_list:
            vote_counts = Counter(predictions_list)
            ensemble_prediction = vote_counts.most_common(1)[0][0]
            
            # Confidence = proportion of models agreeing with majority
            confidence = vote_counts[ensemble_prediction] / len(predictions_list)
        else:
            ensemble_prediction = 0
            confidence = 0.0
        
        # Calculate metrics
        y_true = np.array([0] * len(predictions_list))  # Placeholder
        y_pred = np.array(predictions_list)
        
        error_rate = self.calculate_error_rate(y_true, y_pred)
        failure_prob = self.calculate_failure_probability(y_pred)
        
        return {
            'is_anomaly': bool(ensemble_prediction == 1),
            'confidence': float(confidence),
            'ensemble_prediction': int(ensemble_prediction),
            'individual_predictions': individual_predictions,
            'num_models_voted': len(predictions_list),
            'error_rate': float(error_rate),
            'failure_probability': float(failure_prob),
            'protocol': 'network'
        }
    
    def _predict_http_anomaly(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Predict HTTP request anomaly using CSIC 2010 models.
        Combines XGBoost and Autoencoder predictions.
        
        Args:
            X: Input features
        
        Returns:
            Prediction results
        """
        if not self.csic_models:
            print("Warning: CSIC HTTP models not loaded. Returning default prediction.")
            return {
                'is_anomaly': False,
                'confidence': 0.0,
                'ensemble_prediction': 0,
                'individual_predictions': {},
                'num_models_voted': 0,
                'error_rate': 0.0,
                'failure_probability': 0.0,
                'protocol': 'http'
            }
        
        individual_predictions = {}
        predictions_list = []
        
        # XGBoost prediction
        if 'XGBoost' in self.csic_models:
            try:
                xgb_pred = self.csic_models['XGBoost'].predict(X)
                pred_binary = int(xgb_pred[0]) if isinstance(xgb_pred, (list, np.ndarray)) else int(xgb_pred)
                individual_predictions['XGBoost'] = pred_binary
                predictions_list.append(pred_binary)
            except Exception as e:
                print(f"Warning: XGBoost prediction failed: {e}")
        
        # Autoencoder prediction (if loaded)
        if 'Autoencoder' in self.csic_models:
            try:
                autoencoder = self.csic_models['Autoencoder']
                
                # Get reconstruction from autoencoder
                reconstruction = autoencoder.predict(X, verbose=0)
                
                # Calculate mean squared error (reconstruction error)
                mse = np.mean(np.square(X - reconstruction))
                
                # Compare to threshold to determine anomaly
                # Higher reconstruction error = anomaly
                threshold = getattr(self, 'ae_threshold', 0.1)
                ae_pred = 1 if mse > threshold else 0
                
                individual_predictions['Autoencoder'] = ae_pred
                predictions_list.append(ae_pred)
            except Exception as e:
                print(f"Warning: Autoencoder prediction failed: {e}")
        
        # Ensemble prediction
        if predictions_list:
            vote_counts = Counter(predictions_list)
            ensemble_prediction = vote_counts.most_common(1)[0][0]
            confidence = vote_counts[ensemble_prediction] / len(predictions_list)
        else:
            ensemble_prediction = 0
            confidence = 0.0
        
        # Calculate metrics
        y_true = np.array([0] * len(predictions_list))
        y_pred = np.array(predictions_list)
        
        error_rate = self.calculate_error_rate(y_true, y_pred)
        failure_prob = self.calculate_failure_probability(y_pred)
        
        return {
            'is_anomaly': bool(ensemble_prediction == 1),
            'confidence': float(confidence),
            'ensemble_prediction': int(ensemble_prediction),
            'individual_predictions': individual_predictions,
            'num_models_voted': len(predictions_list),
            'error_rate': float(error_rate),
            'failure_probability': float(failure_prob),
            'protocol': 'http'
        }
    
    def calculate_error_rate(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray
    ) -> float:
        """
        Calculate error rate (misclassification rate).
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
        
        Returns:
            Error rate (0-1)
        """
        if len(y_true) == 0 or len(y_pred) == 0:
            return 0.0
        
        try:
            # Ensure same length
            min_len = min(len(y_true), len(y_pred))
            y_true = y_true[:min_len]
            y_pred = y_pred[:min_len]
            
            # Calculate error rate
            errors = np.sum(y_true != y_pred)
            error_rate = errors / len(y_true)
            
            return float(error_rate)
        except Exception as e:
            print(f"Warning: Error rate calculation failed: {e}")
            return 0.0
    
    def calculate_failure_probability(
        self, 
        y_pred: np.ndarray,
        window_size: int = 10
    ) -> float:
        """
        Calculate failure probability based on recent predictions.
        
        Args:
            y_pred: Recent predictions
            window_size: Number of recent predictions to consider
        
        Returns:
            Failure probability (0-1)
        """
        if len(y_pred) == 0:
            return 0.0
        
        try:
            # Take last window_size predictions
            recent_preds = y_pred[-window_size:]
            
            # Failure probability = proportion of anomalies
            failure_prob = np.sum(recent_preds == 1) / len(recent_preds)
            
            return float(failure_prob)
        except Exception as e:
            print(f"Warning: Failure probability calculation failed: {e}")
            return 0.0
    
    def check_and_block_ip(
        self, 
        ip: str, 
        prediction: Dict[str, Any],
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Check if IP should be blocked based on prediction and add to blocklist.
        
        Args:
            ip: IP address
            prediction: Prediction result from predict_anomaly()
            threshold: Confidence threshold for blocking
        
        Returns:
            Dictionary with blocking decision and details
        """
        should_block = False
        reason = ""
        
        # Check if prediction indicates anomaly with high confidence
        if prediction['is_anomaly'] and prediction['confidence'] >= threshold:
            should_block = True
            reason = f"Anomaly detected with {prediction['confidence']:.2%} confidence"
            
            # Add to blocked IPs
            if ip not in self.blocked_ips:
                self.blocked_ips.add(ip)
                action_taken = "IP added to blocklist"
            else:
                action_taken = "IP already in blocklist"
        else:
            action_taken = "No action taken"
            if prediction['is_anomaly']:
                reason = f"Anomaly detected but confidence ({prediction['confidence']:.2%}) below threshold"
            else:
                reason = "No anomaly detected"
        
        # Record in history
        self.prediction_history[ip].append({
            'timestamp': pd.Timestamp.now(),
            'is_anomaly': prediction['is_anomaly'],
            'confidence': prediction['confidence'],
            'blocked': should_block
        })
        
        return {
            'ip': ip,
            'should_block': should_block,
            'is_blocked': ip in self.blocked_ips,
            'reason': reason,
            'action_taken': action_taken,
            'confidence': prediction['confidence'],
            'prediction': prediction
        }
    
    def is_ip_blocked(self, ip: str) -> bool:
        """
        Check if an IP is in the blocklist.
        
        Args:
            ip: IP address to check
        
        Returns:
            True if blocked, False otherwise
        """
        return ip in self.blocked_ips
    
    def unblock_ip(self, ip: str) -> bool:
        """
        Remove an IP from the blocklist.
        
        Args:
            ip: IP address to unblock
        
        Returns:
            True if IP was unblocked, False if not in blocklist
        """
        if ip in self.blocked_ips:
            self.blocked_ips.remove(ip)
            return True
        return False
    
    def get_blocked_ips(self) -> List[str]:
        """
        Get list of all blocked IPs.
        
        Returns:
            List of blocked IP addresses
        """
        return list(self.blocked_ips)
    
    def get_ip_history(self, ip: str, limit: int = 10) -> List[Dict]:
        """
        Get prediction history for an IP.
        
        Args:
            ip: IP address
            limit: Maximum number of records to return
        
        Returns:
            List of prediction records
        """
        if ip not in self.prediction_history:
            return []
        
        history = self.prediction_history[ip]
        return history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about the detector.
        
        Returns:
            Statistics dictionary
        """
        total_predictions = sum(len(hist) for hist in self.prediction_history.values())
        anomaly_predictions = sum(
            sum(1 for record in hist if record['is_anomaly'])
            for hist in self.prediction_history.values()
        )
        
        return {
            'total_ips_seen': len(self.prediction_history),
            'blocked_ips_count': len(self.blocked_ips),
            'total_predictions': total_predictions,
            'anomaly_predictions': anomaly_predictions,
            'anomaly_rate': anomaly_predictions / total_predictions if total_predictions > 0 else 0.0,
            'cic_models_loaded': len(self.cic_models),
            'csic_models_loaded': len(self.csic_models),
            'total_models': len(self.cic_models) + len(self.csic_models)
        }


# Standalone functions for backward compatibility
def load_models(models_dir: str = None) -> MLAnomalyDetector:
    """
    Load all ML models and return detector instance.
    
    Args:
        models_dir: Directory containing models
    
    Returns:
        MLAnomalyDetector instance with loaded models
    """
    detector = MLAnomalyDetector(models_dir)
    detector.load_models()
    return detector


def predict_anomaly(
    detector: MLAnomalyDetector,
    data: Union[np.ndarray, pd.DataFrame, Dict],
    protocol: str = 'network'
) -> Dict[str, Any]:
    """
    Predict anomaly using the detector.
    
    Args:
        detector: MLAnomalyDetector instance
        data: Input features
        protocol: 'network' or 'http'
    
    Returns:
        Prediction results
    """
    return detector.predict_anomaly(data, protocol)


def calculate_error_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate error rate between true and predicted labels.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
    
    Returns:
        Error rate (0-1)
    """
    detector = MLAnomalyDetector()
    return detector.calculate_error_rate(y_true, y_pred)


def calculate_failure_probability(y_pred: np.ndarray, window_size: int = 10) -> float:
    """
    Calculate failure probability from predictions.
    
    Args:
        y_pred: Predicted labels
        window_size: Number of predictions to consider
    
    Returns:
        Failure probability (0-1)
    """
    detector = MLAnomalyDetector()
    return detector.calculate_failure_probability(y_pred, window_size)


def check_and_block_ip(
    detector: MLAnomalyDetector,
    ip: str,
    prediction: Dict[str, Any],
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Check if IP should be blocked based on prediction.
    
    Args:
        detector: MLAnomalyDetector instance
        ip: IP address
        prediction: Prediction result
        threshold: Confidence threshold for blocking
    
    Returns:
        Blocking decision details
    """
    return detector.check_and_block_ip(ip, prediction, threshold)


if __name__ == "__main__":
    """
    Example usage and testing
    """
    print("="*70)
    print("ML ANOMALY DETECTION - TESTING")
    print("="*70 + "\n")
    
    # Initialize detector
    detector = MLAnomalyDetector()
    
    # Load models
    success = detector.load_models()
    
    if success:
        print("\n" + "="*70)
        print("TESTING PREDICTIONS")
        print("="*70 + "\n")
        
        # Test network anomaly detection (if models loaded)
        if detector.cic_models:
            print("Testing Network Traffic Anomaly Detection...")
            # Create dummy network traffic features (adjust size based on actual model requirements)
            dummy_network_data = np.random.randn(1, 10)  # Placeholder
            
            try:
                result = detector.predict_anomaly(dummy_network_data, protocol='network')
                print(f"  Prediction: {'ANOMALY' if result['is_anomaly'] else 'NORMAL'}")
                print(f"  Confidence: {result['confidence']:.2%}")
                print(f"  Models voted: {result['num_models_voted']}")
                print(f"  Error rate: {result['error_rate']:.4f}")
                print(f"  Failure probability: {result['failure_probability']:.4f}")
                
                # Test IP blocking
                print("\nTesting IP Blocking...")
                block_result = detector.check_and_block_ip('192.168.1.100', result)
                print(f"  IP: {block_result['ip']}")
                print(f"  Should block: {block_result['should_block']}")
                print(f"  Reason: {block_result['reason']}")
                print(f"  Action: {block_result['action_taken']}")
                
            except Exception as e:
                print(f"  Error during prediction: {e}")
                import traceback
                traceback.print_exc()
        
        # Display statistics
        print("\n" + "="*70)
        print("STATISTICS")
        print("="*70)
        stats = detector.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*70)
        print("Blocked IPs:", detector.get_blocked_ips())
        print("="*70 + "\n")
    else:
        print("\n⚠ Models could not be loaded. Please check the models directory.")
