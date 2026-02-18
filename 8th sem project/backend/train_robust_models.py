"""
Main Enhanced Training Pipeline Orchestrator

Complete workflow:
1. Preserve CSIC baseline models
2. Generate enhanced synthetic data
3. Train robust models with k-fold CV
4. Evaluate and compare models
5. Generate comprehensive reports

Usage:
    python train_robust_models.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
import joblib
import shutil
from datetime import datetime
from typing import Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')

from synthetic_data_generator import SyntheticDataGenerator
from robust_training_pipeline import RobustTrainingPipeline
from model_comparison import ModelComparator


class EnhancedTrainingOrchestrator:
    """
    Orchestrates the complete enhanced training pipeline.
    """
    
    def __init__(
        self,
        models_dir: str = 'models',
        datasets_dir: str = 'datasets/processed',
        output_dir: str = 'evaluation_results',
        random_state: int = 42
    ):
        """
        Initialize the orchestrator.
        
        Args:
            models_dir: Directory for model storage
            datasets_dir: Directory with CSIC datasets
            output_dir: Directory for evaluation results
            random_state: Random seed
        """
        self.models_dir = Path(models_dir)
        self.datasets_dir = Path(datasets_dir)
        self.output_dir = Path(output_dir)
        self.random_state = random_state
        
        # Create directories
        self.models_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        print("="*80)
        print("ENHANCED TRAINING PIPELINE")
        print("="*80)
        print(f"Models directory:   {self.models_dir}")
        print(f"Datasets directory: {self.datasets_dir}")
        print(f"Output directory:   {self.output_dir}")
        print(f"Random state:       {self.random_state}")
        print("="*80)
    
    def preserve_csic_baseline(self) -> None:
        """
        Preserve existing CSIC models as baseline (rename if needed).
        
        Renames:
        - random_forest.pkl → csic_random_forest.pkl
        - isolation_forest.pkl → csic_isolation_forest.pkl
        - *_scaler.pkl → csic_*_scaler.pkl
        """
        print("\n" + "="*80)
        print("STEP 1: PRESERVE CSIC BASELINE MODELS")
        print("="*80)
        
        # Check if CSIC baselines already exist
        csic_rf_path = self.models_dir / 'csic_random_forest.pkl'
        csic_iso_path = self.models_dir / 'csic_isolation_forest.pkl'
        
        if csic_rf_path.exists() and csic_iso_path.exists():
            print("✅ CSIC baseline models already preserved:")
            print(f"   {csic_rf_path}")
            print(f"   {csic_iso_path}")
            return
        
        # Look for original models
        orig_rf_path = self.models_dir / 'random_forest.pkl'
        orig_iso_path = self.models_dir / 'isolation_forest.pkl'
        orig_iso_scaler_path = self.models_dir / 'isolation_scaler.pkl'
        
        if orig_rf_path.exists():
            # Copy (not move) to preserve original
            if not csic_rf_path.exists():
                shutil.copy2(orig_rf_path, csic_rf_path)
                print(f"✅ Preserved Random Forest: {orig_rf_path} → {csic_rf_path}")
            
            # Also preserve scaler if it exists
            # Try to find appropriate scaler
            for scaler_name in ['lr_scaler.pkl', 'random_forest_scaler.pkl', 'rf_scaler.pkl']:
                scaler_path = self.models_dir / scaler_name
                if scaler_path.exists():
                    csic_scaler_path = self.models_dir / 'csic_random_forest_scaler.pkl'
                    if not csic_scaler_path.exists():
                        shutil.copy2(scaler_path, csic_scaler_path)
                        print(f"✅ Preserved RF Scaler: {scaler_path} → {csic_scaler_path}")
                    break
        else:
            print(f"⚠️  Random Forest model not found at {orig_rf_path}")
            print("   Will train new baseline from CSIC data")
        
        if orig_iso_path.exists():
            if not csic_iso_path.exists():
                shutil.copy2(orig_iso_path, csic_iso_path)
                print(f"✅ Preserved Isolation Forest: {orig_iso_path} → {csic_iso_path}")
            
            if orig_iso_scaler_path.exists():
                csic_iso_scaler_path = self.models_dir / 'csic_isolation_forest_scaler.pkl'
                if not csic_iso_scaler_path.exists():
                    shutil.copy2(orig_iso_scaler_path, csic_iso_scaler_path)
                    print(f"✅ Preserved ISO Scaler: {orig_iso_scaler_path} → {csic_iso_scaler_path}")
        else:
            print(f"⚠️  Isolation Forest model not found at {orig_iso_path}")
            print("   Will train new baseline from CSIC data")
    
    def load_or_train_csic_baseline(self) -> None:
        """
        Load existing CSIC baseline or train from CSIC dataset.
        """
        csic_rf_path = self.models_dir / 'csic_random_forest.pkl'
        csic_iso_path = self.models_dir / 'csic_isolation_forest.pkl'
        
        # If models already exist, skip training
        if csic_rf_path.exists() and csic_iso_path.exists():
            print("\n✅ CSIC baseline models already exist. Skipping training.")
            return
        
        print("\n⚠️  Training CSIC baseline models from dataset...")
        
        # Load CSIC dataset
        csic_data_path = self.datasets_dir / 'combined_training_data.csv'
        
        if not csic_data_path.exists():
            print(f"❌ CSIC dataset not found at {csic_data_path}")
            print("   Cannot train baseline. Please ensure CSIC dataset is processed.")
            return
        
        df = pd.read_csv(csic_data_path)
        print(f"✅ Loaded CSIC dataset: {len(df)} samples")
        
        # Extract features and labels
        feature_cols = [col for col in df.columns if col != 'is_anomalous']
        X = df[feature_cols]
        y = df['is_anomalous'].values
        
        # Train simple baseline models (no CV, just fit)
        from sklearn.ensemble import RandomForestClassifier, IsolationForest
        from sklearn.preprocessing import StandardScaler
        
        # Train Random Forest
        print("\nTraining CSIC Random Forest baseline...")
        rf_scaler = StandardScaler()
        X_scaled = rf_scaler.fit_transform(X)
        
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=self.random_state,
            n_jobs=-1
        )
        rf.fit(X_scaled, y)
        
        joblib.dump(rf, csic_rf_path)
        joblib.dump(rf_scaler, self.models_dir / 'csic_random_forest_scaler.pkl')
        print(f"✅ Saved CSIC Random Forest baseline")
        
        # Train Isolation Forest
        print("\nTraining CSIC Isolation Forest baseline...")
        iso_scaler = StandardScaler()
        X_scaled_iso = iso_scaler.fit_transform(X)
        
        contamination = y.mean()
        iso = IsolationForest(
            n_estimators=100,
            contamination=contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        iso.fit(X_scaled_iso)
        
        joblib.dump(iso, csic_iso_path)
        joblib.dump(iso_scaler, self.models_dir / 'csic_isolation_forest_scaler.pkl')
        print(f"✅ Saved CSIC Isolation Forest baseline")
    
    def generate_enhanced_data(
        self,
        n_samples: int = 1800,
        anomaly_ratio: float = 0.08
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Generate enhanced synthetic training data.
        
        Args:
            n_samples: Total samples to generate
            anomaly_ratio: Fraction of anomalous samples
            
        Returns:
            Tuple of (X, y)
        """
        print("\n" + "="*80)
        print("STEP 2: GENERATE ENHANCED SYNTHETIC DATA")
        print("="*80)
        
        generator = SyntheticDataGenerator(random_state=self.random_state)
        X, y = generator.generate_dataset(
            n_samples=n_samples,
            anomaly_ratio=anomaly_ratio,
            noise_level=0.03
        )
        
        # Save generated data
        output_path = self.datasets_dir / 'synthetic_robust_training.csv'
        df = X.copy()
        df['is_anomalous'] = y
        df.to_csv(output_path, index=False)
        print(f"\n✅ Saved synthetic training data: {output_path}")
        
        return X, y
    
    def train_robust_models(
        self,
        X: pd.DataFrame,
        y: np.ndarray
    ) -> None:
        """
        Train robust models with k-fold cross-validation.
        
        Args:
            X: Feature matrix
            y: Labels
        """
        print("\n" + "="*80)
        print("STEP 3: TRAIN ROBUST MODELS WITH K-FOLD CV")
        print("="*80)
        
        pipeline = RobustTrainingPipeline(
            n_folds=5,
            random_state=self.random_state,
            models_dir=str(self.models_dir)
        )
        
        # Train Random Forest
        rf_model, rf_scaler, rf_cv = pipeline.train_random_forest_cv(X, y)
        pipeline.save_model(
            rf_model, rf_scaler, rf_cv,
            model_name='robust_random_forest',
            metadata={
                'training_samples': len(X),
                'anomaly_ratio': y.mean(),
                'training_date': datetime.now().isoformat()
            }
        )
        
        # Train Isolation Forest
        iso_model, iso_scaler, iso_cv = pipeline.train_isolation_forest_cv(X, y)
        pipeline.save_model(
            iso_model, iso_scaler, iso_cv,
            model_name='robust_isolation_forest',
            metadata={
                'training_samples': len(X),
                'anomaly_ratio': y.mean(),
                'training_date': datetime.now().isoformat()
            }
        )
        
        print("\n✅ Robust models trained and saved!")
    
    def evaluate_and_compare(self) -> None:
        """
        Evaluate and compare CSIC baseline vs robust models.
        """
        print("\n" + "="*80)
        print("STEP 4: EVALUATE AND COMPARE MODELS")
        print("="*80)
        
        # Generate test scenarios
        print("\nGenerating test scenarios...")
        generator = SyntheticDataGenerator(random_state=self.random_state + 1)
        test_scenarios = generator.generate_test_scenarios()
        
        # Initialize comparator
        comparator = ModelComparator(
            models_dir=str(self.models_dir),
            output_dir=str(self.output_dir)
        )
        
        # Load models
        comparator.load_csic_baseline()
        comparator.load_robust_models()
        
        if len(comparator.models) == 0:
            print("\n❌ No models loaded for comparison")
            return
        
        # Compare models
        results = comparator.compare_on_scenarios(test_scenarios)
        
        # Save results
        results_path = self.output_dir / 'comparison_results.csv'
        results.to_csv(results_path, index=False)
        print(f"\n✅ Saved comparison results: {results_path}")
        
        # Compute degradation
        degradation = comparator.compute_degradation(results)
        degradation_path = self.output_dir / 'degradation_analysis.csv'
        degradation.to_csv(degradation_path, index=False)
        print(f"✅ Saved degradation analysis: {degradation_path}")
        
        return comparator, results, degradation, test_scenarios
    
    def generate_visualizations(
        self,
        comparator: ModelComparator,
        results: pd.DataFrame,
        degradation: pd.DataFrame,
        test_scenarios: dict
    ) -> None:
        """
        Generate all visualizations.
        
        Args:
            comparator: ModelComparator instance
            results: Comparison results
            degradation: Degradation analysis
            test_scenarios: Test scenarios dictionary
        """
        print("\n" + "="*80)
        print("STEP 5: GENERATE VISUALIZATIONS")
        print("="*80)
        
        # Plot comparisons
        print("\nGenerating comparison plots...")
        comparator.plot_comparison(results, metric='f1')
        comparator.plot_comparison(results, metric='roc_auc')
        comparator.plot_comparison(results, metric='precision')
        comparator.plot_comparison(results, metric='recall')
        
        # Plot confusion matrices for key scenarios
        print("\nGenerating confusion matrices...")
        for scenario in ['clean', 'noisy', 'adversarial']:
            if scenario in test_scenarios:
                comparator.plot_confusion_matrices(test_scenarios, scenario)
        
        # Plot ROC curves
        print("\nGenerating ROC curves...")
        for scenario in ['clean', 'adversarial', 'gradual_attacks']:
            if scenario in test_scenarios:
                comparator.plot_roc_curves(test_scenarios, scenario)
        
        # Generate comprehensive report
        print("\nGenerating comprehensive report...")
        comparator.generate_report(results, degradation)
        
        print("\n✅ All visualizations generated!")
    
    def run_complete_pipeline(
        self,
        n_samples: int = 1800,
        anomaly_ratio: float = 0.08
    ) -> None:
        """
        Run the complete enhanced training pipeline.
        
        Args:
            n_samples: Number of training samples to generate
            anomaly_ratio: Anomaly ratio in training data
        """
        start_time = datetime.now()
        
        print("\n" + "="*80)
        print("STARTING COMPLETE ENHANCED TRAINING PIPELINE")
        print("="*80)
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Preserve CSIC baseline
        self.preserve_csic_baseline()
        self.load_or_train_csic_baseline()
        
        # Step 2: Generate enhanced synthetic data
        X_train, y_train = self.generate_enhanced_data(n_samples, anomaly_ratio)
        
        # Step 3: Train robust models
        self.train_robust_models(X_train, y_train)
        
        # Step 4: Evaluate and compare
        comparator, results, degradation, test_scenarios = self.evaluate_and_compare()
        
        # Step 5: Generate visualizations
        self.generate_visualizations(comparator, results, degradation, test_scenarios)
        
        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "="*80)
        print("PIPELINE COMPLETE!")
        print("="*80)
        print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"\nModels saved in:     {self.models_dir}")
        print(f"Results saved in:    {self.output_dir}")
        print("="*80)
        
        # Print key findings
        print("\n" + "="*80)
        print("KEY FINDINGS")
        print("="*80)
        
        # Average performance by model type
        for model in results['model'].unique():
            model_data = results[results['model'] == model]
            print(f"\n{model.upper()}:")
            print(f"  Average F1 Score:  {model_data['f1'].mean():.4f} ± {model_data['f1'].std():.4f}")
            print(f"  Average ROC AUC:   {model_data['roc_auc'].mean():.4f} ± {model_data['roc_auc'].std():.4f}")
        
        print("\n" + "="*80)


def main():
    """
    Main entry point for the enhanced training pipeline.
    """
    orchestrator = EnhancedTrainingOrchestrator(
        models_dir='models',
        datasets_dir='datasets/processed',
        output_dir='evaluation_results',
        random_state=42
    )
    
    orchestrator.run_complete_pipeline(
        n_samples=1800,  # Generate 1800 samples
        anomaly_ratio=0.08  # 8% anomaly ratio
    )


if __name__ == "__main__":
    main()
