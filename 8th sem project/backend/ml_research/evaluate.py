"""
Model Evaluation Module for API Anomaly Detection
==================================================
Comprehensive evaluation with metrics, visualizations, and analysis.

Metrics:
- Confusion Matrix
- Precision, Recall, F1-Score
- ROC-AUC Curve
- Anomaly Score Distribution
- Threshold Tuning

Author: Research Team
Date: February 2026
"""

import numpy as np
import pandas as pd
import joblib
import os
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    precision_recall_curve,
    roc_curve,
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)
from typing import Dict, Tuple


class ModelEvaluator:
    """Comprehensive model evaluation and visualization"""
    
    def __init__(self, models_dir: str = 'models', output_dir: str = 'evaluation_results'):
        """
        Initialize evaluator
        
        Args:
            models_dir: Directory containing trained models
            output_dir: Directory to save evaluation results
        """
        self.models_dir = models_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Load models
        self.isolation_forest = None
        self.random_forest = None
        self.scaler = None
        
        self._load_models()
    
    def _load_models(self):
        """Load trained models from disk"""
        print("📂 Loading trained models...")
        
        if_path = os.path.join(self.models_dir, 'isolation_forest.pkl')
        rf_path = os.path.join(self.models_dir, 'random_forest.pkl')
        scaler_path = os.path.join(self.models_dir, 'scaler.pkl')
        
        if os.path.exists(if_path):
            self.isolation_forest = joblib.load(if_path)
            print(f"   ✓ Loaded Isolation Forest")
        
        if os.path.exists(rf_path):
            self.random_forest = joblib.load(rf_path)
            print(f"   ✓ Loaded Random Forest")
        
        if os.path.exists(scaler_path):
            self.scaler = joblib.load(scaler_path)
            print(f"   ✓ Loaded Scaler")
    
    def load_test_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load test data"""
        X_test = np.load(os.path.join(self.models_dir, 'X_test.npy'))
        y_test = np.load(os.path.join(self.models_dir, 'y_test.npy'))
        return X_test, y_test
    
    def plot_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        model_name: str,
        save_path: str = None
    ):
        """
        Plot confusion matrix
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            model_name: Name of model for title
            save_path: Path to save figure
        """
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(
            cm,
            annot=True,
            fmt='d',
            cmap='Blues',
            xticklabels=['Normal', 'Anomaly'],
            yticklabels=['Normal', 'Anomaly'],
            cbar_kws={'label': 'Count'}
        )
        plt.title(f'Confusion Matrix - {model_name}', fontsize=14, fontweight='bold')
        plt.ylabel('True Label', fontsize=12)
        plt.xlabel('Predicted Label', fontsize=12)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   ✓ Saved: {save_path}")
        
        plt.close()
    
    def plot_roc_curve(
        self,
        y_true: np.ndarray,
        y_scores: np.ndarray,
        model_name: str,
        save_path: str = None
    ):
        """
        Plot ROC curve
        
        Args:
            y_true: True labels
            y_scores: Prediction scores/probabilities
            model_name: Name of model
            save_path: Path to save figure
        """
        fpr, tpr, thresholds = roc_curve(y_true, y_scores)
        roc_auc = roc_auc_score(y_true, y_scores)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title(f'ROC Curve - {model_name}', fontsize=14, fontweight='bold')
        plt.legend(loc="lower right", fontsize=10)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   ✓ Saved: {save_path}")
        
        plt.close()
    
    def plot_precision_recall_curve(
        self,
        y_true: np.ndarray,
        y_scores: np.ndarray,
        model_name: str,
        save_path: str = None
    ):
        """
        Plot Precision-Recall curve
        
        Args:
            y_true: True labels
            y_scores: Prediction scores/probabilities
            model_name: Name of model
            save_path: Path to save figure
        """
        precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
        
        plt.figure(figsize=(8, 6))
        plt.plot(recall, precision, color='blue', lw=2, label='Precision-Recall curve')
        plt.xlabel('Recall', fontsize=12)
        plt.ylabel('Precision', fontsize=12)
        plt.title(f'Precision-Recall Curve - {model_name}', fontsize=14, fontweight='bold')
        plt.legend(loc="lower left", fontsize=10)
        plt.grid(alpha=0.3)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   ✓ Saved: {save_path}")
        
        plt.close()
    
    def plot_anomaly_score_distribution(
        self,
        scores: np.ndarray,
        y_true: np.ndarray,
        model_name: str,
        save_path: str = None
    ):
        """
        Plot anomaly score distribution
        
        Args:
            scores: Anomaly scores
            y_true: True labels
            model_name: Name of model
            save_path: Path to save figure
        """
        plt.figure(figsize=(10, 6))
        
        # Separate scores by true label
        normal_scores = scores[y_true == 0]
        anomaly_scores = scores[y_true == 1]
        
        plt.hist(normal_scores, bins=50, alpha=0.6, label='Normal', color='green', edgecolor='black')
        plt.hist(anomaly_scores, bins=50, alpha=0.6, label='Anomaly', color='red', edgecolor='black')
        
        plt.xlabel('Anomaly Score', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.title(f'Anomaly Score Distribution - {model_name}', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(alpha=0.3, axis='y')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"   ✓ Saved: {save_path}")
        
        plt.close()
    
    def evaluate_random_forest(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate Random Forest Classifier"""
        print("\n" + "="*70)
        print("🌳 RANDOM FOREST EVALUATION")
        print("="*70)
        
        # Predictions
        y_pred = self.random_forest.predict(X_test)
        y_proba = self.random_forest.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_test, y_proba)
        
        print(f"\n📊 Performance Metrics:")
        print(f"   Accuracy:  {accuracy:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        print(f"   ROC-AUC:   {roc_auc:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n📈 Confusion Matrix:")
        print(f"   True Negatives:  {cm[0, 0]}")
        print(f"   False Positives: {cm[0, 1]}")
        print(f"   False Negatives: {cm[1, 0]}")
        print(f"   True Positives:  {cm[1, 1]}")
        
        # Classification report
        print(f"\n📋 Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))
        
        # Generate visualizations
        print(f"\n📊 Generating visualizations...")
        self.plot_confusion_matrix(
            y_test, y_pred, 'Random Forest',
            os.path.join(self.output_dir, 'rf_confusion_matrix.png')
        )
        self.plot_roc_curve(
            y_test, y_proba, 'Random Forest',
            os.path.join(self.output_dir, 'rf_roc_curve.png')
        )
        self.plot_precision_recall_curve(
            y_test, y_proba, 'Random Forest',
            os.path.join(self.output_dir, 'rf_precision_recall.png')
        )
        self.plot_anomaly_score_distribution(
            y_proba, y_test, 'Random Forest',
            os.path.join(self.output_dir, 'rf_score_distribution.png')
        )
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm.tolist()
        }
    
    def evaluate_isolation_forest(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """Evaluate Isolation Forest"""
        print("\n" + "="*70)
        print("🌲 ISOLATION FOREST EVALUATION")
        print("="*70)
        
        # Predictions (-1 for anomaly, 1 for normal)
        y_pred_raw = self.isolation_forest.predict(X_test)
        y_pred = np.where(y_pred_raw == -1, 1, 0)  # Convert to 0/1
        
        # Anomaly scores (lower = more anomalous)
        anomaly_scores = self.isolation_forest.score_samples(X_test)
        # Invert for consistency (higher = more anomalous)
        anomaly_scores_inverted = -anomaly_scores
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        print(f"\n📊 Performance Metrics:")
        print(f"   Accuracy:  {accuracy:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n📈 Confusion Matrix:")
        print(f"   True Negatives:  {cm[0, 0]}")
        print(f"   False Positives: {cm[0, 1]}")
        print(f"   False Negatives: {cm[1, 0]}")
        print(f"   True Positives:  {cm[1, 1]}")
        
        # Generate visualizations
        print(f"\n📊 Generating visualizations...")
        self.plot_confusion_matrix(
            y_test, y_pred, 'Isolation Forest',
            os.path.join(self.output_dir, 'if_confusion_matrix.png')
        )
        self.plot_anomaly_score_distribution(
            anomaly_scores_inverted, y_test, 'Isolation Forest',
            os.path.join(self.output_dir, 'if_score_distribution.png')
        )
        
        # Threshold tuning
        print(f"\n🎯 Threshold Tuning Analysis:")
        self._analyze_threshold_tuning(anomaly_scores_inverted, y_test)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm.tolist()
        }
    
    def _analyze_threshold_tuning(self, scores: np.ndarray, y_true: np.ndarray):
        """Analyze different threshold values"""
        percentiles = [90, 95, 97, 99]
        
        print(f"\n   Testing different anomaly score thresholds:")
        for percentile in percentiles:
            threshold = np.percentile(scores, percentile)
            y_pred_threshold = (scores >= threshold).astype(int)
            
            precision = precision_score(y_true, y_pred_threshold, zero_division=0)
            recall = recall_score(y_true, y_pred_threshold, zero_division=0)
            f1 = f1_score(y_true, y_pred_threshold, zero_division=0)
            
            print(f"     {percentile}th percentile (threshold={threshold:.4f}):")
            print(f"       Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    
    def generate_comparison_report(
        self,
        rf_metrics: Dict,
        if_metrics: Dict
    ):
        """Generate comparison report"""
        print("\n" + "="*70)
        print("📊 MODEL COMPARISON REPORT")
        print("="*70)
        
        comparison = pd.DataFrame({
            'Random Forest': [
                rf_metrics['accuracy'],
                rf_metrics['precision'],
                rf_metrics['recall'],
                rf_metrics['f1_score'],
                rf_metrics.get('roc_auc', 'N/A')
            ],
            'Isolation Forest': [
                if_metrics['accuracy'],
                if_metrics['precision'],
                if_metrics['recall'],
                if_metrics['f1_score'],
                'N/A'
            ]
        }, index=['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC'])
        
        print("\n" + comparison.to_string())
        
        # Save to CSV
        comparison.to_csv(os.path.join(self.output_dir, 'model_comparison.csv'))
        print(f"\n✓ Comparison saved to: {os.path.join(self.output_dir, 'model_comparison.csv')}")
        
        # Determine best model
        print(f"\n🏆 Best Model:")
        if rf_metrics['f1_score'] > if_metrics['f1_score']:
            print(f"   Random Forest (F1-Score: {rf_metrics['f1_score']:.4f})")
        else:
            print(f"   Isolation Forest (F1-Score: {if_metrics['f1_score']:.4f})")
    
    def run_full_evaluation(self):
        """Run complete evaluation pipeline"""
        print("="*70)
        print("🔬 COMPREHENSIVE MODEL EVALUATION")
        print("="*70)
        
        # Load test data
        X_test, y_test = self.load_test_data()
        print(f"\nTest set size: {len(y_test)} samples")
        print(f"  Normal: {(y_test == 0).sum()} ({(y_test == 0).sum()/len(y_test)*100:.2f}%)")
        print(f"  Anomaly: {(y_test == 1).sum()} ({(y_test == 1).sum()/len(y_test)*100:.2f}%)")
        
        # Evaluate Random Forest
        rf_metrics = self.evaluate_random_forest(X_test, y_test)
        
        # Evaluate Isolation Forest
        if_metrics = self.evaluate_isolation_forest(X_test, y_test)
        
        # Generate comparison
        self.generate_comparison_report(rf_metrics, if_metrics)
        
        print("\n" + "="*70)
        print("✅ EVALUATION COMPLETE")
        print("="*70)
        print(f"\nResults saved to: {self.output_dir}/")


def main():
    """Main execution function"""
    evaluator = ModelEvaluator(
        models_dir='models',
        output_dir='evaluation_results'
    )
    
    evaluator.run_full_evaluation()
    
    print("\n✨ Evaluation complete! Check evaluation_results/ for visualizations.")


if __name__ == '__main__':
    main()
