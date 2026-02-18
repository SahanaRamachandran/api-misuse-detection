"""
Ensemble Threat Scoring Engine

Combines multiple detection methods into a unified threat score:
- Random Forest probability
- Isolation Forest anomaly score
- Rule-based heuristic score
- Weighted ensemble with configurable weights
- Normalized to 0-1 scale
- Risk levels: Low (0-0.3), Medium (0.3-0.7), High (0.7-1.0)

Provides more robust detection than single-model approach.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class EnsembleThreatScorer:
    """
    Ensemble-based threat scoring combining multiple detection models.
    """
    
    def __init__(
        self,
        models_dir: str = 'models',
        rf_model_name: str = 'robust_random_forest',
        iso_model_name: str = 'robust_isolation_forest',
        weights: Dict[str, float] = None
    ):
        """
        Initialize ensemble scorer.
        
        Args:
            models_dir: Directory containing models
            rf_model_name: Random Forest model name
            iso_model_name: Isolation Forest model name
            weights: Dictionary with model weights (default: equal weighting)
        """
        self.models_dir = Path(models_dir)
        
        # Default weights (can be tuned)
        self.weights = weights or {
            'random_forest': 0.4,
            'isolation_forest': 0.3,
            'heuristic': 0.3
        }
        
        # Normalize weights to sum to 1
        total_weight = sum(self.weights.values())
        self.weights = {k: v/total_weight for k, v in self.weights.items()}
        
        # Load models
        self.rf_model = None
        self.rf_scaler = None
        self.iso_model = None
        self.iso_scaler = None
        
        self.load_models(rf_model_name, iso_model_name)
        
        # Risk level thresholds
        self.risk_thresholds = {
            'low': (0.0, 0.3),
            'medium': (0.3, 0.7),
            'high': (0.7, 1.0)
        }
    
    def load_models(self, rf_name: str, iso_name: str) -> None:
        """
        Load Random Forest and Isolation Forest models.
        
        Args:
            rf_name: Random Forest model name
            iso_name: Isolation Forest model name
        """
        # Load Random Forest
        rf_path = self.models_dir / f'{rf_name}.pkl'
        rf_scaler_path = self.models_dir / f'{rf_name}_scaler.pkl'
        
        if rf_path.exists() and rf_scaler_path.exists():
            self.rf_model = joblib.load(rf_path)
            self.rf_scaler = joblib.load(rf_scaler_path)
            print(f"[OK] Loaded Random Forest: {rf_name}")
        else:
            print(f"[WARN] Random Forest not found: {rf_name}")
        
        # Load Isolation Forest
        iso_path = self.models_dir / f'{iso_name}.pkl'
        iso_scaler_path = self.models_dir / f'{iso_name}_scaler.pkl'
        
        if iso_path.exists() and iso_scaler_path.exists():
            self.iso_model = joblib.load(iso_path)
            self.iso_scaler = joblib.load(iso_scaler_path)
            print(f"[OK] Loaded Isolation Forest: {iso_name}")
        else:
            print(f"[WARN] Isolation Forest not found: {iso_name}")
    
    def _get_rf_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get Random Forest anomaly probability.
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of anomaly probabilities (0-1)
        """
        if self.rf_model is None:
            return np.zeros(len(X))
        
        X_scaled = self.rf_scaler.transform(X.values if isinstance(X, pd.DataFrame) else X)
        probabilities = self.rf_model.predict_proba(X_scaled)[:, 1]
        return probabilities
    
    def _get_iso_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Get Isolation Forest anomaly score (normalized to 0-1).
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of anomaly scores (0-1, higher = more anomalous)
        """
        if self.iso_model is None:
            return np.zeros(len(X))
        
        X_scaled = self.iso_scaler.transform(X.values if isinstance(X, pd.DataFrame) else X)
        
        # Get anomaly scores (more negative = more anomalous)
        scores = self.iso_model.score_samples(X_scaled)
        
        # Normalize to 0-1 range (invert so higher = more anomalous)
        scores_normalized = 1 - (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
        
        return scores_normalized
    
    def _get_heuristic_score(self, X: pd.DataFrame) -> np.ndarray:
        """
        Compute rule-based heuristic anomaly score.
        
        Rules:
        - High request rate (> 50 req/s)
        - High error rate (> 30%)
        - High response time (> 500ms)
        - Low endpoint diversity (< 3 unique endpoints)
        
        Args:
            X: Feature matrix
            
        Returns:
            Array of heuristic scores (0-1)
        """
        scores = np.zeros(len(X))
        
        # Convert to DataFrame if needed
        if not isinstance(X, pd.DataFrame):
            return scores
        
        # Rule 1: High request rate
        if 'request_rate' in X.columns:
            high_rate = (X['request_rate'] > 50).astype(float)
            scores += high_rate * 0.3
        
        # Rule 2: High error rate
        if 'error_rate' in X.columns:
            high_errors = (X['error_rate'] > 0.3).astype(float)
            scores += high_errors * 0.3
        
        # Rule 3: High response time
        if 'avg_response_time' in X.columns:
            high_latency = (X['avg_response_time'] > 500).astype(float)
            scores += high_latency * 0.2
        
        # Rule 4: Low endpoint diversity (potential scanning)
        if 'unique_endpoint_count' in X.columns:
            low_diversity = (X['unique_endpoint_count'] < 3).astype(float)
            scores += low_diversity * 0.2
        
        # Clip to [0, 1]
        scores = np.clip(scores, 0, 1)
        
        return scores
    
    def compute_ensemble_score(
        self,
        X: pd.DataFrame,
        return_components: bool = False
    ) -> np.ndarray:
        """
        Compute weighted ensemble threat score.
        
        Args:
            X: Feature matrix
            return_components: If True, return individual component scores
            
        Returns:
            Array of ensemble threat scores (0-1)
            If return_components=True, returns (ensemble_scores, components_dict)
        """
        # Get individual scores
        rf_scores = self._get_rf_score(X)
        iso_scores = self._get_iso_score(X)
        heuristic_scores = self._get_heuristic_score(X)
        
        # Weighted ensemble
        ensemble_scores = (
            self.weights['random_forest'] * rf_scores +
            self.weights['isolation_forest'] * iso_scores +
            self.weights['heuristic'] * heuristic_scores
        )
        
        # Ensure [0, 1] range
        ensemble_scores = np.clip(ensemble_scores, 0, 1)
        
        if return_components:
            components = {
                'random_forest': rf_scores,
                'isolation_forest': iso_scores,
                'heuristic': heuristic_scores,
                'ensemble': ensemble_scores
            }
            return ensemble_scores, components
        
        return ensemble_scores
    
    def classify_risk_level(self, score: float) -> str:
        """
        Classify score into risk level.
        
        Args:
            score: Threat score (0-1)
            
        Returns:
            Risk level: 'low', 'medium', or 'high'
        """
        for level, (low, high) in self.risk_thresholds.items():
            if low <= score < high:
                return level
        
        return 'high'  # If score >= 0.7
    
    def batch_score(
        self,
        X: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Score a batch of samples with detailed results.
        
        Args:
            X: Feature matrix
            
        Returns:
            List of dictionaries with scoring details
        """
        ensemble_scores, components = self.compute_ensemble_score(X, return_components=True)
        
        results = []
        for i in range(len(X)):
            result = {
                'sample_index': i,
                'ensemble_score': float(ensemble_scores[i]),
                'risk_level': self.classify_risk_level(ensemble_scores[i]),
                'component_scores': {
                    'random_forest': float(components['random_forest'][i]),
                    'isolation_forest': float(components['isolation_forest'][i]),
                    'heuristic': float(components['heuristic'][i])
                },
                'weights': self.weights,
                'features': X.iloc[i].to_dict() if isinstance(X, pd.DataFrame) else {}
            }
            results.append(result)
        
        return results
    
    def update_weights(self, new_weights: Dict[str, float]) -> None:
        """
        Update ensemble weights.
        
        Args:
            new_weights: Dictionary with new weights
        """
        # Normalize
        total = sum(new_weights.values())
        self.weights = {k: v/total for k, v in new_weights.items()}
        
        print(f"[OK] Updated weights: {self.weights}")
    
    def get_risk_distribution(
        self,
        X: pd.DataFrame
    ) -> Dict[str, int]:
        """
        Get distribution of risk levels in dataset.
        
        Args:
            X: Feature matrix
            
        Returns:
            Dictionary with count of each risk level
        """
        ensemble_scores = self.compute_ensemble_score(X)
        
        distribution = {'low': 0, 'medium': 0, 'high': 0}
        
        for score in ensemble_scores:
            level = self.classify_risk_level(score)
            distribution[level] += 1
        
        return distribution


def demo_ensemble_scoring():
    """
    Demo: Ensemble threat scoring on test data.
    """
    print("="*80)
    print("ENSEMBLE THREAT SCORING DEMO")
    print("="*80)
    
    # Initialize ensemble scorer
    try:
        scorer = EnsembleThreatScorer(
            rf_model_name='robust_random_forest',
            iso_model_name='robust_isolation_forest'
        )
    except Exception as e:
        print(f"\n[ERROR] {e}")
        print("Please train robust models first using train_robust_models.py")
        return
    
    print(f"\nEnsemble weights:")
    for component, weight in scorer.weights.items():
        print(f"  {component:20s}: {weight:.2f}")
    
    # Generate test data
    from synthetic_data_generator import SyntheticDataGenerator
    
    generator = SyntheticDataGenerator(random_state=42)
    X_test, y_test = generator.generate_dataset(n_samples=500, anomaly_ratio=0.1)
    
    print(f"\nTest data: {len(X_test)} samples ({y_test.sum()} anomalies)")
    
    # Compute ensemble scores
    print("\n=== Computing Ensemble Scores ===")
    
    ensemble_scores, components = scorer.compute_ensemble_score(X_test, return_components=True)
    
    # Show statistics
    print(f"\nEnsemble Score Statistics:")
    print(f"  Mean:   {np.mean(ensemble_scores):.4f}")
    print(f"  Median: {np.median(ensemble_scores):.4f}")
    print(f"  Std:    {np.std(ensemble_scores):.4f}")
    print(f"  Min:    {np.min(ensemble_scores):.4f}")
    print(f"  Max:    {np.max(ensemble_scores):.4f}")
    
    # Component score statistics
    print(f"\nComponent Score Statistics:")
    for component in ['random_forest', 'isolation_forest', 'heuristic']:
        scores = components[component]
        print(f"\n{component.upper()}:")
        print(f"  Mean:   {np.mean(scores):.4f}")
        print(f"  Median: {np.median(scores):.4f}")
        print(f"  Std:    {np.std(scores):.4f}")
    
    # Risk distribution
    print("\n=== Risk Level Distribution ===")
    
    distribution = scorer.get_risk_distribution(X_test)
    total = len(X_test)
    
    print(f"\nLow Risk    (0.0-0.3): {distribution['low']:4d} samples ({distribution['low']/total*100:5.1f}%)")
    print(f"Medium Risk (0.3-0.7): {distribution['medium']:4d} samples ({distribution['medium']/total*100:5.1f}%)")
    print(f"High Risk   (0.7-1.0): {distribution['high']:4d} samples ({distribution['high']/total*100:5.1f}%)")
    
    # Show detailed results for top 10 highest-risk samples
    print("\n=== Top 10 Highest-Risk Samples ===")
    
    results = scorer.batch_score(X_test)
    sorted_results = sorted(results, key=lambda x: x['ensemble_score'], reverse=True)[:10]
    
    print(f"\n{'Index':<8s} {'Ensemble':>10s} {'RF':>8s} {'ISO':>8s} {'Heur':>8s} {'Risk':<10s}")
    print("-"*60)
    
    for r in sorted_results:
        print(f"{r['sample_index']:<8d} {r['ensemble_score']:>10.4f} "
              f"{r['component_scores']['random_forest']:>8.4f} "
              f"{r['component_scores']['isolation_forest']:>8.4f} "
              f"{r['component_scores']['heuristic']:>8.4f} "
              f"{r['risk_level'].upper():<10s}")
    
    # Compare with ground truth
    print("\n=== Performance vs Ground Truth ===")
    
    # Using 0.5 as threshold
    predictions = (ensemble_scores >= 0.5).astype(int)
    
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    
    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, zero_division=0)
    recall = recall_score(y_test, predictions, zero_division=0)
    f1 = f1_score(y_test, predictions, zero_division=0)
    
    print(f"\nAccuracy:  {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    
    print("\n" + "="*80)
    print("ENSEMBLE SCORING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    demo_ensemble_scoring()
