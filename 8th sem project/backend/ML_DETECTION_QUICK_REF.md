# ML ANOMALY DETECTION - QUICK REFERENCE

## Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install -r requirements_ml_detection.txt
```

### 2. Basic Usage
```python
from ml_anomaly_detection import MLAnomalyDetector
import numpy as np

# Initialize and load models
detector = MLAnomalyDetector()
detector.load_models()

# Predict network anomaly
data = np.random.randn(1, 10)  # Your network features
result = detector.predict_anomaly(data, protocol='network')

print(f"Anomaly: {result['is_anomaly']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### 3. IP Blocking
```python
# Check and block suspicious IP
blocking = detector.check_and_block_ip(
    ip='192.168.1.100',
    prediction=result,
    threshold=0.7
)
print(f"Blocked: {blocking['should_block']}")
```

## Key Functions

### Load Models
```python
detector = MLAnomalyDetector()
detector.load_models()
```

### Predict Anomaly
```python
# Network traffic
result = detector.predict_anomaly(data, protocol='network')

# HTTP request
result = detector.predict_anomaly(data, protocol='http')
```

### IP Management
```python
# Block IP based on prediction
blocking = detector.check_and_block_ip(ip, prediction, threshold=0.7)

# Check if blocked
is_blocked = detector.is_ip_blocked('192.168.1.100')

# Unblock IP
detector.unblock_ip('192.168.1.100')

# Get all blocked IPs
blocked_list = detector.get_blocked_ips()
```

### Calculate Metrics
```python
# Error rate
error_rate = detector.calculate_error_rate(y_true, y_pred)

# Failure probability
failure_prob = detector.calculate_failure_probability(y_pred)
```

### Get Statistics
```python
stats = detector.get_statistics()
print(f"Total predictions: {stats['total_predictions']}")
print(f"Blocked IPs: {stats['blocked_ips_count']}")
print(f"Anomaly rate: {stats['anomaly_rate']:.2%}")
```

## Return Values

### predict_anomaly() Returns:
```python
{
    'is_anomaly': bool,              # True if anomalous
    'confidence': float,              # 0.0 to 1.0
    'ensemble_prediction': int,       # 0 or 1
    'individual_predictions': dict,   # Per-model predictions
    'num_models_voted': int,          # Number of models
    'error_rate': float,              # Calculated error rate
    'failure_probability': float,     # Failure probability
    'protocol': str                   # 'network' or 'http'
}
```

### check_and_block_ip() Returns:
```python
{
    'ip': str,                  # IP address
    'should_block': bool,       # Blocking recommendation
    'is_blocked': bool,         # Current blocked status
    'reason': str,              # Reason for decision
    'action_taken': str,        # Action description
    'confidence': float,        # Prediction confidence
    'prediction': dict          # Full prediction result
}
```

## Model Structure Required

```
backend/models/
├── CIC-IDS/
│   ├── LightGBM_BAG_L1/model.pkl
│   ├── LightGBMXT_BAG_L1/model.pkl
│   ├── CatBoost_BAG_L2/model.pkl
│   ├── RandomForestGini_BAG_L1/model.pkl
│   ├── RandomForestEntr_BAG_L1/model.pkl
│   └── ExtraTreesGini_BAG_L1/model.pkl
└── CSIC/
    ├── xgboost_model.pkl
    └── autoencoder_model.pt
```

## Integration with Existing System

```python
from ml_integration_example import EnhancedAnomalyDetectionSystem

# Initialize
system = EnhancedAnomalyDetectionSystem()

# Process request
result = system.process_request(
    ip='192.168.1.100',
    features={'packet_count': 1500, ...},
    protocol='network',
    block_threshold=0.7
)

# Check result
if result['detection']['combined_decision']:
    print(f"ANOMALY DETECTED!")
    print(f"Confidence: {result['detection']['confidence']:.2%}")
    if result['blocking']:
        print(f"IP blocked: {result['blocking']['is_blocked']}")
```

## Testing

```bash
# Test ML anomaly detection
python ml_anomaly_detection.py

# Test autoencoder
python autoencoder_wrapper.py

# Test integration
python ml_integration_example.py
```

## Common Issues

### Issue: Models not found
**Solution:** Check models directory path
```python
detector = MLAnomalyDetector(models_dir='path/to/models')
```

### Issue: Feature dimension mismatch
**Solution:** Ensure correct number of features
```python
# For single sample with 10 features
data = np.array([...]).reshape(1, 10)
```

### Issue: XGBoost/Autoencoder not loaded
**Solution:** Export from notebooks
```python
# In notebook
import joblib
joblib.dump(model, 'xgboost_model.pkl')
```

## Performance Tips

1. **Load models once:** Initialize detector at startup
2. **Batch predictions:** Process multiple samples together
3. **Cache results:** Store predictions for identical inputs
4. **Selective loading:** Load only needed models

## Next Steps

1. ✓ Install dependencies
2. ✓ Load and test models
3. ✓ Integrate with your system
4. ✓ Monitor statistics
5. ✓ Tune blocking threshold
6. ✓ Export CSIC models from notebooks (if needed)

## Files Reference

- `ml_anomaly_detection.py` - Main module
- `autoencoder_wrapper.py` - Autoencoder utilities
- `ml_integration_example.py` - Integration examples
- `ML_ANOMALY_DETECTION_README.md` - Full documentation
- `requirements_ml_detection.txt` - Dependencies

## Support

For detailed documentation, see `ML_ANOMALY_DETECTION_README.md`

For examples, run: `python ml_integration_example.py`
