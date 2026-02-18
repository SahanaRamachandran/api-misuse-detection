# Research-Grade ML Pipeline for API Anomaly Detection

## 🎯 Overview

This is a **production-ready, research-grade** machine learning pipeline for API anomaly detection. Designed for academic publication and real-world deployment.

### Key Features
- ✅ **Randomized Anomaly Injection** - No deterministic patterns
- ✅ **Proper ML Methodology** - 80/20 train/test split, stratification
- ✅ **StandardScaler Normalization** - Prevents feature bias
- ✅ **Multiple ML Models** - Random Forest + Isolation Forest
- ✅ **Comprehensive Evaluation** - Confusion matrix, ROC-AUC, precision, recall, F1
- ✅ **Publication-Ready Visualizations** - High-DPI charts and graphs
- ✅ **Real-Time Prediction** - Production-ready inference module

---

## 📁 Project Structure

```
ml_research/
├── dataset_generator.py      # Labeled dataset generation
├── preprocessing.py           # Data cleaning & normalization
├── train_models.py           # Model training (RF + IF)
├── evaluate.py               # Comprehensive evaluation
├── realtime_predictor.py     # Real-time prediction module
├── run_pipeline.py           # Full pipeline orchestration
├── README.md                 # This file
│
├── api_telemetry_dataset.csv # Generated dataset (after step 1)
├── models/                   # Trained models & artifacts
│   ├── scaler.pkl
│   ├── random_forest.pkl
│   ├── isolation_forest.pkl
│   ├── X_train.npy
│   ├── X_test.npy
│   ├── y_train.npy
│   └── y_test.npy
│
└── evaluation_results/       # Evaluation outputs
    ├── rf_confusion_matrix.png
    ├── rf_roc_curve.png
    ├── rf_precision_recall.png
    ├── if_confusion_matrix.png
    ├── if_score_distribution.png
    └── model_comparison.csv
```

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install numpy pandas scikit-learn matplotlib seaborn joblib
```

### Option 1: Run Complete Pipeline (Recommended)

Execute the full pipeline in one command:

```bash
cd backend/ml_research
python run_pipeline.py
```

**Parameters:**
- `--duration`: Dataset duration in minutes (default: 120)
- `--interval`: Metric collection interval in seconds (default: 10)
- `--skip-dataset`: Skip dataset generation if already exists

Example:
```bash
python run_pipeline.py --duration 60 --interval 10
```

### Option 2: Run Steps Individually

#### Step 1: Generate Dataset
```bash
python dataset_generator.py
```
**Output:** `api_telemetry_dataset.csv` with labeled anomalies

#### Step 2: Preprocess Data
```bash
python preprocessing.py
```
**Output:** Normalized train/test splits in `models/` directory

#### Step 3: Train Models
```bash
python train_models.py
```
**Output:** Trained Random Forest and Isolation Forest models

#### Step 4: Evaluate Models
```bash
python evaluate.py
```
**Output:** Visualizations and metrics in `evaluation_results/`

#### Step 5: Real-Time Prediction
```bash
python realtime_predictor.py
```
**Output:** Demo of live prediction with sample metrics

---

## 📊 Dataset Specification

### Metrics Collected (Every 10 Seconds)

| Metric | Description | Range |
|--------|-------------|-------|
| `avg_response_time` | Average API response time (ms) | 0+ |
| `request_count` | Number of requests | 0+ |
| `error_rate` | Overall error rate | 0-1 |
| `five_xx_rate` | 5xx server error rate | 0-1 |
| `four_xx_rate` | 4xx client error rate | 0-1 |
| `payload_avg_size` | Average payload size (bytes) | 0+ |
| `unique_ip_count` | Unique IP addresses | 0+ |
| `cpu_usage` | CPU utilization (%) | 0-100 |
| `memory_usage` | Memory utilization (%) | 0-100 |

### Labels

- **0** = Normal
- **1** = Anomaly

### Anomaly Types (Randomized)

1. **Traffic Burst** - 10x request volume, moderate latency increase
2. **Latency Spike** - 3-10x response time, increased errors
3. **Error Spike** - 60-80% error rate, moderate latency
4. **Timeout** - >5000ms response time, >70% errors

### Randomization Features

- ✅ Random endpoint selection
- ✅ Random start time (200-600s gaps)
- ✅ Random duration (30-180 seconds)
- ✅ Random severity multiplier (3x-10x)
- ✅ Random anomaly type

---

## 🤖 Model Architecture

### 1. Random Forest Classifier (Supervised)
**Configuration:**
```python
RandomForestClassifier(
    n_estimators=200,
    class_weight='balanced',
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42
)
```

**Advantages:**
- High interpretability (feature importances)
- Robust to imbalanced classes
- Excellent precision and recall
- Handles non-linear relationships

### 2. Isolation Forest (Unsupervised)
**Configuration:**
```python
IsolationForest(
    contamination=0.03,
    n_estimators=200,
    random_state=42
)
```

**Advantages:**
- Detects unknown anomaly patterns
- No labeled data required for training
- Fast prediction
- Good for novelty detection

---

## 📈 Evaluation Metrics

### Classification Metrics (Random Forest)
- **Accuracy** - Overall correctness
- **Precision** - True positive rate among predicted positives
- **Recall** - True positive rate among actual positives
- **F1-Score** - Harmonic mean of precision and recall
- **ROC-AUC** - Area under ROC curve

### Visualizations
1. **Confusion Matrix** - True/false positives & negatives
2. **ROC Curve** - TPR vs FPR trade-off
3. **Precision-Recall Curve** - Precision vs recall trade-off
4. **Anomaly Score Distribution** - Score histograms by class

---

## 🔧 Real-Time Prediction API

### Usage Example

```python
from realtime_predictor import RealtimeAnomalyPredictor

# Initialize predictor
predictor = RealtimeAnomalyPredictor(
    models_dir='models',
    use_random_forest=True,
    use_isolation_forest=True
)

# Prepare live metrics
metrics = {
    'avg_response_time': 150.5,
    'request_count': 45,
    'error_rate': 0.02,
    'five_xx_rate': 0.01,
    'four_xx_rate': 0.01,
    'payload_avg_size': 2048.0,
    'unique_ip_count': 25,
    'cpu_usage': 35.0,
    'memory_usage': 45.0
}

# Get prediction
result = predictor.predict(metrics)

# Extract results
prediction = result['primary_prediction']
print(f"Label: {prediction['prediction_label']}")
print(f"Confidence: {prediction['confidence']:.4f}")
print(f"Anomaly Score: {prediction['anomaly_score']:.4f}")
```

### Response Format

```json
{
  "timestamp": "2026-02-15T10:30:00",
  "input_metrics": { ... },
  "predictions": {
    "random_forest": {
      "model": "Random Forest",
      "prediction": 0,
      "prediction_label": "Normal",
      "anomaly_score": 0.05,
      "confidence": 0.95
    },
    "isolation_forest": {
      "model": "Isolation Forest",
      "prediction": 0,
      "prediction_label": "Normal",
      "anomaly_score": 0.03,
      "confidence": 0.97
    }
  },
  "primary_prediction": { ... }
}
```

---

## 📚 Research Methodology

### Data Collection
- **Duration:** 2 hours (configurable)
- **Sampling Rate:** 10 seconds
- **Total Samples:** ~720 data points
- **Anomaly Rate:** ~15% (randomized)

### Data Preprocessing
1. **Null Removal** - Drop incomplete samples
2. **Feature Scaling** - StandardScaler (zero mean, unit variance)
3. **Train/Test Split** - 80/20 stratified split
4. **Shuffling** - Random shuffle with seed=42

### Model Training
- **Cross-Validation:** Stratified to maintain class balance
- **Hyperparameters:** Tuned for imbalanced datasets
- **Evaluation:** Held-out test set (no data leakage)

### Publication Standards
✅ Reproducible (random_state=42)  
✅ Proper train/test isolation  
✅ No data leakage (scaler fit on train only)  
✅ Comprehensive metrics reported  
✅ Visualizations at 300 DPI  
✅ Code documented with docstrings  

---

## 🎓 Academic Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{api_anomaly_ml_2026,
  title={Research-Grade ML Pipeline for API Anomaly Detection},
  author={Research Team},
  year={2026},
  version={1.0},
  description={Production-ready machine learning pipeline with randomized
               anomaly injection, proper train/test methodology, and
               comprehensive evaluation metrics}
}
```

---

## 🔬 Experimental Results (Expected)

Based on proper randomization and balanced training:

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC |
|-------|----------|-----------|--------|----------|---------|
| Random Forest | 0.92-0.96 | 0.88-0.94 | 0.85-0.92 | 0.86-0.93 | 0.94-0.98 |
| Isolation Forest | 0.85-0.91 | 0.75-0.85 | 0.78-0.88 | 0.76-0.86 | N/A |

*Results may vary based on random seed and anomaly distribution*

---

## 🛠️ Troubleshooting

### Issue: "Scaler not found"
**Solution:** Run preprocessing before prediction:
```bash
python preprocessing.py
```

### Issue: "Models not trained"
**Solution:** Run training pipeline:
```bash
python train_models.py
```

### Issue: "Low model performance"
**Solution:** 
1. Increase dataset duration: `--duration 240`
2. Adjust contamination parameter in `train_models.py`
3. Check anomaly injection randomization

---

## 📞 Support

For research collaboration or technical support:
- Review code comments and docstrings
- Check evaluation visualizations in `evaluation_results/`
- Verify data quality in `api_telemetry_dataset.csv`

---

## ✨ Future Enhancements

- [ ] LSTM/RNN for temporal anomaly detection
- [ ] AutoEncoder for unsupervised learning
- [ ] Real-time streaming prediction API
- [ ] Hyperparameter optimization (Grid/Random search)
- [ ] Multi-class anomaly classification
- [ ] Explainable AI (SHAP values)

---

**Built for Research. Ready for Production.**

*Last Updated: February 2026*
