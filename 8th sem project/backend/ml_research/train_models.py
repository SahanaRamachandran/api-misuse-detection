"""
Model Training Module for API Anomaly Detection
================================================
Trains Isolation Forest and Random Forest Classifier for anomaly detection.

Models:
1. Isolation Forest (Unsupervised)
   - contamination=0.03
   - n_estimators=200
   
2. Random Forest Classifier (Supervised)
   - n_estimators=200
   - class_weight='balanced'

Author: Research Team
Date: February 2026
"""

import numpy as np
import joblib
import os
import time
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)
from typing import Dict, Tuple


class ModelTrainer:
    """Handles training of anomaly detection models"""
    
    def __init__(self):
        """Initialize model trainer"""
        self.isolation_forest = None
        self.random_forest = None
        self.training_history = {}
    
    def load_preprocessed_data(
        self,
        data_dir: str = 'models'
    ) -> Dict[str, np.ndarray]:
        """
        Load preprocessed data from disk
        
        Args:
            data_dir: Directory containing preprocessed data
        
        Returns:
            Dictionary with data arrays
        """
        print("📂 Loading preprocessed data...")
        
        X_train = np.load(os.path.join(data_dir, 'X_train.npy'))
        X_test = np.load(os.path.join(data_dir, 'X_test.npy'))
        y_train = np.load(os.path.join(data_dir, 'y_train.npy'))
        y_test = np.load(os.path.join(data_dir, 'y_test.npy'))
        
        print(f"   Training set: {X_train.shape}")
        print(f"   Testing set: {X_test.shape}")
        
        return {
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test
        }
    
    def train_isolation_forest(
        self,
        X_train: np.ndarray,
        contamination: float = 0.03,
        n_estimators: int = 200,
        random_state: int = 42
    ) -> IsolationForest:
        """
        Train Isolation Forest model (unsupervised)
        
        Args:
            X_train: Training features
            contamination: Expected proportion of anomalies
            n_estimators: Number of trees
            random_state: Random seed
        
        Returns:
            Trained Isolation Forest model
        """
        print("\n" + "="*70)
        print("🌲 TRAINING ISOLATION FOREST (Unsupervised)")
        print("="*70)
        print(f"   Configuration:")
        print(f"     - contamination: {contamination}")
        print(f"     - n_estimators: {n_estimators}")
        print(f"     - random_state: {random_state}")
        
        start_time = time.time()
        
        self.isolation_forest = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,  # Use all CPU cores
            verbose=1
        )
        
        print("\n   Training in progress...")
        self.isolation_forest.fit(X_train)
        
        training_time = time.time() - start_time
        
        print(f"\n✅ Isolation Forest training complete!")
        print(f"   Training time: {training_time:.2f} seconds")
        
        self.training_history['isolation_forest'] = {
            'training_time': training_time,
            'n_estimators': n_estimators,
            'contamination': contamination
        }
        
        return self.isolation_forest
    
    def train_random_forest(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        n_estimators: int = 200,
        random_state: int = 42
    ) -> RandomForestClassifier:
        """
        Train Random Forest Classifier (supervised)
        
        Args:
            X_train: Training features
            y_train: Training labels
            n_estimators: Number of trees
            random_state: Random seed
        
        Returns:
            Trained Random Forest model
        """
        print("\n" + "="*70)
        print("🌳 TRAINING RANDOM FOREST CLASSIFIER (Supervised)")
        print("="*70)
        print(f"   Configuration:")
        print(f"     - n_estimators: {n_estimators}")
        print(f"     - class_weight: balanced")
        print(f"     - random_state: {random_state}")
        
        # Class distribution
        unique, counts = np.unique(y_train, return_counts=True)
        print(f"\n   Training data distribution:")
        for label, count in zip(unique, counts):
            label_name = "Normal" if label == 0 else "Anomaly"
            print(f"     {label_name}: {count} samples ({count/len(y_train)*100:.2f}%)")
        
        start_time = time.time()
        
        self.random_forest = RandomForestClassifier(
            n_estimators=n_estimators,
            class_weight='balanced',  # Handle imbalanced classes
            random_state=random_state,
            n_jobs=-1,  # Use all CPU cores
            verbose=1,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2
        )
        
        print("\n   Training in progress...")
        self.random_forest.fit(X_train, y_train)
        
        training_time = time.time() - start_time
        
        print(f"\n✅ Random Forest training complete!")
        print(f"   Training time: {training_time:.2f} seconds")
        
        # Feature importances
        feature_names = [
            'avg_response_time', 'request_count', 'error_rate',
            'five_xx_rate', 'four_xx_rate', 'payload_avg_size',
            'unique_ip_count', 'cpu_usage', 'memory_usage'
        ]
        
        importances = self.random_forest.feature_importances_
        sorted_indices = np.argsort(importances)[::-1]
        
        print(f"\n   Top 5 Feature Importances:")
        for i in range(min(5, len(feature_names))):
            idx = sorted_indices[i]
            print(f"     {i+1}. {feature_names[idx]:<20s}: {importances[idx]:.4f}")
        
        self.training_history['random_forest'] = {
            'training_time': training_time,
            'n_estimators': n_estimators,
            'feature_importances': dict(zip(feature_names, importances))
        }
        
        return self.random_forest
    
    def quick_evaluation(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Dict]:
        """
        Quick evaluation on test set
        
        Args:
            X_test: Test features
            y_test: Test labels
        
        Returns:
            Dictionary with evaluation metrics
        """
        print("\n" + "="*70)
        print("📊 QUICK EVALUATION ON TEST SET")
        print("="*70)
        
        results = {}
        
        # Evaluate Isolation Forest
        if self.isolation_forest is not None:
            print("\n🌲 Isolation Forest:")
            if_predictions = self.isolation_forest.predict(X_test)
            # Convert Isolation Forest output (-1, 1) to (1, 0)
            if_predictions = np.where(if_predictions == -1, 1, 0)
            
            accuracy = accuracy_score(y_test, if_predictions)
            precision = precision_score(y_test, if_predictions, zero_division=0)
            recall = recall_score(y_test, if_predictions, zero_division=0)
            f1 = f1_score(y_test, if_predictions, zero_division=0)
            
            print(f"   Accuracy:  {accuracy:.4f}")
            print(f"   Precision: {precision:.4f}")
            print(f"   Recall:    {recall:.4f}")
            print(f"   F1-Score:  {f1:.4f}")
            
            results['isolation_forest'] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1
            }
        
        # Evaluate Random Forest
        if self.random_forest is not None:
            print("\n🌳 Random Forest Classifier:")
            rf_predictions = self.random_forest.predict(X_test)
            
            accuracy = accuracy_score(y_test, rf_predictions)
            precision = precision_score(y_test, rf_predictions, zero_division=0)
            recall = recall_score(y_test, rf_predictions, zero_division=0)
            f1 = f1_score(y_test, rf_predictions, zero_division=0)
            
            try:
                rf_proba = self.random_forest.predict_proba(X_test)[:, 1]
                roc_auc = roc_auc_score(y_test, rf_proba)
                print(f"   Accuracy:  {accuracy:.4f}")
                print(f"   Precision: {precision:.4f}")
                print(f"   Recall:    {recall:.4f}")
                print(f"   F1-Score:  {f1:.4f}")
                print(f"   ROC-AUC:   {roc_auc:.4f}")
                
                results['random_forest'] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'roc_auc': roc_auc
                }
            except:
                print(f"   Accuracy:  {accuracy:.4f}")
                print(f"   Precision: {precision:.4f}")
                print(f"   Recall:    {recall:.4f}")
                print(f"   F1-Score:  {f1:.4f}")
                
                results['random_forest'] = {
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1
                }
        
        return results
    
    def save_models(
        self,
        output_dir: str = 'models'
    ):
        """
        Save trained models to disk
        
        Args:
            output_dir: Directory to save models
        """
        print("\n" + "="*70)
        print("💾 SAVING MODELS")
        print("="*70)
        
        os.makedirs(output_dir, exist_ok=True)
        
        if self.isolation_forest is not None:
            if_path = os.path.join(output_dir, 'isolation_forest.pkl')
            joblib.dump(self.isolation_forest, if_path)
            print(f"   ✓ Isolation Forest saved: {if_path}")
        
        if self.random_forest is not None:
            rf_path = os.path.join(output_dir, 'random_forest.pkl')
            joblib.dump(self.random_forest, rf_path)
            print(f"   ✓ Random Forest saved: {rf_path}")
        
        # Save training history
        history_path = os.path.join(output_dir, 'training_history.pkl')
        joblib.dump(self.training_history, history_path)
        print(f"   ✓ Training history saved: {history_path}")
    
    def train_all_models(
        self,
        data_dir: str = 'models',
        output_dir: str = 'models'
    ) -> Dict[str, Dict]:
        """
        Complete training pipeline for all models
        
        Args:
            data_dir: Directory with preprocessed data
            output_dir: Directory to save trained models
        
        Returns:
            Dictionary with evaluation results
        """
        print("="*70)
        print("🎯 MODEL TRAINING PIPELINE")
        print("="*70)
        
        # Load data
        data = self.load_preprocessed_data(data_dir)
        
        # Train Isolation Forest
        self.train_isolation_forest(
            X_train=data['X_train'],
            contamination=0.03,
            n_estimators=200
        )
        
        # Train Random Forest
        self.train_random_forest(
            X_train=data['X_train'],
            y_train=data['y_train'],
            n_estimators=200
        )
        
        # Quick evaluation
        results = self.quick_evaluation(
            X_test=data['X_test'],
            y_test=data['y_test']
        )
        
        # Save models
        self.save_models(output_dir)
        
        print("\n" + "="*70)
        print("✅ TRAINING PIPELINE COMPLETE")
        print("="*70)
        
        return results


def main():
    """Main execution function"""
    # Initialize trainer
    trainer = ModelTrainer()
    
    # Run complete training pipeline
    results = trainer.train_all_models(
        data_dir='models',
        output_dir='models'
    )
    
    print("\n✨ All models trained and saved!")
    print("\nNext step: Run evaluate.py for detailed model evaluation")


if __name__ == '__main__':
    main()
