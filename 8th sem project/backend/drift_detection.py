"""
Concept Drift Detection Module

Monitors distribution changes in key features using Kolmogorov-Smirnov test:
- Compares training vs live data distributions
- Tracks: latency, error_rate, request_rate, burst_score
- Triggers alerts when p-value < 0.05
- Logs results to drift_report.json
- Does NOT retrain automatically (requires manual intervention)

Statistical rigor: two-sample KS test with significance level α = 0.05
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from scipy.stats import ks_2samp, wasserstein_distance
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class ConceptDriftDetector:
    """
    Detects distribution drift in feature space using statistical tests.
    """
    
    def __init__(
        self,
        reference_data_path: str = None,
        output_dir: str = 'evaluation_results/drift_monitoring',
        alert_threshold: float = 0.05,
        monitored_features: List[str] = None
    ):
        """
        Initialize drift detector.
        
        Args:
            reference_data_path: Path to reference (training) data CSV
            output_dir: Directory for drift reports
            alert_threshold: p-value threshold for drift alert (default: 0.05)
            monitored_features: Features to monitor for drift
        """
        self.reference_data_path = reference_data_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.alert_threshold = alert_threshold
        
        # Default monitored features
        self.monitored_features = monitored_features or [
            'avg_response_time',    # latency
            'error_rate',           # error rate
            'request_rate',         # request rate
            'max_response_time'     # burst indicator
        ]
        
        self.reference_distributions = {}
        self.drift_history = []
        
        # Load reference data if provided
        if reference_data_path and Path(reference_data_path).exists():
            self.load_reference_data(reference_data_path)
    
    def load_reference_data(self, data_path: str) -> None:
        """
        Load reference (training) data for baseline distributions.
        
        Args:
            data_path: Path to CSV file with training data
        """
        df = pd.read_csv(data_path)
        
        print(f"[OK] Loaded reference data: {len(df)} samples")
        
        # Store distributions for each monitored feature
        for feature in self.monitored_features:
            if feature in df.columns:
                self.reference_distributions[feature] = df[feature].dropna().values
                print(f"  Feature: {feature:25s} - {len(self.reference_distributions[feature])} values")
            else:
                print(f"  [WARN] Feature {feature} not found in reference data")
    
    def compute_ks_statistic(
        self,
        reference: np.ndarray,
        current: np.ndarray
    ) -> Tuple[float, float]:
        """
        Compute Kolmogorov-Smirnov two-sample test.
        
        Args:
            reference: Reference distribution
            current: Current (live) distribution
            
        Returns:
            Tuple of (KS statistic, p-value)
        """
        if len(reference) == 0 or len(current) == 0:
            return 0.0, 1.0
        
        statistic, p_value = ks_2samp(reference, current)
        return float(statistic), float(p_value)
    
    def compute_wasserstein_distance(
        self,
        reference: np.ndarray,
        current: np.ndarray
    ) -> float:
        """
        Compute Wasserstein (Earth Mover's) distance.
        
        Provides magnitude of distribution shift.
        
        Args:
            reference: Reference distribution
            current: Current distribution
            
        Returns:
            Wasserstein distance
        """
        if len(reference) == 0 or len(current) == 0:
            return 0.0
        
        return float(wasserstein_distance(reference, current))
    
    def detect_drift(
        self,
        current_data: pd.DataFrame,
        timestamp: str = None
    ) -> Dict[str, Any]:
        """
        Detect drift in current data compared to reference.
        
        Args:
            current_data: DataFrame with current (live) feature data
            timestamp: Timestamp for this drift check (optional)
            
        Returns:
            Dictionary with drift detection results
        """
        if not self.reference_distributions:
            raise ValueError("No reference distributions loaded")
        
        timestamp = timestamp or datetime.utcnow().isoformat()
        
        drift_results = {
            'timestamp': timestamp,
            'n_samples_current': len(current_data),
            'features': {},
            'overall_drift_detected': False,
            'drifted_features': []
        }
        
        for feature in self.monitored_features:
            if feature not in self.reference_distributions:
                continue
            
            if feature not in current_data.columns:
                print(f"  [WARN] Feature {feature} not in current data")
                continue
            
            reference = self.reference_distributions[feature]
            current = current_data[feature].dropna().values
            
            # Compute KS test
            ks_stat, p_value = self.compute_ks_statistic(reference, current)
            
            # Compute Wasserstein distance
            w_distance = self.compute_wasserstein_distance(reference, current)
            
            # Determine drift
            drift_detected = p_value < self.alert_threshold
            
            if drift_detected:
                drift_results['drifted_features'].append(feature)
                drift_results['overall_drift_detected'] = True
            
            # Store feature-level results
            drift_results['features'][feature] = {
                'ks_statistic': ks_stat,
                'p_value': p_value,
                'wasserstein_distance': w_distance,
                'drift_detected': drift_detected,
                'reference_mean': float(np.mean(reference)),
                'reference_std': float(np.std(reference)),
                'current_mean': float(np.mean(current)),
                'current_std': float(np.std(current)),
                'mean_shift': float(np.mean(current) - np.mean(reference))
            }
        
        # Log to history
        self.drift_history.append(drift_results)
        
        return drift_results
    
    def save_drift_report(
        self,
        drift_results: Dict[str, Any],
        filename: str = 'drift_report.json'
    ) -> None:
        """
        Save drift detection results to JSON file.
        
        Args:
            drift_results: Results from detect_drift()
            filename: Output filename
        """
        output_path = self.output_dir / filename
        
        # Load existing reports if available
        if output_path.exists():
            with open(output_path, 'r') as f:
                existing_reports = json.load(f)
        else:
            existing_reports = {'drift_checks': []}
        
        # Append new result
        existing_reports['drift_checks'].append(drift_results)
        existing_reports['last_updated'] = datetime.utcnow().isoformat()
        existing_reports['total_checks'] = len(existing_reports['drift_checks'])
        
        # Save
        with open(output_path, 'w') as f:
            json.dump(existing_reports, f, indent=2)
        
        print(f"[OK] Saved drift report: {output_path}")
    
    def generate_drift_summary(self) -> Dict[str, Any]:
        """
        Generate summary of drift detection history.
        
        Returns:
            Summary statistics
        """
        if not self.drift_history:
            return {'message': 'No drift checks performed yet'}
        
        total_checks = len(self.drift_history)
        drift_count = sum(1 for result in self.drift_history if result['overall_drift_detected'])
        
        # Feature-level drift frequency
        feature_drift_counts = {}
        for feature in self.monitored_features:
            feature_drift_counts[feature] = sum(
                1 for result in self.drift_history
                if feature in result.get('drifted_features', [])
            )
        
        summary = {
            'total_checks': total_checks,
            'drift_detected_count': drift_count,
            'drift_rate': drift_count / total_checks if total_checks > 0 else 0.0,
            'feature_drift_frequency': feature_drift_counts,
            'most_drifted_feature': max(feature_drift_counts, key=feature_drift_counts.get) if feature_drift_counts else None
        }
        
        return summary
    
    def print_drift_report(self, drift_results: Dict[str, Any]) -> None:
        """
        Print formatted drift detection report.
        
        Args:
            drift_results: Results from detect_drift()
        """
        print("\n" + "="*80)
        print("CONCEPT DRIFT DETECTION REPORT")
        print("="*80)
        print(f"Timestamp: {drift_results['timestamp']}")
        print(f"Current samples: {drift_results['n_samples_current']}")
        print(f"Alert threshold (α): {self.alert_threshold}")
        print(f"\nOverall drift detected: {'YES' if drift_results['overall_drift_detected'] else 'NO'}")
        
        if drift_results['drifted_features']:
            print(f"\nDrifted features: {', '.join(drift_results['drifted_features'])}")
        
        print("\nFeature-level Analysis:")
        print("-"*80)
        print(f"{'Feature':<25s} {'KS Stat':>10s} {'p-value':>10s} {'W-Dist':>10s} {'Drift':>8s}")
        print("-"*80)
        
        for feature, stats in drift_results['features'].items():
            drift_flag = "[DRIFT]" if stats['drift_detected'] else "  OK  "
            print(f"{feature:<25s} {stats['ks_statistic']:>10.4f} {stats['p_value']:>10.4f} "
                  f"{stats['wasserstein_distance']:>10.4f} {drift_flag:>8s}")
        
        print("-"*80)
        
        # Show distribution shifts
        print("\nDistribution Shifts:")
        print("-"*80)
        print(f"{'Feature':<25s} {'Ref Mean':>12s} {'Curr Mean':>12s} {'Shift':>12s}")
        print("-"*80)
        
        for feature, stats in drift_results['features'].items():
            print(f"{feature:<25s} {stats['reference_mean']:>12.4f} {stats['current_mean']:>12.4f} "
                  f"{stats['mean_shift']:>+12.4f}")
        
        print("="*80)
    
    def continuous_monitoring(
        self,
        current_data: pd.DataFrame,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Perform drift detection and automatically save report.
        
        Args:
            current_data: Current data to check for drift
            auto_save: Whether to automatically save report
            
        Returns:
            Drift detection results
        """
        drift_results = self.detect_drift(current_data)
        
        # Print report
        self.print_drift_report(drift_results)
        
        # Save if enabled
        if auto_save:
            self.save_drift_report(drift_results)
        
        # Alert if drift detected
        if drift_results['overall_drift_detected']:
            print("\n[ALERT] Concept drift detected!")
            print(f"Affected features: {', '.join(drift_results['drifted_features'])}")
            print("Consider retraining models or investigating data changes.")
        
        return drift_results


def demo_drift_detection():
    """
    Demo: Detect concept drift using synthetic data.
    """
    print("="*80)
    print("CONCEPT DRIFT DETECTION DEMO")
    print("="*80)
    
    # Generate reference (training) data
    from synthetic_data_generator import SyntheticDataGenerator
    
    generator = SyntheticDataGenerator(random_state=42)
    X_train, y_train = generator.generate_dataset(n_samples=1000, anomaly_ratio=0.08)
    
    # Save reference data
    reference_path = Path('datasets/processed/drift_reference_data.csv')
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    X_train.to_csv(reference_path, index=False)
    
    print(f"\n[OK] Created reference data: {reference_path}")
    
    # Initialize detector
    detector = ConceptDriftDetector(
        reference_data_path=str(reference_path),
        alert_threshold=0.05
    )
    
    # Scenario 1: No drift (similar distribution)
    print("\n" + "="*80)
    print("SCENARIO 1: No Drift (Similar Distribution)")
    print("="*80)
    
    X_current_1, _ = generator.generate_dataset(n_samples=500, anomaly_ratio=0.08)
    drift_results_1 = detector.continuous_monitoring(X_current_1)
    
    # Scenario 2: Moderate drift (increased latency)
    print("\n" + "="*80)
    print("SCENARIO 2: Moderate Drift (Increased Latency)")
    print("="*80)
    
    generator_drift = SyntheticDataGenerator(random_state=43)
    X_current_2, _ = generator_drift.generate_dataset(n_samples=500, anomaly_ratio=0.08)
    
    # Artificially increase latency to simulate drift
    X_current_2['avg_response_time'] *= 1.5
    X_current_2['max_response_time'] *= 1.6
    
    drift_results_2 = detector.continuous_monitoring(X_current_2)
    
    # Scenario 3: Severe drift (increased error rate)
    print("\n" + "="*80)
    print("SCENARIO 3: Severe Drift (Increased Error Rate)")
    print("="*80)
    
    generator_drift2 = SyntheticDataGenerator(random_state=44)
    X_current_3, _ = generator_drift2.generate_dataset(n_samples=500, anomaly_ratio=0.15)
    
    # Artificially increase error rate
    X_current_3['error_rate'] *= 3.0
    X_current_3['request_rate'] *= 2.0
    
    drift_results_3 = detector.continuous_monitoring(X_current_3)
    
    # Summary
    print("\n" + "="*80)
    print("DRIFT MONITORING SUMMARY")
    print("="*80)
    
    summary = detector.generate_drift_summary()
    print(f"Total checks: {summary['total_checks']}")
    print(f"Drift detected: {summary['drift_detected_count']}")
    print(f"Drift rate: {summary['drift_rate']*100:.1f}%")
    print(f"\nFeature drift frequency:")
    for feature, count in summary['feature_drift_frequency'].items():
        print(f"  {feature:25s}: {count}/{summary['total_checks']}")
    print(f"\nMost drifted feature: {summary['most_drifted_feature']}")
    
    print("\n" + "="*80)
    print("DRIFT DETECTION COMPLETE")
    print("="*80)
    print(f"Reports saved to: {detector.output_dir}")


if __name__ == "__main__":
    demo_drift_detection()
