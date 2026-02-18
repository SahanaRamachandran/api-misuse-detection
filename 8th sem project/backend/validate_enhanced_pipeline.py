"""
Quick Validation Script

Validates that all components of the enhanced training pipeline are working correctly.
"""

import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from synthetic_data_generator import SyntheticDataGenerator
        print("  [OK] synthetic_data_generator")
    except Exception as e:
        print(f"  [FAIL] synthetic_data_generator: {e}")
        return False
    
    try:
        from robust_training_pipeline import RobustTrainingPipeline
        print("  [OK] robust_training_pipeline")
    except Exception as e:
        print(f"  [FAIL] robust_training_pipeline: {e}")
        return False
    
    try:
        from model_comparison import ModelComparator
        print("  [OK] model_comparison")
    except Exception as e:
        print(f"  [FAIL] model_comparison: {e}")
        return False
    
    try:
        from train_robust_models import EnhancedTrainingOrchestrator
        print("  [OK] train_robust_models")
    except Exception as e:
        print(f"  [FAIL] train_robust_models: {e}")
        return False
    
    return True


def test_data_generation():
    """Test synthetic data generation."""
    print("\nTesting synthetic data generation...")
    
    try:
        from synthetic_data_generator import SyntheticDataGenerator
        
        generator = SyntheticDataGenerator(random_state=42)
        X, y = generator.generate_dataset(n_samples=100, anomaly_ratio=0.1)
        
        assert len(X) == 100, f"Expected 100 samples, got {len(X)}"
        assert len(y) == 100, f"Expected 100 labels, got {len(y)}"
        assert X.shape[1] == 9, f"Expected 9 features, got {X.shape[1]}"
        assert 5 <= y.sum() <= 15, f"Expected ~10 anomalies, got {y.sum()}"
        
        print(f"  [OK] Generated {len(X)} samples with {y.sum()} anomalies")
        print(f"  [OK] Feature columns: {list(X.columns)}")
        return True
        
    except Exception as e:
        print(f"  [FAIL] Data generation failed: {e}")
        return False


def test_training_pipeline():
    """Test training pipeline (quick version)."""
    print("\nTesting training pipeline...")
    
    try:
        from synthetic_data_generator import SyntheticDataGenerator
        from robust_training_pipeline import RobustTrainingPipeline
        
        # Generate small dataset
        generator = SyntheticDataGenerator(random_state=42)
        X, y = generator.generate_dataset(n_samples=200, anomaly_ratio=0.1)
        
        # Test with 2 folds for speed
        pipeline = RobustTrainingPipeline(n_folds=2, random_state=42)
        
        # Train Random Forest
        rf_model, rf_scaler, rf_cv = pipeline.train_random_forest_cv(X, y)
        
        assert rf_model is not None, "RF model is None"
        assert rf_scaler is not None, "RF scaler is None"
        assert 'mean' in rf_cv.get('accuracy', {}), "CV results missing"
        
        print(f"  [OK] Random Forest trained successfully")
        print(f"  [OK] CV Accuracy: {rf_cv['accuracy']['mean']:.4f} +/- {rf_cv['accuracy']['std']:.4f}")
        
        # Train Isolation Forest
        iso_model, iso_scaler, iso_cv = pipeline.train_isolation_forest_cv(X, y)
        
        assert iso_model is not None, "ISO model is None"
        assert iso_scaler is not None, "ISO scaler is None"
        
        print(f"  [OK] Isolation Forest trained successfully")
        print(f"  [OK] CV Accuracy: {iso_cv['accuracy']['mean']:.4f} +/- {iso_cv['accuracy']['std']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Training pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_comparison():
    """Test model comparison (quick version)."""
    print("\nTesting model comparison...")
    
    try:
        from synthetic_data_generator import SyntheticDataGenerator
        from model_comparison import ModelComparator
        import numpy as np
        import pandas as pd
        
        # Create test scenarios
        generator = SyntheticDataGenerator(random_state=42)
        X_test, y_test = generator.generate_dataset(n_samples=100, anomaly_ratio=0.1)
        
        test_scenarios = {
            'test': (X_test, y_test)
        }
        
        comparator = ModelComparator()
        
        # Try to load models (may not exist yet)
        comparator.load_csic_baseline()
        comparator.load_robust_models()
        
        if len(comparator.models) > 0:
            print(f"  [OK] Loaded {len(comparator.models)} models")
            
            # Test evaluation
            results = comparator.compare_on_scenarios(test_scenarios)
            print(f"  [OK] Evaluation completed: {len(results)} results")
        else:
            print("  [WARN] No models found (run training first)")
        
        return True
        
    except Exception as e:
        print(f"  [FAIL] Model comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_directory_structure():
    """Test that required directories exist."""
    print("\nTesting directory structure...")
    
    required_dirs = [
        'models',
        'datasets',
        'datasets/processed'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [WARN] {dir_path} (will be created)")
            path.mkdir(parents=True, exist_ok=True)
    
    return True


def main():
    """Run all validation tests."""
    print("="*80)
    print("ENHANCED TRAINING PIPELINE - VALIDATION")
    print("="*80)
    
    results = {}
    
    results['imports'] = test_imports()
    results['directories'] = test_directory_structure()
    results['data_generation'] = test_data_generation()
    results['training'] = test_training_pipeline()
    results['comparison'] = test_model_comparison()
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status:12s} {test_name}")
    
    print("="*80)
    
    if all_passed:
        print("\n[OK] All validations passed! Pipeline is ready to use.")
        print("\nRun the full pipeline with:")
        print("   python train_robust_models.py")
        return 0
    else:
        print("\n[FAIL] Some validations failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
