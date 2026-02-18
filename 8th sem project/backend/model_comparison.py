"""
Model Comparison and Evaluation System

Compares CSIC baseline models against robust enhanced models on various test scenarios:
- Clean synthetic data
- Noisy data
- Gradual attacks
- Adversarial attacks
- Unseen anomaly types

Generates comprehensive performance reports with degradation analysis.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)
from typing import Dict, Tuple, List, Any
import joblib
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ModelComparator:
    """
    Compare multiple models across various test scenarios.
    """
    
    def __init__(
        self,
        models_dir: str = 'models',
        output_dir: str = 'evaluation_results'
    ):
        """
        Initialize the comparator.
        
        Args:
            models_dir: Directory containing saved models
            models_dir: Directory to save evaluation results
        """
        self.models_dir = Path(models_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Store loaded models
        self.models = {}
        self.scalers = {}
        self.metadata = {}
    
    def load_csic_baseline(self) -> None:
        """
        Load CSIC baseline models (frozen baseline).
        
        Expected files:
        - csic_random_forest.pkl
        - csic_random_forest_scaler.pkl
        - csic_isolation_forest.pkl
        - csic_isolation_forest_scaler.pkl
        """
        print("\n=== Loading CSIC Baseline Models ===")
        
        # Load Random Forest
        rf_path = self.models_dir / 'csic_random_forest.pkl'
        rf_scaler_path = self.models_dir / 'csic_random_forest_scaler.pkl'
        
        if rf_path.exists() and rf_scaler_path.exists():
            self.models['csic_rf'] = joblib.load(rf_path)
            self.scalers['csic_rf'] = joblib.load(rf_scaler_path)
            print("✅ Loaded CSIC Random Forest")
        else:
            print(f"⚠️  CSIC Random Forest not found at {rf_path}")
            print("   Will attempt to load from standard location...")
            # Try standard location
            std_rf_path = self.models_dir / 'random_forest.pkl'
            std_scaler_path = self.models_dir / 'lr_scaler.pkl'  # or appropriate scaler
            if std_rf_path.exists():
                self.models['csic_rf'] = joblib.load(std_rf_path)
                # Try to find appropriate scaler
                if std_scaler_path.exists():
                    self.scalers['csic_rf'] = joblib.load(std_scaler_path)
                    print("✅ Loaded from standard location")
        
        # Load Isolation Forest
        iso_path = self.models_dir / 'csic_isolation_forest.pkl'
        iso_scaler_path = self.models_dir / 'csic_isolation_forest_scaler.pkl'
        
        if iso_path.exists() and iso_scaler_path.exists():
            self.models['csic_iso'] = joblib.load(iso_path)
            self.scalers['csic_iso'] = joblib.load(iso_scaler_path)
            print("✅ Loaded CSIC Isolation Forest")
        else:
            print(f"⚠️  CSIC Isolation Forest not found at {iso_path}")
            print("   Will attempt to load from standard location...")
            std_iso_path = self.models_dir / 'isolation_forest.pkl'
            std_iso_scaler_path = self.models_dir / 'isolation_scaler.pkl'
            if std_iso_path.exists() and std_iso_scaler_path.exists():
                self.models['csic_iso'] = joblib.load(std_iso_path)
                self.scalers['csic_iso'] = joblib.load(std_iso_scaler_path)
                print("✅ Loaded from standard location")
    
    def load_robust_models(self) -> None:
        """
        Load robust enhanced models.
        
        Expected files:
        - robust_random_forest.pkl
        - robust_random_forest_scaler.pkl
        - robust_isolation_forest.pkl
        - robust_isolation_forest_scaler.pkl
        """
        print("\n=== Loading Robust Enhanced Models ===")
        
        # Load Random Forest
        rf_path = self.models_dir / 'robust_random_forest.pkl'
        rf_scaler_path = self.models_dir / 'robust_random_forest_scaler.pkl'
        
        if rf_path.exists() and rf_scaler_path.exists():
            self.models['robust_rf'] = joblib.load(rf_path)
            self.scalers['robust_rf'] = joblib.load(rf_scaler_path)
            print("✅ Loaded Robust Random Forest")
        else:
            print(f"⚠️  Robust Random Forest not found at {rf_path}")
        
        # Load Isolation Forest
        iso_path = self.models_dir / 'robust_isolation_forest.pkl'
        iso_scaler_path = self.models_dir / 'robust_isolation_forest_scaler.pkl'
        
        if iso_path.exists() and iso_scaler_path.exists():
            self.models['robust_iso'] = joblib.load(iso_path)
            self.scalers['robust_iso'] = joblib.load(iso_scaler_path)
            print("✅ Loaded Robust Isolation Forest")
        else:
            print(f"⚠️  Robust Isolation Forest not found at {iso_path}")
    
    def _predict_with_model(
        self,
        model_key: str,
        X: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Make predictions using a loaded model.
        
        Args:
            model_key: Key in self.models dictionary
            X: Feature matrix
            
        Returns:
            Tuple of (predictions, probabilities)
        """
        if model_key not in self.models:
            raise ValueError(f"Model {model_key} not loaded")
        
        model = self.models[model_key]
        scaler = self.scalers[model_key]
        
        # Scale features
        X_scaled = scaler.transform(X.values if isinstance(X, pd.DataFrame) else X)
        
        # Handle Isolation Forest differently
        if 'iso' in model_key:
            predictions = model.predict(X_scaled)
            # Convert -1 (anomaly) to 1, and 1 (normal) to 0
            predictions = (predictions == -1).astype(int)
            
            # Get anomaly scores
            scores = model.score_samples(X_scaled)
            # Convert to probabilities
            probas = 1 - (scores - scores.min()) / (scores.max() - scores.min() + 1e-10)
        else:
            predictions = model.predict(X_scaled)
            probas = model.predict_proba(X_scaled)[:, 1]
        
        return predictions, probas
    
    def evaluate_model(
        self,
        model_key: str,
        X: pd.DataFrame,
        y: np.ndarray,
        scenario_name: str = ''
    ) -> Dict[str, float]:
        """
        Evaluate a single model on test data.
        
        Args:
            model_key: Key in self.models dictionary
            X: Feature matrix
            y: True labels
            scenario_name: Name of test scenario (for logging)
            
        Returns:
            Dictionary of metrics
        """
        y_pred, y_proba = self._predict_with_model(model_key, X)
        
        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1': f1_score(y, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y, y_proba) if len(np.unique(y)) > 1 else 0.0
        }
        
        # Add confusion matrix
        cm = confusion_matrix(y, y_pred)
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            metrics['true_negative'] = tn
            metrics['false_positive'] = fp
            metrics['false_negative'] = fn
            metrics['true_positive'] = tp
        
        return metrics
    
    def compare_on_scenarios(
        self,
        test_scenarios: Dict[str, Tuple[pd.DataFrame, np.ndarray]]
    ) -> pd.DataFrame:
        """
        Compare all loaded models across multiple test scenarios.
        
        Args:
            test_scenarios: Dictionary mapping scenario names to (X, y) tuples
            
        Returns:
            DataFrame with comparison results
        """
        results = []
        
        print("\n" + "="*80)
        print("COMPARATIVE EVALUATION")
        print("="*80)
        
        for scenario_name, (X_test, y_test) in test_scenarios.items():
            print(f"\n### {scenario_name.upper()} ###")
            print(f"Test samples: {len(X_test)}, Anomalies: {y_test.sum()} ({y_test.mean()*100:.1f}%)")
            
            for model_key in self.models.keys():
                print(f"\nEvaluating {model_key}...")
                
                try:
                    metrics = self.evaluate_model(model_key, X_test, y_test, scenario_name)
                    
                    result_row = {
                        'model': model_key,
                        'scenario': scenario_name,
                        **metrics
                    }
                    results.append(result_row)
                    
                    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
                    print(f"  Precision: {metrics['precision']:.4f}")
                    print(f"  Recall:    {metrics['recall']:.4f}")
                    print(f"  F1 Score:  {metrics['f1']:.4f}")
                    print(f"  ROC AUC:   {metrics['roc_auc']:.4f}")
                    
                except Exception as e:
                    print(f"  ❌ Error: {e}")
        
        results_df = pd.DataFrame(results)
        return results_df
    
    def compute_degradation(
        self,
        results_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute performance degradation from clean to challenging scenarios.
        
        Args:
            results_df: Results DataFrame from compare_on_scenarios
            
        Returns:
            DataFrame with degradation analysis
        """
        degradation = []
        
        baseline_scenario = 'clean'
        
        for model in results_df['model'].unique():
            model_data = results_df[results_df['model'] == model]
            
            # Get baseline performance
            baseline = model_data[model_data['scenario'] == baseline_scenario]
            if len(baseline) == 0:
                continue
            
            baseline_f1 = baseline['f1'].values[0]
            baseline_roc = baseline['roc_auc'].values[0]
            
            # Compare against other scenarios
            for scenario in model_data['scenario'].unique():
                if scenario == baseline_scenario:
                    continue
                
                scenario_data = model_data[model_data['scenario'] == scenario]
                if len(scenario_data) == 0:
                    continue
                
                scenario_f1 = scenario_data['f1'].values[0]
                scenario_roc = scenario_data['roc_auc'].values[0]
                
                degradation.append({
                    'model': model,
                    'scenario': scenario,
                    'f1_degradation': baseline_f1 - scenario_f1,
                    'f1_degradation_pct': ((baseline_f1 - scenario_f1) / (baseline_f1 + 1e-10)) * 100,
                    'roc_degradation': baseline_roc - scenario_roc,
                    'roc_degradation_pct': ((baseline_roc - scenario_roc) / (baseline_roc + 1e-10)) * 100
                })
        
        return pd.DataFrame(degradation)
    
    def plot_comparison(
        self,
        results_df: pd.DataFrame,
        metric: str = 'f1'
    ) -> None:
        """
        Plot model comparison across scenarios.
        
        Args:
            results_df: Results DataFrame
            metric: Metric to plot
        """
        plt.figure(figsize=(12, 6))
        
        # Pivot data for plotting
        pivot_data = results_df.pivot(index='scenario', columns='model', values=metric)
        
        pivot_data.plot(kind='bar', ax=plt.gca(), width=0.8)
        
        plt.title(f'Model Comparison: {metric.upper()} Score Across Scenarios', fontsize=14, fontweight='bold')
        plt.xlabel('Test Scenario', fontsize=12)
        plt.ylabel(f'{metric.upper()} Score', fontsize=12)
        plt.legend(title='Model', fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.ylim([0, 1.0])
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / f'comparison_{metric}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved plot: {output_path}")
        plt.close()
    
    def plot_confusion_matrices(
        self,
        test_scenarios: Dict[str, Tuple[pd.DataFrame, np.ndarray]],
        scenario_name: str = 'clean'
    ) -> None:
        """
        Plot confusion matrices for all models on a specific scenario.
        
        Args:
            test_scenarios: Test scenarios dictionary
            scenario_name: Which scenario to plot
        """
        if scenario_name not in test_scenarios:
            print(f"Scenario {scenario_name} not found")
            return
        
        X_test, y_test = test_scenarios[scenario_name]
        
        n_models = len(self.models)
        fig, axes = plt.subplots(1, n_models, figsize=(5*n_models, 4))
        
        if n_models == 1:
            axes = [axes]
        
        for idx, (model_key, model) in enumerate(self.models.items()):
            y_pred, _ = self._predict_with_model(model_key, X_test)
            cm = confusion_matrix(y_test, y_pred)
            
            sns.heatmap(
                cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Normal', 'Anomaly'],
                yticklabels=['Normal', 'Anomaly'],
                ax=axes[idx],
                cbar=False
            )
            
            axes[idx].set_title(f'{model_key}\n({scenario_name})', fontweight='bold')
            axes[idx].set_ylabel('True Label')
            axes[idx].set_xlabel('Predicted Label')
        
        plt.tight_layout()
        output_path = self.output_dir / f'confusion_matrices_{scenario_name}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved confusion matrices: {output_path}")
        plt.close()
    
    def plot_roc_curves(
        self,
        test_scenarios: Dict[str, Tuple[pd.DataFrame, np.ndarray]],
        scenario_name: str = 'clean'
    ) -> None:
        """
        Plot ROC curves for all models on a specific scenario.
        
        Args:
            test_scenarios: Test scenarios dictionary
            scenario_name: Which scenario to plot
        """
        if scenario_name not in test_scenarios:
            print(f"Scenario {scenario_name} not found")
            return
        
        X_test, y_test = test_scenarios[scenario_name]
        
        plt.figure(figsize=(10, 8))
        
        for model_key in self.models.keys():
            _, y_proba = self._predict_with_model(model_key, X_test)
            
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            auc = roc_auc_score(y_test, y_proba)
            
            plt.plot(fpr, tpr, linewidth=2, label=f'{model_key} (AUC = {auc:.3f})')
        
        # Plot diagonal line
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
        
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title(f'ROC Curves - {scenario_name.upper()}', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / f'roc_curves_{scenario_name}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved ROC curves: {output_path}")
        plt.close()
    
    def generate_report(
        self,
        results_df: pd.DataFrame,
        degradation_df: pd.DataFrame
    ) -> None:
        """
        Generate comprehensive text report.
        
        Args:
            results_df: Results DataFrame
            degradation_df: Degradation DataFrame
        """
        report_path = self.output_dir / 'evaluation_report.txt'
        
        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MODEL COMPARISON EVALUATION REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("="*80 + "\n")
            f.write("COMPREHENSIVE RESULTS\n")
            f.write("="*80 + "\n\n")
            f.write(results_df.to_string(index=False))
            f.write("\n\n")
            
            f.write("="*80 + "\n")
            f.write("PERFORMANCE DEGRADATION ANALYSIS\n")
            f.write("="*80 + "\n\n")
            f.write(degradation_df.to_string(index=False))
            f.write("\n\n")
            
            f.write("="*80 + "\n")
            f.write("SUMMARY STATISTICS\n")
            f.write("="*80 + "\n\n")
            
            for model in results_df['model'].unique():
                model_data = results_df[results_df['model'] == model]
                f.write(f"\n{model}:\n")
                f.write(f"  Average F1 Score:  {model_data['f1'].mean():.4f} ± {model_data['f1'].std():.4f}\n")
                f.write(f"  Average ROC AUC:   {model_data['roc_auc'].mean():.4f} ± {model_data['roc_auc'].std():.4f}\n")
                f.write(f"  Average Precision: {model_data['precision'].mean():.4f} ± {model_data['precision'].std():.4f}\n")
                f.write(f"  Average Recall:    {model_data['recall'].mean():.4f} ± {model_data['recall'].std():.4f}\n")
        
        print(f"\n✅ Generated report: {report_path}")


if __name__ == "__main__":
    # Demo usage
    from synthetic_data_generator import SyntheticDataGenerator
    
    print("="*80)
    print("Model Comparison Demo")
    print("="*80)
    
    # Generate test scenarios
    generator = SyntheticDataGenerator(random_state=42)
    test_scenarios = generator.generate_test_scenarios()
    
    # Initialize comparator
    comparator = ModelComparator()
    
    # Load models
    comparator.load_csic_baseline()
    comparator.load_robust_models()
    
    if len(comparator.models) == 0:
        print("\n❌ No models loaded. Please train models first.")
    else:
        # Compare models
        results = comparator.compare_on_scenarios(test_scenarios)
        
        # Compute degradation
        degradation = comparator.compute_degradation(results)
        
        # Generate visualizations
        comparator.plot_comparison(results, metric='f1')
        comparator.plot_comparison(results, metric='roc_auc')
        comparator.plot_confusion_matrices(test_scenarios, 'clean')
        comparator.plot_roc_curves(test_scenarios, 'clean')
        
        # Generate report
        comparator.generate_report(results, degradation)
