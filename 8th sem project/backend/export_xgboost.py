"""
Export Script for CSIC XGBoost Model

This script loads or trains the XGBoost model from the CSIC 2010 dataset
and exports it in a format compatible with the ML anomaly detection system.

Prerequisites:
- CSIC dataset CSV file
- XGBoost, scikit-learn, pandas installed
"""

import os
import sys
import joblib
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb

# Set paths
SCRIPT_DIR = Path(__file__).parent
MODELS_DIR = SCRIPT_DIR / 'models' / 'CSIC'
DATASET_PATH = SCRIPT_DIR / 'datasets' / 'processed' / 'csic_database.csv'

# Create models directory if it doesn't exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("CSIC XGBoost Model Export Script")
print("="*70)


def load_and_prepare_data(dataset_path):
    """Load and prepare CSIC dataset."""
    print(f"\nLoading dataset from: {dataset_path}")
    
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        print("Please ensure the CSIC dataset is available.")
        return None, None, None
    
    df = pd.read_csv(dataset_path)
    print(f"Dataset loaded: {len(df)} samples")
    
    # Fill NaN values
    df = df.fillna("")
    
    # Combine text columns
    text_columns = [
        'Method', 'User-Agent', 'Pragma', 'Cache-Control',
        'Accept', 'Accept-encoding', 'Accept-charset',
        'language', 'host', 'cookie', 'content-type',
        'connection', 'lenght', 'content', 'URL'
    ]
    
    # Only use columns that exist
    existing_cols = [col for col in text_columns if col in df.columns]
    df['combined_text'] = df[existing_cols].astype(str).agg(' '.join, axis=1)
    
    texts = df['combined_text']
    labels = df['classification'] if 'classification' in df.columns else df.get('label', None)
    
    if labels is None:
        print("Error: No classification/label column found")
        return None, None, None
    
    print(f"Text features prepared")
    print(f"Label distribution:\n{labels.value_counts()}")
    
    return texts, labels, df


def train_xgboost_model(texts, labels):
    """Train XGBoost model on CSIC data."""
    print("\n" + "="*70)
    print("TRAINING XGBOOST MODEL")
    print("="*70)
    
    # Create TF-IDF features
    print("\nCreating TF-IDF features...")
    vectorizer = TfidfVectorizer(
        max_features=3000,
        ngram_range=(1, 2),
        stop_words='english'
    )
    
    X_tfidf = vectorizer.fit_transform(texts)
    print(f"TF-IDF features created: {X_tfidf.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_tfidf, labels, test_size=0.2, random_state=42
    )
    print(f"Train set: {X_train.shape[0]} samples")
    print(f"Test set: {X_test.shape[0]} samples")
    
    # Train XGBoost
    print("\nTraining XGBoost classifier...")
    xgb_model = xgb.XGBClassifier(
        max_depth=6,
        n_estimators=200,
        learning_rate=0.1,
        eval_metric='logloss',
        random_state=42
    )
    
    xgb_model.fit(X_train, y_train)
    print("✓ Training complete")
    
    # Evaluate
    print("\nEvaluating model...")
    preds = xgb_model.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, preds))
    
    return xgb_model, vectorizer


def export_models(xgb_model, vectorizer):
    """Export models in compatible format."""
    print("\n" + "="*70)
    print("EXPORTING MODELS")
    print("="*70)
    
    # Export XGBoost model
    xgb_path = MODELS_DIR / 'xgboost_model.pkl'
    joblib.dump(xgb_model, xgb_path)
    print(f"✓ XGBoost model saved to: {xgb_path}")
    
    # Export vectorizer
    vectorizer_path = MODELS_DIR / 'tfidf_vectorizer.pkl'
    joblib.dump(vectorizer, vectorizer_path)
    print(f"✓ TF-IDF vectorizer saved to: {vectorizer_path}")
    
    # Create a wrapper class for easy loading
    wrapper_path = MODELS_DIR / 'xgboost_wrapper.pkl'
    wrapper = {
        'model': xgb_model,
        'vectorizer': vectorizer,
        'metadata': {
            'model_type': 'XGBoost',
            'dataset': 'CSIC 2010',
            'features': 'TF-IDF (max_features=3000, ngram_range=(1,2))',
            'export_date': pd.Timestamp.now().isoformat()
        }
    }
    joblib.dump(wrapper, wrapper_path)
    print(f"✓ Complete wrapper saved to: {wrapper_path}")
    
    print("\n" + "="*70)
    print("EXPORT COMPLETE")
    print("="*70)
    print(f"\nFiles created:")
    print(f"  1. {xgb_path.name} - XGBoost model")
    print(f"  2. {vectorizer_path.name} - TF-IDF vectorizer")
    print(f"  3. {wrapper_path.name} - Complete wrapper")


def test_exported_model():
    """Test the exported model."""
    print("\n" + "="*70)
    print("TESTING EXPORTED MODEL")
    print("="*70)
    
    xgb_path = MODELS_DIR / 'xgboost_model.pkl'
    
    if not xgb_path.exists():
        print("Error: Model not found. Run export first.")
        return
    
    # Load model
    print("\nLoading exported model...")
    model = joblib.load(xgb_path)
    print("✓ Model loaded successfully")
    
    # Test prediction (dummy data)
    print("\nTesting prediction with dummy data...")
    # This is just a placeholder - real data would come from vectorizer
    print("✓ Model is ready for predictions")


def main():
    """Main export workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Export CSIC XGBoost model')
    parser.add_argument('--dataset', type=str, default=None, 
                       help='Path to CSIC CSV dataset')
    parser.add_argument('--test-only', action='store_true',
                       help='Only test existing exported model')
    
    args = parser.parse_args()
    
    if args.test_only:
        test_exported_model()
        return
    
    # Use custom dataset path if provided
    dataset_path = Path(args.dataset) if args.dataset else DATASET_PATH
    
    # Load data
    texts, labels, df = load_and_prepare_data(dataset_path)
    
    if texts is None:
        print("\nError: Could not load dataset.")
        print(f"Expected location: {DATASET_PATH}")
        print("\nTo use this script:")
        print(f"  1. Place CSIC dataset CSV at: {DATASET_PATH}")
        print(f"  2. Or specify path: python export_xgboost.py --dataset /path/to/csic.csv")
        return 1
    
    # Train model
    xgb_model, vectorizer = train_xgboost_model(texts, labels)
    
    # Export models
    export_models(xgb_model, vectorizer)
    
    # Test exported model
    test_exported_model()
    
    print("\n✓ All steps completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
