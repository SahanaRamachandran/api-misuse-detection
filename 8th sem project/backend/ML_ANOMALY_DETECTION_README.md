# ML Anomaly Detection Integration

## Overview

This module integrates multiple machine learning models for comprehensive anomaly detection in network traffic and HTTP requests.

## Features

### 1. Multi-Model Ensemble
- **CIC IDS 2017 Models** (Network Traffic):
  - LightGBM
  - LightGBMXT
  - CatBoost
  - RandomForest (Gini)
  - RandomForest (Entropy)
  - ExtraTrees (Gini)

- **CSIC 2010 Models** (HTTP Requests):
  - XGBoost
  - Autoencoder (PyTorch)

### 2. Ensemble Prediction
- Majority voting for network traffic models
- Combined XGBoost + Autoencoder for HTTP requests
- Confidence scoring based on model agreement

### 3. Advanced Metrics
- Error rate calculation
- Failure probability estimation
- Real-time risk assessment

### 4. IP Management
- Automatic IP blocking based on anomaly confidence
- Blocked IP tracking
- Prediction history for each IP

## Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements_ml_detection.txt
```

Or install individually:

```bash
pip install numpy pandas scikit-learn joblib torch
pip install lightgbm catboost xgboost
pip install autogluon.tabular
```

### Step 2: Verify Models

Ensure your models are organized in the following structure:

```
backend/models/
├── CIC-IDS/
│   ├── LightGBM_BAG_L1/
│   │   └── model.pkl
│   ├── LightGBMXT_BAG_L1/
│   │   └── model.pkl
│   ├── CatBoost_BAG_L2/
│   │   └── model.pkl
│   ├── RandomForestGini_BAG_L1/
│   │   └── model.pkl
│   ├── RandomForestEntr_BAG_L1/
│   │   └── model.pkl
│   └── ExtraTreesGini_BAG_L1/
│       └── model.pkl
└── CSIC/
    ├── xgboost_model.pkl
    └── autoencoder_model.pt
```

## Usage

### Basic Usage

```python
from ml_anomaly_detection import MLAnomalyDetector
import numpy as np

# Initialize detector
detector = MLAnomalyDetector()

# Load models
detector.load_models()

# Prepare input data (example with 10 features)
network_data = np.random.randn(1, 10)

# Predict network traffic anomaly
result = detector.predict_anomaly(network_data, protocol='network')

print(f"Anomaly: {result['is_anomaly']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Models voted: {result['num_models_voted']}")
```

### HTTP Request Detection

```python
# HTTP request features
http_data = np.array([[512, 15, 120, 3, 1, 0, 0, 3.5, 0, 512]])

# Predict HTTP anomaly
result = detector.predict_anomaly(http_data, protocol='http')

print(f"Anomaly: {result['is_anomaly']}")
print(f"Confidence: {result['confidence']:.2%}")
```

### IP Blocking

```python
# Check if IP should be blocked
ip_address = '192.168.1.100'
blocking_result = detector.check_and_block_ip(
    ip=ip_address,
    prediction=result,
    threshold=0.7
)

print(f"Should block: {blocking_result['should_block']}")
print(f"Reason: {blocking_result['reason']}")
print(f"Action: {blocking_result['action_taken']}")

# Check if IP is blocked
if detector.is_ip_blocked(ip_address):
    print(f"{ip_address} is blocked")

# Unblock IP
detector.unblock_ip(ip_address)
```

### Integration with Existing System

```python
from ml_integration_example import EnhancedAnomalyDetectionSystem

# Initialize enhanced system
system = EnhancedAnomalyDetectionSystem()

# Process network request
network_features = {
    'packet_count': 1500,
    'byte_count': 150000,
    'duration': 60,
    'avg_packet_size': 100,
    'flow_rate': 25,
    'protocol_type': 6,
    'src_port': 45678,
    'dst_port': 80,
    'flags': 2,
    'connection_state': 1
}

result = system.process_request(
    ip='192.168.1.100',
    features=network_features,
    protocol='network'
)

print(f"Anomaly: {result['detection']['combined_decision']}")
print(f"Confidence: {result['detection']['confidence']:.2%}")
```

### Standalone Functions

```python
from ml_anomaly_detection import (
    load_models,
    predict_anomaly,
    calculate_error_rate,
    calculate_failure_probability
)

# Load models
detector = load_models()

# Make prediction
data = np.random.randn(1, 10)
result = predict_anomaly(detector, data, protocol='network')

# Calculate error rate
y_true = np.array([0, 0, 1, 1, 0])
y_pred = np.array([0, 1, 1, 0, 0])
error_rate = calculate_error_rate(y_true, y_pred)
print(f"Error rate: {error_rate:.2%}")

# Calculate failure probability
y_pred_window = np.array([0, 0, 1, 1, 1, 0, 1, 1, 0, 1])
failure_prob = calculate_failure_probability(y_pred_window)
print(f"Failure probability: {failure_prob:.2%}")
```

## API Reference

### MLAnomalyDetector Class

#### Methods

##### `__init__(models_dir=None)`
Initialize the detector.

**Parameters:**
- `models_dir` (str, optional): Path to models directory. Defaults to 'backend/models'.

##### `load_models() -> bool`
Load all ML models from disk.

**Returns:**
- `bool`: True if models loaded successfully, False otherwise.

##### `predict_anomaly(data, protocol='network') -> Dict`
Predict anomaly for input data.

**Parameters:**
- `data` (np.ndarray, pd.DataFrame, or Dict): Input features
- `protocol` (str): 'network' or 'http'

**Returns:**
- Dictionary containing:
  - `is_anomaly` (bool): Whether input is anomalous
  - `confidence` (float): Prediction confidence (0-1)
  - `ensemble_prediction` (int): 0 (normal) or 1 (anomaly)
  - `individual_predictions` (dict): Predictions from each model
  - `num_models_voted` (int): Number of models that made predictions
  - `error_rate` (float): Calculated error rate
  - `failure_probability` (float): Failure probability
  - `protocol` (str): Protocol used

##### `check_and_block_ip(ip, prediction, threshold=0.7) -> Dict`
Check if IP should be blocked based on prediction.

**Parameters:**
- `ip` (str): IP address
- `prediction` (Dict): Result from `predict_anomaly()`
- `threshold` (float): Confidence threshold for blocking

**Returns:**
- Dictionary containing blocking decision and details.

##### `is_ip_blocked(ip) -> bool`
Check if an IP is in the blocklist.

##### `unblock_ip(ip) -> bool`
Remove an IP from the blocklist.

##### `get_blocked_ips() -> List[str]`
Get list of all blocked IPs.

##### `get_statistics() -> Dict`
Get overall statistics about the detector.

## Autoencoder Usage

### Training a New Autoencoder

```python
from autoencoder_wrapper import train_autoencoder
import numpy as np

# Generate or load training data (normal samples only)
X_train = np.random.randn(1000, 10)
X_val = np.random.randn(200, 10)

# Train autoencoder
detector = train_autoencoder(
    X_train=X_train,
    X_val=X_val,
    epochs=50,
    batch_size=32,
    learning_rate=0.001,
    encoding_dim=5
)

# Save model
detector.save_model('models/CSIC/autoencoder_model.pt')
```

### Loading Existing Autoencoder

```python
from autoencoder_wrapper import create_autoencoder_detector

# Load autoencoder
detector = create_autoencoder_detector(
    model_path='models/CSIC/autoencoder_model.pt',
    input_dim=10,
    encoding_dim=5
)

# Make predictions
X_test = np.random.randn(100, 10)
predictions = detector.predict(X_test)
print(f"Anomalies detected: {predictions.sum()}/{len(predictions)}")
```

## Testing

### Run Unit Tests

```python
# Test ML anomaly detection
python ml_anomaly_detection.py

# Test autoencoder
python autoencoder_wrapper.py

# Test integration
python ml_integration_example.py
```

### Expected Output

When models are loaded successfully:
```
============================================================
LOADING CIC IDS 2017 MODELS (Network Traffic)
============================================================
✓ Loaded: LightGBM_BAG_L1
✓ Loaded: LightGBMXT_BAG_L1
✓ Loaded: CatBoost_BAG_L2
✓ Loaded: RandomForestGini_BAG_L1
✓ Loaded: RandomForestEntr_BAG_L1
✓ Loaded: ExtraTreesGini_BAG_L1

============================================================
LOADING CSIC 2010 HTTP MODELS
============================================================
✓ Loaded: XGBoost
ℹ Autoencoder found but loader not implemented yet

============================================================
SUMMARY: 6 CIC models, 1 CSIC models loaded
============================================================
```

## Troubleshooting

### Models Not Found

If you see "CIC-IDS models directory not found":
1. Verify the `models/CIC-IDS/` directory exists
2. Check that model.pkl files are in the correct subdirectories
3. Set the correct path: `detector = MLAnomalyDetector(models_dir='path/to/models')`

### XGBoost/Autoencoder Not Found

The CSIC models may be in Jupyter notebook format:
1. Open the notebooks in `models/CSIC/`
2. Export trained models using `joblib.dump()` for XGBoost
3. Export using `torch.save()` for Autoencoder

Example export code:
```python
# In XgBoost.ipynb
import joblib
joblib.dump(xgb_model, 'xgboost_model.pkl')

# In Autoencoder.ipynb
import torch
torch.save(autoencoder_model.state_dict(), 'autoencoder_model.pt')
```

### Feature Dimension Mismatch

Ensure input data has the same number of features as training data:
- CIC IDS models expect specific features (check model training logs)
- Reshape single samples: `data.reshape(1, -1)`
- Use consistent feature ordering

## Performance Considerations

### Memory Usage
- Each model consumes memory when loaded
- Consider loading only required models for your use case
- Use `del detector` to free memory when done

### Prediction Speed
- Ensemble of 6+ models takes ~10-50ms per prediction
- Use batch predictions for multiple samples
- Consider caching predictions for identical inputs

### Scaling
- For high-throughput scenarios, consider:
  - Model serving platforms (TensorFlow Serving, TorchServe)
  - Async prediction queues
  - Model quantization for faster inference

## Integration with Web Framework

### Flask Example

```python
from flask import Flask, request, jsonify
from ml_anomaly_detection import load_models

app = Flask(__name__)
detector = load_models()

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    features = np.array(data['features']).reshape(1, -1)
    result = detector.predict_anomaly(features, protocol='network')
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=False)
```

### FastAPI Example

```python
from fastapi import FastAPI
from pydantic import BaseModel
from ml_anomaly_detection import load_models
import numpy as np

app = FastAPI()
detector = load_models()

class PredictionRequest(BaseModel):
    features: list
    protocol: str = 'network'

@app.post('/predict')
async def predict(request: PredictionRequest):
    features = np.array(request.features).reshape(1, -1)
    result = detector.predict_anomaly(features, protocol=request.protocol)
    return result
```

## Contributing

When adding new models:
1. Save models in appropriate directory (CIC-IDS or CSIC)
2. Update model name lists in `ml_anomaly_detection.py`
3. Ensure models have `.predict()` method
4. Update documentation

## License

This module is part of the Traffic Monitoring System project.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review example code in `ml_integration_example.py`
3. Test with `python ml_anomaly_detection.py`

## Version History

- **v1.0.0** (2026-02-23): Initial release
  - CIC IDS 2017 integration
  - CSIC 2010 HTTP models
  - Ensemble prediction
  - IP blocking
  - Comprehensive documentation
