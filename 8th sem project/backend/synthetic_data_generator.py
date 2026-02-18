"""
Enhanced Synthetic Data Generator for Robust ML Training

Generates realistic synthetic telemetry samples with various anomaly patterns:
- Sudden spikes (flash crowds, DDoS)
- Gradual attacks (slow rate increases)
- Adversarial subtle anomalies (mimicking normal behavior)
- Combined weak signals (multi-feature anomalies)
- Noise injection (measurement errors)

Features realistic anomaly ratio (5-10%) suitable for production systems.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
import warnings
warnings.filterwarnings('ignore')


class SyntheticDataGenerator:
    """
    Generate synthetic traffic telemetry data with realistic anomaly patterns.
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize the generator.
        
        Args:
            random_state: Random seed for reproducibility
        """
        self.random_state = random_state
        np.random.seed(random_state)
        
        # Feature names matching CSIC dataset structure
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
        
        # Normal behavior baseline statistics
        self.normal_params = {
            'request_rate': {'mean': 10.0, 'std': 3.0, 'min': 1.0, 'max': 25.0},
            'unique_endpoint_count': {'mean': 7.0, 'std': 2.5, 'min': 1, 'max': 15},
            'method_ratio': {'mean': 2.0, 'std': 1.0, 'min': 1.0, 'max': 5.0},
            'avg_payload_size': {'mean': 25.0, 'std': 10.0, 'min': 5.0, 'max': 100.0},
            'error_rate': {'mean': 0.02, 'std': 0.01, 'min': 0.0, 'max': 0.15},
            'repeated_parameter_ratio': {'mean': 0.7, 'std': 0.15, 'min': 0.0, 'max': 1.0},
            'user_agent_entropy': {'mean': 0.0, 'std': 0.1, 'min': -0.5, 'max': 0.5},
            'avg_response_time': {'mean': 160.0, 'std': 25.0, 'min': 50.0, 'max': 300.0},
            'max_response_time': {'mean': 180.0, 'std': 30.0, 'min': 60.0, 'max': 400.0}
        }
    
    def _generate_normal_samples(self, n_samples: int) -> np.ndarray:
        """
        Generate normal (non-anomalous) traffic samples.
        
        Args:
            n_samples: Number of normal samples to generate
            
        Returns:
            Array of shape (n_samples, n_features)
        """
        samples = []
        
        for _ in range(n_samples):
            sample = []
            for feat in self.feature_names:
                params = self.normal_params[feat]
                value = np.random.normal(params['mean'], params['std'])
                # Clip to realistic bounds
                value = np.clip(value, params['min'], params['max'])
                sample.append(value)
            samples.append(sample)
        
        return np.array(samples)
    
    def _generate_sudden_spike_anomalies(self, n_samples: int) -> np.ndarray:
        """
        Generate sudden spike anomalies (e.g., DDoS, flash crowds).
        
        Characteristics:
        - Very high request_rate (5-10x normal)
        - Low unique_endpoint_count (focused attack)
        - High repeated_parameter_ratio
        - Elevated error_rate
        
        Args:
            n_samples: Number of spike anomalies
            
        Returns:
            Array of anomalous samples
        """
        normal_samples = self._generate_normal_samples(n_samples)
        
        # Apply spike transformations
        normal_samples[:, 0] *= np.random.uniform(5, 10, n_samples)  # request_rate
        normal_samples[:, 1] *= np.random.uniform(0.3, 0.6, n_samples)  # fewer unique endpoints
        normal_samples[:, 4] *= np.random.uniform(3, 8, n_samples)  # higher error_rate
        normal_samples[:, 5] = np.random.uniform(0.85, 0.99, n_samples)  # high repeat_rate
        normal_samples[:, 7] *= np.random.uniform(1.5, 3.0, n_samples)  # slower response
        
        # Clip to realistic bounds
        normal_samples = self._clip_to_bounds(normal_samples)
        
        return normal_samples
    
    def _generate_gradual_attack_anomalies(self, n_samples: int) -> np.ndarray:
        """
        Generate gradual attack anomalies (slow rate increases, reconnaissance).
        
        Characteristics:
        - Moderately elevated request_rate (2-3x normal)
        - High unique_endpoint_count (scanning)
        - Slightly elevated error_rate
        - Varied method_ratio
        
        Args:
            n_samples: Number of gradual anomalies
            
        Returns:
            Array of anomalous samples
        """
        normal_samples = self._generate_normal_samples(n_samples)
        
        # Apply gradual attack transformations
        normal_samples[:, 0] *= np.random.uniform(2, 3.5, n_samples)  # moderate request_rate
        normal_samples[:, 1] *= np.random.uniform(1.5, 2.5, n_samples)  # more endpoints
        normal_samples[:, 2] *= np.random.uniform(1.3, 2.0, n_samples)  # varied methods
        normal_samples[:, 4] *= np.random.uniform(2, 4, n_samples)  # elevated error_rate
        
        normal_samples = self._clip_to_bounds(normal_samples)
        
        return normal_samples
    
    def _generate_adversarial_anomalies(self, n_samples: int) -> np.ndarray:
        """
        Generate adversarial subtle anomalies (mimicking normal behavior).
        
        Characteristics:
        - Close to normal in most features
        - Subtle deviations in 2-3 features only
        - Designed to evade basic detection
        
        Args:
            n_samples: Number of adversarial anomalies
            
        Returns:
            Array of anomalous samples
        """
        normal_samples = self._generate_normal_samples(n_samples)
        
        # For each sample, perturb only 2-3 random features slightly
        for i in range(n_samples):
            n_perturb = np.random.randint(2, 4)
            perturb_indices = np.random.choice(len(self.feature_names), n_perturb, replace=False)
            
            for idx in perturb_indices:
                # Subtle perturbation (15-30% deviation)
                perturbation = np.random.uniform(1.15, 1.30)
                if np.random.random() > 0.5:
                    perturbation = 1 / perturbation  # Sometimes decrease
                normal_samples[i, idx] *= perturbation
        
        normal_samples = self._clip_to_bounds(normal_samples)
        
        return normal_samples
    
    def _generate_combined_weak_signals(self, n_samples: int) -> np.ndarray:
        """
        Generate anomalies with combined weak signals across multiple features.
        
        Characteristics:
        - Each feature slightly elevated (10-20%)
        - Combined effect creates anomaly
        - Tests model's ability to detect correlated deviations
        
        Args:
            n_samples: Number of combined anomalies
            
        Returns:
            Array of anomalous samples
        """
        normal_samples = self._generate_normal_samples(n_samples)
        
        # Apply small perturbations to all features
        for i in range(len(self.feature_names)):
            perturbation = np.random.uniform(1.1, 1.25, n_samples)
            normal_samples[:, i] *= perturbation
        
        normal_samples = self._clip_to_bounds(normal_samples)
        
        return normal_samples
    
    def _add_noise(self, samples: np.ndarray, noise_level: float = 0.05) -> np.ndarray:
        """
        Add Gaussian noise to simulate measurement errors and variability.
        
        Args:
            samples: Input samples
            noise_level: Standard deviation of noise as fraction of feature std
            
        Returns:
            Noisy samples
        """
        noise = np.random.normal(0, noise_level, samples.shape)
        return samples + noise * samples
    
    def _clip_to_bounds(self, samples: np.ndarray) -> np.ndarray:
        """
        Clip all features to their realistic bounds.
        
        Args:
            samples: Input samples
            
        Returns:
            Clipped samples
        """
        clipped = samples.copy()
        
        for i, feat in enumerate(self.feature_names):
            params = self.normal_params[feat]
            clipped[:, i] = np.clip(clipped[:, i], params['min'], params['max'])
        
        return clipped
    
    def generate_dataset(
        self,
        n_samples: int = 2000,
        anomaly_ratio: float = 0.08,
        noise_level: float = 0.03
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Generate complete synthetic dataset with realistic anomaly distribution.
        
        Args:
            n_samples: Total number of samples to generate (default: 2000)
            anomaly_ratio: Fraction of anomalous samples (default: 0.08 = 8%)
            noise_level: Noise level to add (default: 0.03 = 3%)
            
        Returns:
            Tuple of (features_df, labels_array)
            - features_df: DataFrame with feature columns
            - labels_array: Binary labels (0=normal, 1=anomaly)
        """
        # Calculate sample counts
        n_anomalies = int(n_samples * anomaly_ratio)
        n_normal = n_samples - n_anomalies
        
        # Distribute anomalies across different types
        anomaly_distribution = {
            'sudden_spike': 0.30,       # 30% sudden spikes
            'gradual_attack': 0.25,     # 25% gradual attacks
            'adversarial': 0.25,        # 25% adversarial
            'combined_weak': 0.20       # 20% combined weak signals
        }
        
        # Generate normal samples
        print(f"Generating {n_normal} normal samples...")
        normal_samples = self._generate_normal_samples(n_normal)
        
        # Generate anomalous samples
        anomaly_samples = []
        
        n_spike = int(n_anomalies * anomaly_distribution['sudden_spike'])
        print(f"Generating {n_spike} sudden spike anomalies...")
        anomaly_samples.append(self._generate_sudden_spike_anomalies(n_spike))
        
        n_gradual = int(n_anomalies * anomaly_distribution['gradual_attack'])
        print(f"Generating {n_gradual} gradual attack anomalies...")
        anomaly_samples.append(self._generate_gradual_attack_anomalies(n_gradual))
        
        n_adv = int(n_anomalies * anomaly_distribution['adversarial'])
        print(f"Generating {n_adv} adversarial anomalies...")
        anomaly_samples.append(self._generate_adversarial_anomalies(n_adv))
        
        n_combined = n_anomalies - (n_spike + n_gradual + n_adv)
        print(f"Generating {n_combined} combined weak signal anomalies...")
        anomaly_samples.append(self._generate_combined_weak_signals(n_combined))
        
        # Combine all samples
        all_anomalies = np.vstack(anomaly_samples)
        all_samples = np.vstack([normal_samples, all_anomalies])
        
        # Create labels
        labels = np.concatenate([
            np.zeros(n_normal),
            np.ones(n_anomalies)
        ])
        
        # Add noise to simulate realistic measurements
        print(f"Adding {noise_level*100:.1f}% noise...")
        all_samples = self._add_noise(all_samples, noise_level)
        all_samples = self._clip_to_bounds(all_samples)
        
        # Shuffle dataset
        shuffle_idx = np.random.permutation(len(all_samples))
        all_samples = all_samples[shuffle_idx]
        labels = labels[shuffle_idx]
        
        # Create DataFrame
        df = pd.DataFrame(all_samples, columns=self.feature_names)
        
        print(f"\n[OK] Generated {n_samples} samples ({n_normal} normal, {n_anomalies} anomalous)")
        print(f"   Anomaly ratio: {anomaly_ratio*100:.1f}%")
        print(f"   Features: {len(self.feature_names)}")
        
        return df, labels
    
    def generate_test_scenarios(self) -> Dict[str, Tuple[pd.DataFrame, np.ndarray]]:
        """
        Generate specialized test scenarios for model evaluation.
        
        Returns:
            Dictionary with test scenario names as keys and (X, y) tuples as values
        """
        scenarios = {}
        
        # Clean data (low noise)
        print("\n=== Generating Clean Test Data ===")
        X_clean, y_clean = self.generate_dataset(n_samples=500, anomaly_ratio=0.1, noise_level=0.01)
        scenarios['clean'] = (X_clean, y_clean)
        
        # Noisy data (high noise)
        print("\n=== Generating Noisy Test Data ===")
        X_noisy, y_noisy = self.generate_dataset(n_samples=500, anomaly_ratio=0.1, noise_level=0.10)
        scenarios['noisy'] = (X_noisy, y_noisy)
        
        # Pure gradual attacks
        print("\n=== Generating Gradual Attack Test Data ===")
        X_gradual = self._generate_normal_samples(400)
        X_gradual_anom = self._generate_gradual_attack_anomalies(100)
        X_gradual_all = np.vstack([X_gradual, X_gradual_anom])
        y_gradual = np.concatenate([np.zeros(400), np.ones(100)])
        shuffle_idx = np.random.permutation(len(X_gradual_all))
        scenarios['gradual_attacks'] = (
            pd.DataFrame(X_gradual_all[shuffle_idx], columns=self.feature_names),
            y_gradual[shuffle_idx]
        )
        
        # Pure adversarial attacks
        print("\n=== Generating Adversarial Test Data ===")
        X_adv = self._generate_normal_samples(400)
        X_adv_anom = self._generate_adversarial_anomalies(100)
        X_adv_all = np.vstack([X_adv, X_adv_anom])
        y_adv = np.concatenate([np.zeros(400), np.ones(100)])
        shuffle_idx = np.random.permutation(len(X_adv_all))
        scenarios['adversarial'] = (
            pd.DataFrame(X_adv_all[shuffle_idx], columns=self.feature_names),
            y_adv[shuffle_idx]
        )
        
        # Combined weak signals only
        print("\n=== Generating Combined Weak Signals Test Data ===")
        X_weak = self._generate_normal_samples(400)
        X_weak_anom = self._generate_combined_weak_signals(100)
        X_weak_all = np.vstack([X_weak, X_weak_anom])
        y_weak = np.concatenate([np.zeros(400), np.ones(100)])
        shuffle_idx = np.random.permutation(len(X_weak_all))
        scenarios['weak_signals'] = (
            pd.DataFrame(X_weak_all[shuffle_idx], columns=self.feature_names),
            y_weak[shuffle_idx]
        )
        
        print("\n[OK] Generated all test scenarios")
        
        return scenarios


if __name__ == "__main__":
    # Demo usage
    print("="*80)
    print("Enhanced Synthetic Data Generator")
    print("="*80)
    
    generator = SyntheticDataGenerator(random_state=42)
    
    # Generate training data
    print("\n### TRAINING DATA ###")
    X_train, y_train = generator.generate_dataset(
        n_samples=1800,
        anomaly_ratio=0.08,
        noise_level=0.03
    )
    
    print("\nTraining Data Summary:")
    print(X_train.describe())
    print(f"\nClass distribution: {np.bincount(y_train.astype(int))}")
    
    # Generate test scenarios
    print("\n### TEST SCENARIOS ###")
    test_scenarios = generator.generate_test_scenarios()
    
    for scenario_name, (X, y) in test_scenarios.items():
        print(f"\n{scenario_name}: {len(X)} samples, {y.sum()} anomalies ({y.mean()*100:.1f}%)")
