"""
Main Orchestration Script for ML Research Pipeline
===================================================
Executes the complete ML pipeline from dataset generation to evaluation.

Pipeline Steps:
1. Dataset Generation
2. Data Preprocessing
3. Model Training
4. Model Evaluation
5. Real-time Prediction Demo

Author: Research Team
Date: February 2026
"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dataset_generator import DatasetGenerator
from preprocessing import DataPreprocessor
from train_models import ModelTrainer
from evaluate import ModelEvaluator
from realtime_predictor import RealtimeAnomalyPredictor, create_sample_metrics, create_anomaly_metrics


def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def run_full_pipeline(
    duration_minutes: int = 120,
    interval_seconds: int = 10,
    skip_dataset_generation: bool = False
):
    """
    Execute complete ML research pipeline
    
    Args:
        duration_minutes: Dataset duration (default 120 min = 2 hours)
        interval_seconds: Metric collection interval (default 10s)
        skip_dataset_generation: Skip dataset generation if already exists
    """
    start_time = time.time()
    
    print_header("🔬 ML RESEARCH PIPELINE - API ANOMALY DETECTION")
    print(f"Configuration:")
    print(f"  - Dataset Duration: {duration_minutes} minutes")
    print(f"  - Metric Interval: {interval_seconds} seconds")
    print(f"  - Expected Samples: {(duration_minutes * 60) // interval_seconds}")
    
    # Step 1: Dataset Generation
    if not skip_dataset_generation:
        print_header("STEP 1/5: Dataset Generation")
        generator = DatasetGenerator(output_file='api_telemetry_dataset.csv')
        generator.generate_dataset(
            duration_minutes=duration_minutes,
            interval_seconds=interval_seconds,
            anomaly_probability=0.15
        )
    else:
        print_header("STEP 1/5: Dataset Generation (SKIPPED)")
        print("Using existing dataset: api_telemetry_dataset.csv")
    
    # Step 2: Data Preprocessing
    print_header("STEP 2/5: Data Preprocessing")
    preprocessor = DataPreprocessor(dataset_path='api_telemetry_dataset.csv')
    data = preprocessor.preprocess_pipeline(
        save_scaler=True,
        scaler_path='models/scaler.pkl'
    )
    
    # Save preprocessed data
    import numpy as np
    import os
    os.makedirs('models', exist_ok=True)
    np.save('models/X_train.npy', data['X_train'])
    np.save('models/X_test.npy', data['X_test'])
    np.save('models/y_train.npy', data['y_train'])
    np.save('models/y_test.npy', data['y_test'])
    
    # Step 3: Model Training
    print_header("STEP 3/5: Model Training")
    trainer = ModelTrainer()
    trainer.train_all_models(data_dir='models', output_dir='models')
    
    # Step 4: Model Evaluation
    print_header("STEP 4/5: Model Evaluation")
    evaluator = ModelEvaluator(models_dir='models', output_dir='evaluation_results')
    evaluator.run_full_evaluation()
    
    # Step 5: Real-time Prediction Demo
    print_header("STEP 5/5: Real-time Prediction Demo")
    predictor = RealtimeAnomalyPredictor(
        models_dir='models',
        use_random_forest=True,
        use_isolation_forest=True
    )
    
    # Test with normal metrics
    print("\n🔍 Testing with NORMAL metrics:")
    normal_metrics = create_sample_metrics()
    result_normal = predictor.predict(normal_metrics)
    primary = result_normal['primary_prediction']
    print(f"  Prediction: {primary['prediction_label']}")
    print(f"  Confidence: {primary['confidence']:.4f}")
    print(f"  Anomaly Score: {primary['anomaly_score']:.4f}")
    
    # Test with anomalous metrics
    print("\n⚠️  Testing with ANOMALOUS metrics:")
    anomaly_metrics = create_anomaly_metrics()
    result_anomaly = predictor.predict(anomaly_metrics)
    primary = result_anomaly['primary_prediction']
    print(f"  Prediction: {primary['prediction_label']}")
    print(f"  Confidence: {primary['confidence']:.4f}")
    print(f"  Anomaly Score: {primary['anomaly_score']:.4f}")
    
    # Final Summary
    elapsed_time = time.time() - start_time
    print_header("✅ PIPELINE COMPLETE")
    print(f"Total execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)\n")
    print("📁 Generated Files:")
    print("  - api_telemetry_dataset.csv (raw dataset)")
    print("  - models/scaler.pkl (feature scaler)")
    print("  - models/random_forest.pkl (RF model)")
    print("  - models/isolation_forest.pkl (IF model)")
    print("  - models/X_train.npy, X_test.npy, y_train.npy, y_test.npy")
    print("  - evaluation_results/*.png (visualizations)")
    print("  - evaluation_results/model_comparison.csv")
    
    print("\n📊 Next Steps:")
    print("  1. Review evaluation_results/ for model performance")
    print("  2. Use realtime_predictor.py for production predictions")
    print("  3. Integrate into your API monitoring system")
    
    print("\n📚 Publication Ready:")
    print("  - Randomized anomaly injection ✓")
    print("  - Proper train/test split (80/20) ✓")
    print("  - StandardScaler normalization ✓")
    print("  - Multiple ML models (RF + IF) ✓")
    print("  - Comprehensive evaluation metrics ✓")
    print("  - Visualizations (confusion matrix, ROC, PR curves) ✓")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ML Research Pipeline for API Anomaly Detection'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=120,
        help='Dataset duration in minutes (default: 120)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Metric collection interval in seconds (default: 10)'
    )
    parser.add_argument(
        '--skip-dataset',
        action='store_true',
        help='Skip dataset generation (use existing dataset)'
    )
    
    args = parser.parse_args()
    
    run_full_pipeline(
        duration_minutes=args.duration,
        interval_seconds=args.interval,
        skip_dataset_generation=args.skip_dataset
    )


if __name__ == '__main__':
    main()
