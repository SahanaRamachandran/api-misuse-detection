"""
Robust Training Pipeline with Cross-Validation

Implements proper machine learning training pipeline with:
- Stratified K-Fold cross-validation (k=5)
- Proper scaling inside each fold (no data leakage)
- Mean ± std metrics reporting
- Model persistence with metadata
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from typing import Dict, List, Tuple, Any
import joblib
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


class RobustTrainingPipeline:
    """
    Robust ML training pipeline with proper cross-validation and evaluation.
    """
    
    def __init__(
        self,
        n_folds: int = 5,
        random_state: int = 42,
        models_dir: str = 'models'
    ):
        """
        Initialize the training pipeline.
        
        Args:
            n_folds: Number of folds for cross-validation
            random_state: Random seed for reproducibility
            models_dir: Directory to save models
        """
        self.n_folds = n_folds
        self.random_state = random_state
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Store fold results
        self.fold_metrics = {
            'random_forest': [],
            'isolation_forest': []
        }
    
    def _get_isolation_forest_labels(
        self,
        model: IsolationForest,
        X: np.ndarray
    ) -> np.ndarray:
        """
        Convert Isolation Forest predictions to binary labels.
        
        Args:
            model: Trained Isolation Forest model
            X: Feature matrix
            
        Returns:
            Binary labels (0=normal, 1=anomaly)
        """
        predictions = model.predict(X)
        # Isolation Forest returns -1 for anomalies, 1 for normal
        # Convert to 0=normal, 1=anomaly
        return (predictions == -1).astype(int)
    
    def _compute_metrics(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray = None
    ) -> Dict[str, float]:
        """
        Compute comprehensive evaluation metrics.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            y_proba: Predicted probabilities (for ROC AUC)
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0)
        }
        
        # Add ROC AUC if probabilities provided
        if y_proba is not None:
            try:
                metrics['roc_auc'] = roc_auc_score(y_true, y_proba)
            except:
                metrics['roc_auc'] = 0.0
        
        return metrics
    
    def train_random_forest_cv(
        self,
        X: pd.DataFrame,
        y: np.ndarray
    ) -> Tuple[RandomForestClassifier, StandardScaler, Dict[str, Any]]:
        """
        Train Random Forest with stratified k-fold cross-validation.
        
        Prevents data leakage by:
        - Scaling data inside each fold
        - Using stratified splits
        - Reporting mean ± std metrics
        
        Args:
            X: Feature matrix (DataFrame)
            y: Binary labels
            
        Returns:
            Tuple of (final_model, final_scaler, cv_results)
        """
        print(f"\n{'='*80}")
        print("Training Random Forest with {}-Fold Cross-Validation".format(self.n_folds))
        print(f"{'='*80}")
        
        X_np = X.values
        skf = StratifiedKFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        
        fold_results = []
        
        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_np, y), 1):
            print(f"\n--- Fold {fold_idx}/{self.n_folds} ---")
            
            # Split data
            X_train_fold, X_val_fold = X_np[train_idx], X_np[val_idx]
            y_train_fold, y_val_fold = y[train_idx], y[val_idx]
            
            # Scale data INSIDE fold (prevent leakage)
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train_fold)
            X_val_scaled = scaler.transform(X_val_fold)
            
            # Train model
            rf = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=5,
                class_weight='balanced',
                random_state=self.random_state,
                n_jobs=-1
            )
            
            rf.fit(X_train_scaled, y_train_fold)
            
            # Evaluate on validation fold
            y_pred = rf.predict(X_val_scaled)
            y_proba = rf.predict_proba(X_val_scaled)[:, 1]
            
            metrics = self._compute_metrics(y_val_fold, y_pred, y_proba)
            fold_results.append(metrics)
            
            print(f"  Accuracy:  {metrics['accuracy']:.4f}")
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall:    {metrics['recall']:.4f}")
            print(f"  F1 Score:  {metrics['f1']:.4f}")
            print(f"  ROC AUC:   {metrics['roc_auc']:.4f}")
        
        # Compute mean ± std across folds
        cv_results = {}
        for metric_name in fold_results[0].keys():
            values = [fold[metric_name] for fold in fold_results]
            cv_results[metric_name] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'values': values
            }
        
        print(f"\n{'='*80}")
        print("Cross-Validation Results (Mean ± Std)")
        print(f"{'='*80}")
        for metric_name, stats in cv_results.items():
            print(f"{metric_name.upper():12s}: {stats['mean']:.4f} ± {stats['std']:.4f}")
        
        # Train final model on full dataset
        print(f"\n{'='*80}")
        print("Training final Random Forest model on full dataset...")
        print(f"{'='*80}")
        
        final_scaler = StandardScaler()
        X_scaled = final_scaler.fit_transform(X_np)
        
        final_rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=self.random_state,
            n_jobs=-1
        )
        
        final_rf.fit(X_scaled, y)
        
        # Store fold metrics
        self.fold_metrics['random_forest'] = fold_results
        
        return final_rf, final_scaler, cv_results
    
    def train_isolation_forest_cv(
        self,
        X: pd.DataFrame,
        y: np.ndarray
    ) -> Tuple[IsolationForest, StandardScaler, Dict[str, Any]]:
        """
        Train Isolation Forest with stratified k-fold cross-validation.
        
        Note: Isolation Forest is unsupervised, but we still evaluate
        using labeled data for comparison purposes.
        
        Args:
            X: Feature matrix (DataFrame)
            y: Binary labels (for evaluation only)
            
        Returns:
            Tuple of (final_model, final_scaler, cv_results)
        """
        print(f"\n{'='*80}")
        print("Training Isolation Forest with {}-Fold Cross-Validation".format(self.n_folds))
        print(f"{'='*80}")
        
        X_np = X.values
        skf = StratifiedKFold(n_splits=self.n_folds, shuffle=True, random_state=self.random_state)
        
        fold_results = []
        
        # Calculate contamination from actual data
        contamination = y.mean()
        print(f"Using contamination={contamination:.4f} (actual anomaly rate)\n")
        
        for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_np, y), 1):
            print(f"--- Fold {fold_idx}/{self.n_folds} ---")
            
            # Split data
            X_train_fold, X_val_fold = X_np[train_idx], X_np[val_idx]
            y_train_fold, y_val_fold = y[train_idx], y[val_idx]
            
            # Scale data INSIDE fold
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train_fold)
            X_val_scaled = scaler.transform(X_val_fold)
            
            # Train Isolation Forest
            iso_forest = IsolationForest(
                n_estimators=200,
                contamination=contamination,
                random_state=self.random_state,
                n_jobs=-1
            )
            
            iso_forest.fit(X_train_scaled)
            
            # Evaluate on validation fold
            y_pred = self._get_isolation_forest_labels(iso_forest, X_val_scaled)
            
            # Get anomaly scores for ROC AUC
            scores = iso_forest.score_samples(X_val_scaled)
            # Convert to probabilities (higher score = more anomalous)
            y_proba = 1 - (scores - scores.min()) / (scores.max() - scores.min())
            
            metrics = self._compute_metrics(y_val_fold, y_pred, y_proba)
            fold_results.append(metrics)
            
            print(f"  Accuracy:  {metrics['accuracy']:.4f}")
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall:    {metrics['recall']:.4f}")
            print(f"  F1 Score:  {metrics['f1']:.4f}")
            print(f"  ROC AUC:   {metrics['roc_auc']:.4f}")
        
        # Compute mean ± std across folds
        cv_results = {}
        for metric_name in fold_results[0].keys():
            values = [fold[metric_name] for fold in fold_results]
            cv_results[metric_name] = {
                'mean': np.mean(values),
                'std': np.std(values),
                'values': values
            }
        
        print(f"\n{'='*80}")
        print("Cross-Validation Results (Mean ± Std)")
        print(f"{'='*80}")
        for metric_name, stats in cv_results.items():
            print(f"{metric_name.upper():12s}: {stats['mean']:.4f} ± {stats['std']:.4f}")
        
        # Train final model on full dataset
        print(f"\n{'='*80}")
        print("Training final Isolation Forest model on full dataset...")
        print(f"{'='*80}")
        
        final_scaler = StandardScaler()
        X_scaled = final_scaler.fit_transform(X_np)
        
        final_iso = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=self.random_state,
            n_jobs=-1
        )
        
        final_iso.fit(X_scaled)
        
        # Store fold metrics
        self.fold_metrics['isolation_forest'] = fold_results
        
        return final_iso, final_scaler, cv_results
    
    def save_model(
        self,
        model: Any,
        scaler: StandardScaler,
        cv_results: Dict[str, Any],
        model_name: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Save trained model with scaler and metadata.
        
        Args:
            model: Trained model
            scaler: Fitted scaler
            cv_results: Cross-validation results
            model_name: Name prefix for saved files
            metadata: Additional metadata to save
        """
        model_path = self.models_dir / f"{model_name}.pkl"
        scaler_path = self.models_dir / f"{model_name}_scaler.pkl"
        metadata_path = self.models_dir / f"{model_name}_metadata.pkl"
        
        # Save model and scaler
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Prepare metadata
        full_metadata = {
            'cv_results': cv_results,
            'n_folds': self.n_folds,
            'random_state': self.random_state,
            'model_type': type(model).__name__
        }
        
        if metadata:
            full_metadata.update(metadata)
        
        joblib.dump(full_metadata, metadata_path)
        
        print(f"\n✅ Saved {model_name}:")
        print(f"   Model:    {model_path}")
        print(f"   Scaler:   {scaler_path}")
        print(f"   Metadata: {metadata_path}")
    
    def load_model(
        self,
        model_name: str
    ) -> Tuple[Any, StandardScaler, Dict[str, Any]]:
        """
        Load saved model with scaler and metadata.
        
        Args:
            model_name: Name prefix of saved files
            
        Returns:
            Tuple of (model, scaler, metadata)
        """
        model_path = self.models_dir / f"{model_name}.pkl"
        scaler_path = self.models_dir / f"{model_name}_scaler.pkl"
        metadata_path = self.models_dir / f"{model_name}_metadata.pkl"
        
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        metadata = joblib.load(metadata_path)
        
        return model, scaler, metadata


if __name__ == "__main__":
    # Demo usage
    from synthetic_data_generator import SyntheticDataGenerator
    
    print("="*80)
    print("Robust Training Pipeline Demo")
    print("="*80)
    
    # Generate synthetic data
    generator = SyntheticDataGenerator(random_state=42)
    X_train, y_train = generator.generate_dataset(n_samples=1000, anomaly_ratio=0.08)
    
    # Initialize pipeline
    pipeline = RobustTrainingPipeline(n_folds=5, random_state=42)
    
    # Train Random Forest with CV
    rf_model, rf_scaler, rf_cv = pipeline.train_random_forest_cv(X_train, y_train)
    
    # Train Isolation Forest with CV
    iso_model, iso_scaler, iso_cv = pipeline.train_isolation_forest_cv(X_train, y_train)
    
    print("\n" + "="*80)
    print("Training Complete!")
    print("="*80)
