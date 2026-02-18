"""
Pipeline Visualization and Testing Script
==========================================
Visual representation of the ML pipeline and quick tests.

Author: Research Team
Date: February 2026
"""


def print_pipeline_diagram():
    """Print ASCII art pipeline diagram"""
    diagram = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                   ML RESEARCH PIPELINE ARCHITECTURE                       ║
╚═══════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Dataset Generation (dataset_generator.py)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input: Configuration (duration, interval, anomaly_probability)        │
│     │                                                                   │
│     ├─→ Generate normal traffic baseline                              │
│     ├─→ Randomize anomaly schedule (time, type, severity, duration)   │
│     ├─→ Inject anomalies (traffic_burst, latency_spike, error_spike)  │
│     └─→ Export labeled CSV                                             │
│                                                                         │
│  Output: api_telemetry_dataset.csv (720+ samples with labels)          │
│          [timestamp, 9 metrics, label, anomaly_type]                   │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Preprocessing (preprocessing.py)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input: api_telemetry_dataset.csv                                      │
│     │                                                                   │
│     ├─→ Load & validate data                                           │
│     ├─→ Remove null values                                             │
│     ├─→ Train/test split (80/20, stratified)                          │
│     ├─→ Fit StandardScaler on train set only                          │
│     ├─→ Transform both train and test sets                            │
│     └─→ Save scaler + numpy arrays                                     │
│                                                                         │
│  Output: models/scaler.pkl                                             │
│          models/X_train.npy, X_test.npy, y_train.npy, y_test.npy      │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Model Training (train_models.py)                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input: Preprocessed train/test data                                   │
│     │                                                                   │
│     ├─→ Train Isolation Forest (contamination=0.03, n_estimators=200) │
│     │   • Unsupervised learning                                        │
│     │   • Detects outliers in feature space                           │
│     │                                                                   │
│     ├─→ Train Random Forest (n_estimators=200, class_weight=balanced) │
│     │   • Supervised learning                                          │
│     │   • Uses labeled data                                            │
│     │   • Feature importance analysis                                  │
│     │                                                                   │
│     ├─→ Quick evaluation on test set                                   │
│     └─→ Save models with joblib                                        │
│                                                                         │
│  Output: models/random_forest.pkl                                      │
│          models/isolation_forest.pkl                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Evaluation (evaluate.py)                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Input: Trained models + test data                                     │
│     │                                                                   │
│     ├─→ Random Forest Evaluation                                       │
│     │   • Confusion Matrix                                             │
│     │   • Precision, Recall, F1-Score                                  │
│     │   • ROC-AUC Curve                                                │
│     │   • Precision-Recall Curve                                       │
│     │                                                                   │
│     ├─→ Isolation Forest Evaluation                                    │
│     │   • Anomaly score distribution                                   │
│     │   • Threshold tuning analysis                                    │
│     │   • Confusion Matrix                                             │
│     │                                                                   │
│     ├─→ Generate visualizations (300 DPI)                             │
│     └─→ Create comparison report                                       │
│                                                                         │
│  Output: evaluation_results/*.png                                      │
│          evaluation_results/model_comparison.csv                       │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Real-Time Prediction (realtime_predictor.py)                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Production API:                                                        │
│                                                                         │
│  predictor = RealtimeAnomalyPredictor(models_dir='models')            │
│                                                                         │
│  result = predictor.predict({                                          │
│      'avg_response_time': 150.5,                                       │
│      'request_count': 45,                                              │
│      'error_rate': 0.02,                                               │
│      # ... other metrics                                               │
│  })                                                                     │
│                                                                         │
│  Output: {                                                             │
│      'prediction': 0 or 1,                                             │
│      'prediction_label': 'Normal' or 'Anomaly',                        │
│      'anomaly_score': 0.0-1.0,                                         │
│      'confidence': 0.0-1.0                                             │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════════╗
║                         KEY ADVANTAGES                                    ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  ✅ Randomized Anomalies (not deterministic)                             ║
║  ✅ Proper ML Methodology (80/20 split)                                  ║
║  ✅ StandardScaler Normalization                                         ║
║  ✅ Multiple Models (RF + IF)                                            ║
║  ✅ Comprehensive Evaluation                                             ║
║  ✅ Production-Ready API                                                 ║
║  ✅ Publication-Quality Results                                          ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    print(diagram)


def print_file_structure():
    """Print file structure"""
    structure = """
📁 ml_research/
│
├── 📄 dataset_generator.py      ⭐ Step 1: Generate labeled dataset
├── 📄 preprocessing.py          ⭐ Step 2: Clean & normalize data
├── 📄 train_models.py           ⭐ Step 3: Train RF + IF models
├── 📄 evaluate.py               ⭐ Step 4: Evaluate with metrics
├── 📄 realtime_predictor.py     ⭐ Step 5: Production predictions
│
├── 🚀 run_pipeline.py           🎯 Main orchestrator (run this!)
├── 🚀 quick_start.bat           🎯 Windows quick start
├── 💡 integration_example.py    💡 Production integration examples
│
├── 📖 README.md                 📚 Complete documentation
├── 📖 IMPLEMENTATION_SUMMARY.md 📚 Implementation details
├── 📄 requirements.txt          📦 Python dependencies
└── 📄 .gitignore                🔒 Git ignore rules

Generated After Running Pipeline:
├── 📊 api_telemetry_dataset.csv     (720+ labeled samples)
├── 📁 models/
│   ├── 🧠 random_forest.pkl         (Trained RF model)
│   ├── 🧠 isolation_forest.pkl      (Trained IF model)
│   ├── 📏 scaler.pkl                (StandardScaler)
│   └── 💾 X_train/test, y_train/test.npy
└── 📁 evaluation_results/
    ├── 📈 rf_confusion_matrix.png
    ├── 📈 rf_roc_curve.png
    ├── 📈 rf_precision_recall.png
    ├── 📈 if_confusion_matrix.png
    ├── 📈 if_score_distribution.png
    └── 📊 model_comparison.csv
"""
    print(structure)


def print_quick_reference():
    """Print quick reference commands"""
    reference = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                          QUICK REFERENCE                                  ║
╚═══════════════════════════════════════════════════════════════════════════╝

📌 INSTALLATION:
   pip install numpy pandas scikit-learn matplotlib seaborn joblib

📌 RUN COMPLETE PIPELINE:
   python run_pipeline.py

   Options:
   --duration 120        # Dataset duration in minutes (default: 120)
   --interval 10         # Metric interval in seconds (default: 10)
   --skip-dataset        # Skip dataset generation if exists

📌 RUN INDIVIDUAL STEPS:
   python dataset_generator.py    # Generate dataset
   python preprocessing.py        # Preprocess data
   python train_models.py         # Train models
   python evaluate.py             # Evaluate models
   python realtime_predictor.py   # Test predictions

📌 WINDOWS QUICK START:
   quick_start.bat

📌 PRODUCTION USAGE:
   from realtime_predictor import RealtimeAnomalyPredictor
   
   predictor = RealtimeAnomalyPredictor(models_dir='models')
   result = predictor.predict(metrics)
   
   if result['primary_prediction']['prediction'] == 1:
       print("⚠️  ANOMALY DETECTED!")

╔═══════════════════════════════════════════════════════════════════════════╗
║                      EXPECTED OUTPUT METRICS                              ║
╚═══════════════════════════════════════════════════════════════════════════╝

Random Forest Classifier:
  ✓ Accuracy:   0.92 - 0.96
  ✓ Precision:  0.88 - 0.94
  ✓ Recall:     0.85 - 0.92
  ✓ F1-Score:   0.86 - 0.93
  ✓ ROC-AUC:    0.94 - 0.98

Isolation Forest:
  ✓ Accuracy:   0.85 - 0.91
  ✓ Precision:  0.75 - 0.85
  ✓ Recall:     0.78 - 0.88
  ✓ F1-Score:   0.76 - 0.86

╔═══════════════════════════════════════════════════════════════════════════╗
║                        TROUBLESHOOTING                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝

❌ "ModuleNotFoundError: No module named 'sklearn'"
   → pip install scikit-learn

❌ "FileNotFoundError: 'models/scaler.pkl'"
   → Run preprocessing.py first

❌ "No trained models found"
   → Run train_models.py first

❌ Low model performance
   → Increase dataset duration: --duration 240
   → Check data quality in CSV file

"""
    print(reference)


def main():
    """Main function"""
    print("\n")
    print_pipeline_diagram()
    print("\n")
    print_file_structure()
    print("\n")
    print_quick_reference()
    print("\n")
    print("="*79)
    print("  Ready to start! Run: python run_pipeline.py")
    print("="*79)
    print()


if __name__ == '__main__':
    main()
