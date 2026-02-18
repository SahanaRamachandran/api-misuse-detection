"""
SHAP-based Model Explainability Module

Provides interpretable explanations for Random Forest anomaly predictions:
- Global feature importance across all predictions
- Per-sample SHAP values for individual anomalies
- Top-5 contributing features for each flagged request
- Visualization outputs saved to evaluation_results/explainability/

Uses TreeExplainer for efficient Random Forest explanation.
No model modification - read-only analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import shap
from pathlib import Path
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class SHAPExplainer:
    """
    SHAP-based explainability for Random Forest anomaly detection models.
    """
    
    def __init__(
        self,
        models_dir: str = 'models',
        output_dir: str = 'evaluation_results/explainability',
        feature_names: List[str] = None
    ):
        """
        Initialize SHAP explainer.
        
        Args:
            models_dir: Directory containing saved models
            output_dir: Directory for saving explanation outputs
            feature_names: List of feature names (in order)
        """
        self.models_dir = Path(models_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default feature names matching CSIC dataset
        self.feature_names = feature_names or [
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
        
        self.models = {}
        self.scalers = {}
        self.explainers = {}
    
    def load_model(self, model_name: str) -> None:
        """
        Load a Random Forest model and its scaler.
        
        Args:
            model_name: Name prefix (e.g., 'csic_random_forest' or 'robust_random_forest')
        """
        model_path = self.models_dir / f'{model_name}.pkl'
        scaler_path = self.models_dir / f'{model_name}_scaler.pkl'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        if not scaler_path.exists():
            raise FileNotFoundError(f"Scaler not found: {scaler_path}")
        
        self.models[model_name] = joblib.load(model_path)
        self.scalers[model_name] = joblib.load(scaler_path)
        
        print(f"[OK] Loaded model: {model_name}")
    
    def create_explainer(
        self,
        model_name: str,
        background_data: pd.DataFrame = None,
        n_background: int = 100
    ) -> None:
        """
        Create SHAP TreeExplainer for a loaded model.
        
        Args:
            model_name: Name of loaded model
            background_data: Background dataset for SHAP (optional)
            n_background: Number of background samples to use
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
        
        model = self.models[model_name]
        
        # Use background data if provided, otherwise use a small subset
        if background_data is not None:
            scaler = self.scalers[model_name]
            X_background = scaler.transform(background_data.values)[:n_background]
        else:
            # Create small synthetic background (for initialization)
            X_background = np.random.randn(n_background, len(self.feature_names))
        
        # Create TreeExplainer (efficient for tree-based models)
        self.explainers[model_name] = shap.TreeExplainer(model, X_background)
        
        print(f"[OK] Created SHAP explainer for {model_name}")
    
    def explain_global(
        self,
        model_name: str,
        X: pd.DataFrame,
        max_display: int = 10
    ) -> np.ndarray:
        """
        Generate global feature importance using SHAP.
        
        Args:
            model_name: Name of model to explain
            X: Feature matrix
            max_display: Number of top features to display
            
        Returns:
            SHAP values array
        """
        if model_name not in self.explainers:
            raise ValueError(f"Explainer for {model_name} not created")
        
        scaler = self.scalers[model_name]
        explainer = self.explainers[model_name]
        
        # Scale features
        X_scaled = scaler.transform(X.values if isinstance(X, pd.DataFrame) else X)
        
        # Compute SHAP values
        shap_values = explainer.shap_values(X_scaled)
        
        # For binary classification, take positive class
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Anomaly class
        
        # Create summary plot (global importance)
        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            shap_values,
            X_scaled,
            feature_names=self.feature_names,
            max_display=max_display,
            show=False
        )
        
        output_path = self.output_dir / f'{model_name}_global_importance.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[OK] Saved global importance: {output_path}")
        
        return shap_values
    
    def explain_sample(
        self,
        model_name: str,
        X_sample: pd.DataFrame,
        sample_idx: int = 0,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Explain a single prediction with SHAP.
        
        Args:
            model_name: Name of model
            X_sample: Single sample or DataFrame with samples
            sample_idx: Index of sample to explain
            top_k: Number of top contributing features
            
        Returns:
            Dictionary with explanation details
        """
        if model_name not in self.explainers:
            raise ValueError(f"Explainer for {model_name} not created")
        
        scaler = self.scalers[model_name]
        model = self.models[model_name]
        explainer = self.explainers[model_name]
        
        # Get single sample
        if isinstance(X_sample, pd.DataFrame):
            if sample_idx >= len(X_sample):
                raise IndexError(f"Sample index {sample_idx} out of range")
            X_single = X_sample.iloc[[sample_idx]]
        else:
            X_single = pd.DataFrame([X_sample], columns=self.feature_names)
        
        # Scale and predict
        X_scaled = scaler.transform(X_single)
        prediction = model.predict(X_scaled)[0]
        probability = model.predict_proba(X_scaled)[0, 1]
        
        # Compute SHAP values
        shap_values = explainer.shap_values(X_scaled)
        
        if isinstance(shap_values, list):
            shap_values_single = shap_values[1][0]  # Anomaly class
        else:
            shap_values_single = shap_values[0]
        
        # Get top K contributing features
        abs_shap = np.abs(shap_values_single)
        top_indices = np.argsort(abs_shap)[-top_k:][::-1]
        
        top_features = []
        for idx in top_indices:
            top_features.append({
                'feature': self.feature_names[idx],
                'value': float(X_single.iloc[0, idx]),
                'shap_value': float(shap_values_single[idx]),
                'contribution': 'positive' if shap_values_single[idx] > 0 else 'negative'
            })
        
        explanation = {
            'model': model_name,
            'prediction': int(prediction),
            'probability': float(probability),
            'top_features': top_features,
            'all_shap_values': {
                self.feature_names[i]: float(shap_values_single[i])
                for i in range(len(self.feature_names))
            }
        }
        
        return explanation
    
    def create_waterfall_plot(
        self,
        model_name: str,
        X_sample: pd.DataFrame,
        sample_idx: int = 0
    ) -> None:
        """
        Create SHAP waterfall plot for a single prediction.
        
        Args:
            model_name: Name of model
            X_sample: Sample dataset
            sample_idx: Index of sample to visualize
        """
        if model_name not in self.explainers:
            raise ValueError(f"Explainer for {model_name} not created")
        
        scaler = self.scalers[model_name]
        explainer = self.explainers[model_name]
        
        # Get single sample
        X_single = X_sample.iloc[[sample_idx]] if isinstance(X_sample, pd.DataFrame) else X_sample
        X_scaled = scaler.transform(X_single)
        
        # Compute SHAP values
        shap_values = explainer.shap_values(X_scaled)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Anomaly class
        
        # Create waterfall plot
        plt.figure(figsize=(10, 6))
        shap.waterfall_plot(
            shap.Explanation(
                values=shap_values[0],
                base_values=explainer.expected_value if not isinstance(explainer.expected_value, list) else explainer.expected_value[1],
                data=X_scaled[0],
                feature_names=self.feature_names
            ),
            show=False
        )
        
        output_path = self.output_dir / f'{model_name}_waterfall_sample_{sample_idx}.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[OK] Saved waterfall plot: {output_path}")
    
    def batch_explain_anomalies(
        self,
        model_name: str,
        X: pd.DataFrame,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Explain all anomalous predictions in a batch.
        
        Args:
            model_name: Name of model
            X: Feature matrix
            top_k: Number of top features per sample
            
        Returns:
            List of explanations for anomalies
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not loaded")
        
        scaler = self.scalers[model_name]
        model = self.models[model_name]
        
        # Scale and predict
        X_scaled = scaler.transform(X.values if isinstance(X, pd.DataFrame) else X)
        predictions = model.predict(X_scaled)
        
        # Find anomalies (prediction = 1)
        anomaly_indices = np.where(predictions == 1)[0]
        
        print(f"[INFO] Found {len(anomaly_indices)} anomalies to explain")
        
        explanations = []
        for idx in anomaly_indices:
            explanation = self.explain_sample(model_name, X, sample_idx=idx, top_k=top_k)
            explanation['sample_index'] = int(idx)
            explanations.append(explanation)
        
        return explanations
    
    def compare_models(
        self,
        model_names: List[str],
        X: pd.DataFrame
    ) -> None:
        """
        Compare feature importance across multiple models.
        
        Args:
            model_names: List of model names to compare
            X: Feature matrix
        """
        importance_data = []
        
        for model_name in model_names:
            if model_name not in self.explainers:
                print(f"[WARN] Skipping {model_name} - explainer not created")
                continue
            
            scaler = self.scalers[model_name]
            explainer = self.explainers[model_name]
            
            X_scaled = scaler.transform(X.values if isinstance(X, pd.DataFrame) else X)
            shap_values = explainer.shap_values(X_scaled)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            
            # Mean absolute SHAP values
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            
            for i, feature in enumerate(self.feature_names):
                importance_data.append({
                    'model': model_name,
                    'feature': feature,
                    'importance': mean_abs_shap[i]
                })
        
        df_importance = pd.DataFrame(importance_data)
        
        # Create comparison plot
        plt.figure(figsize=(12, 6))
        pivot_data = df_importance.pivot(index='feature', columns='model', values='importance')
        pivot_data.plot(kind='bar', ax=plt.gca())
        
        plt.title('Feature Importance Comparison', fontsize=14, fontweight='bold')
        plt.xlabel('Feature', fontsize=12)
        plt.ylabel('Mean |SHAP Value|', fontsize=12)
        plt.legend(title='Model', fontsize=10)
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        
        output_path = self.output_dir / 'model_comparison_importance.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[OK] Saved comparison plot: {output_path}")


def demo_explainability():
    """
    Demo: Generate SHAP explanations for CSIC and robust models.
    """
    print("="*80)
    print("SHAP EXPLAINABILITY DEMO")
    print("="*80)
    
    # Initialize explainer
    explainer = SHAPExplainer()
    
    # Load models
    try:
        explainer.load_model('csic_random_forest')
        explainer.load_model('robust_random_forest')
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("Please train models first using train_robust_models.py")
        return
    
    # Generate synthetic test data
    from synthetic_data_generator import SyntheticDataGenerator
    
    generator = SyntheticDataGenerator(random_state=42)
    X_test, y_test = generator.generate_dataset(n_samples=500, anomaly_ratio=0.1)
    
    # Create explainers
    explainer.create_explainer('csic_random_forest', X_test, n_background=100)
    explainer.create_explainer('robust_random_forest', X_test, n_background=100)
    
    # Global feature importance
    print("\n=== Global Feature Importance ===")
    explainer.explain_global('csic_random_forest', X_test, max_display=9)
    explainer.explain_global('robust_random_forest', X_test, max_display=9)
    
    # Compare models
    print("\n=== Model Comparison ===")
    explainer.compare_models(['csic_random_forest', 'robust_random_forest'], X_test)
    
    # Explain anomalies
    print("\n=== Per-Sample Explanations ===")
    explanations_csic = explainer.batch_explain_anomalies('csic_random_forest', X_test, top_k=5)
    explanations_robust = explainer.batch_explain_anomalies('robust_random_forest', X_test, top_k=5)
    
    # Show first few explanations
    if len(explanations_robust) > 0:
        print("\nExample explanation (Robust Model):")
        print(f"Sample {explanations_robust[0]['sample_index']}:")
        print(f"  Prediction: {explanations_robust[0]['prediction']}")
        print(f"  Probability: {explanations_robust[0]['probability']:.4f}")
        print("\n  Top 5 Contributing Features:")
        for feat in explanations_robust[0]['top_features']:
            print(f"    {feat['feature']:25s}: {feat['shap_value']:+.4f} ({feat['contribution']})")
    
    # Create waterfall plots for first 3 anomalies
    if len(explanations_robust) >= 3:
        print("\n=== Waterfall Plots (First 3 Anomalies) ===")
        for i in range(min(3, len(explanations_robust))):
            idx = explanations_robust[i]['sample_index']
            explainer.create_waterfall_plot('robust_random_forest', X_test, sample_idx=idx)
    
    print("\n" + "="*80)
    print("EXPLAINABILITY ANALYSIS COMPLETE")
    print("="*80)
    print(f"Output directory: {explainer.output_dir}")


if __name__ == "__main__":
    demo_explainability()
