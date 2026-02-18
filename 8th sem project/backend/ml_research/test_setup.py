"""
Quick Test - Verify ML Pipeline Setup
======================================
Tests each module individually to ensure proper installation.
"""

import sys

def test_imports():
    """Test if all required packages are installed"""
    print("="*70)
    print("Testing Package Imports...")
    print("="*70)
    
    packages = {
        'numpy': 'NumPy',
        'pandas': 'Pandas',
        'sklearn': 'scikit-learn',
        'matplotlib': 'Matplotlib',
        'seaborn': 'Seaborn',
        'joblib': 'Joblib'
    }
    
    all_ok = True
    for package, name in packages.items():
        try:
            __import__(package)
            print(f"✅ {name:<20s} - OK")
        except ImportError as e:
            print(f"❌ {name:<20s} - MISSING")
            all_ok = False
    
    print()
    return all_ok


def test_dataset_generation():
    """Test dataset generation (small sample)"""
    print("="*70)
    print("Testing Dataset Generation...")
    print("="*70)
    
    try:
        from dataset_generator import DatasetGenerator
        
        print("Generating small test dataset (5 minutes)...")
        generator = DatasetGenerator(output_file='test_dataset.csv')
        generator.generate_dataset(
            duration_minutes=5,
            interval_seconds=10,
            anomaly_probability=0.2
        )
        print("✅ Dataset generation - OK\n")
        return True
    except Exception as e:
        print(f"❌ Dataset generation failed: {e}\n")
        return False


def test_preprocessing():
    """Test preprocessing"""
    print("="*70)
    print("Testing Preprocessing...")
    print("="*70)
    
    try:
        from preprocessing import DataPreprocessor
        import os
        
        if not os.path.exists('test_dataset.csv'):
            print("⚠️  Skipping - no test dataset\n")
            return True
        
        preprocessor = DataPreprocessor(dataset_path='test_dataset.csv')
        data = preprocessor.preprocess_pipeline(
            save_scaler=True,
            scaler_path='models/test_scaler.pkl'
        )
        
        print(f"✅ Preprocessing - OK")
        print(f"   Train samples: {len(data['y_train'])}")
        print(f"   Test samples: {len(data['y_test'])}\n")
        return True
    except Exception as e:
        print(f"❌ Preprocessing failed: {e}\n")
        return False


def test_realtime_prediction():
    """Test real-time prediction"""
    print("="*70)
    print("Testing Real-Time Prediction...")
    print("="*70)
    
    try:
        from realtime_predictor import create_sample_metrics, create_anomaly_metrics
        
        # Test sample creation
        normal = create_sample_metrics()
        anomaly = create_anomaly_metrics()
        
        print("✅ Prediction module - OK")
        print(f"   Sample normal metrics created: {len(normal)} features")
        print(f"   Sample anomaly metrics created: {len(anomaly)} features\n")
        return True
    except Exception as e:
        print(f"❌ Prediction module failed: {e}\n")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🔬 ML RESEARCH PIPELINE - QUICK TEST")
    print("="*70 + "\n")
    
    results = []
    
    # Test 1: Imports
    results.append(("Package Imports", test_imports()))
    
    # Test 2: Dataset Generation
    results.append(("Dataset Generation", test_dataset_generation()))
    
    # Test 3: Preprocessing
    results.append(("Preprocessing", test_preprocessing()))
    
    # Test 4: Prediction Module
    results.append(("Prediction Module", test_realtime_prediction()))
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25s}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print()
    if all_passed:
        print("🎉 All tests passed! Ready to run full pipeline.")
        print("\nNext step: python run_pipeline.py")
    else:
        print("⚠️  Some tests failed. Check error messages above.")
    
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
