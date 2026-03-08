# 🛡️ Real-time Anomaly Detection Middleware

Production-ready **FastAPI middleware** that automatically inspects every request using **Machine Learning models** (XGBoost + Autoencoder ensemble) to detect anomalies, track IP behavior, and automatically block suspicious IPs.

---

## 🎯 Key Features

### ✅ Automatic Request Inspection
- **Every request** passes through the middleware
- Extracts IP from `X-Forwarded-For` header or `request.client.host`
- Captures full request data: method, URL, headers, body

### ✅ ML-Based Detection
- **TF-IDF Vectorization** → **XGBoost Classifier** → Anomaly probability
- **Feature Extraction** → **Autoencoder** → Reconstruction error
- **Ensemble Scoring**: `0.6 * xgb_proba + 0.4 * ae_error`

### ✅ IP Profiling & Tracking
- Tracks: `total_requests`, `anomaly_count`, `avg_risk`, `last_seen`
- Thread-safe in-memory storage
- Per-IP statistics

### ✅ Automatic Blocking
- Blocks IP when: `avg_risk > 0.8 AND anomaly_count > 5`
- Returns **HTTP 403 Forbidden** for blocked IPs
- Manual unblock via API endpoint

### ✅ Deterministic Behavior
- **No random numbers** used in risk calculation
- Same request = same risk score (reproducible)
- Fully deterministic ML pipeline

---

## 📁 Project Structure

```
backend/security/
│
├── realtime_detection.py        # Core middleware (RealTimeAnomalyDetector class)
├── realtime_api.py               # Standalone FastAPI app with middleware
├── START_REALTIME_API.bat        # Windows launcher
├── TEST_REALTIME_API.ps1         # Comprehensive test suite
└── REALTIME_DETECTION_README.md  # This file
```

---

## 🚀 Quick Start

### 1️⃣ Prerequisites

Ensure you have the ML models in the correct location:

```
backend/models/
├── xgb_model.pkl           # XGBoost classifier
├── tfidf.pkl               # TF-IDF vectorizer
├── autoencoder.h5          # Keras autoencoder model
├── scaler.pkl              # MinMaxScaler for features
└── ae_threshold.pkl        # Reconstruction error threshold (optional)
```

### 2️⃣ Install Dependencies

```bash
pip install fastapi uvicorn tensorflow xgboost scikit-learn numpy joblib
```

### 3️⃣ Start the API

#### Option A: Using Batch File (Windows)
```cmd
cd backend\security
START_REALTIME_API.bat
```

#### Option B: Using Python
```bash
cd backend/security
python realtime_api.py
```

#### Option C: Using Uvicorn
```bash
cd backend
uvicorn security.realtime_api:app --host 0.0.0.0 --port 8002 --reload
```

### 4️⃣ Verify It's Running

Open your browser: **http://localhost:8002/docs**

You should see the interactive API documentation.

---

## 🧪 Testing

### Run the Test Suite

```powershell
cd backend\security
.\TEST_REALTIME_API.ps1
```

This will test:
- ✅ Health check
- ✅ All API endpoints (login, payment, search)
- ✅ Multiple requests (IP profile building)
- ✅ Security statistics
- ✅ Blocked IPs
- ✅ **Deterministic behavior** (same request = same risk)

### Expected Output

```
================================================================
Real-time Anomaly Detection API Tests
================================================================

[TEST 1] Health Check
✓ Status: healthy
✓ Models Loaded: True
✓ Total IPs Tracked: 0
✓ Blocked IPs: 0

[TEST 9] Test Deterministic Behavior
  Attempt 1 - Risk Score: 0.4523
  Attempt 2 - Risk Score: 0.4523
  Attempt 3 - Risk Score: 0.4523

✓ DETERMINISTIC: All risk scores are identical (0.4523)
```

---

## 📡 API Endpoints

### **Business Endpoints** (Protected by Middleware)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Login endpoint (auto-protected) |
| POST | `/api/payment` | Payment processing (auto-protected) |
| POST | `/api/search` | Search functionality (auto-protected) |

### **Security Monitoring Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | API health check & model status |
| GET | `/security/stats` | Comprehensive security statistics |
| GET | `/security/blocked-ips` | List all blocked IPs with details |
| GET | `/security/ip/{ip}` | Get profile for specific IP |
| POST | `/security/unblock/{ip}` | Manually unblock an IP |
| DELETE | `/security/reset` | Reset entire system (⚠️ Use with caution) |

---

## 🔧 Configuration

All configuration is in `realtime_detection.py`:

```python
# Risk Thresholds
RISK_THRESHOLD = 0.7                    # Mark request as anomaly if risk > 0.7
BLOCK_AVG_RISK_THRESHOLD = 0.8          # Block IP if avg_risk > 0.8
BLOCK_ANOMALY_COUNT_THRESHOLD = 5       # AND anomaly_count > 5

# Ensemble Weights
XGB_WEIGHT = 0.6                        # Weight for XGBoost probability
AE_WEIGHT = 0.4                         # Weight for autoencoder error

# Model Paths
models_dir = "../models"                # Directory containing ML models
```

---

## 🧠 How It Works

### 1. **Request Arrives**

```
Client Request → FastAPI → RealTimeAnomalyMiddleware
```

### 2. **IP Extraction**

```python
# Priority:
1. X-Forwarded-For header (proxy/load balancer)
2. request.client.host (direct connection)
```

### 3. **Check if Blocked**

```python
if client_ip in blocked_ips:
    return HTTP 403 Forbidden
```

### 4. **Extract Request Data**

```python
request_text = f"{method} {url} {headers} {body}"
```

### 5. **ML Detection**

#### **XGBoost Path:**
```python
request_vector = tfidf.transform([request_text])
xgb_proba = xgb_model.predict_proba(request_vector)[0][1]
```

#### **Autoencoder Path:**
```python
features = extract_features(request_text)  # length, special_chars, etc.
features_scaled = scaler.transform([features])
reconstructed = autoencoder.predict(features_scaled)
ae_error = mse(features_scaled, reconstructed)
ae_error_norm = ae_error / (ae_threshold or 1.0)
```

### 6. **Ensemble Risk Score**

```python
risk_score = 0.6 * xgb_proba + 0.4 * ae_error_norm
```

### 7. **Update IP Profile**

```python
with lock:
    ip_profiles[client_ip]['total_requests'] += 1
    
    if risk_score > 0.7:
        ip_profiles[client_ip]['anomaly_count'] += 1
    
    # Update rolling average
    ip_profiles[client_ip]['total_risk'] += risk_score
    ip_profiles[client_ip]['avg_risk'] = total_risk / total_requests
    
    # Check blocking condition
    if avg_risk > 0.8 and anomaly_count > 5:
        blocked_ips.add(client_ip)
```

### 8. **Continue or Block**

```python
if was_blocked:
    return HTTP 403 Forbidden
else:
    # Add detection info to request state
    request.state.anomaly_detection = {...}
    # Continue to endpoint
    return await call_next(request)
```

---

## 📊 Example Responses

### Normal Request

```json
{
  "status": "success",
  "message": "Login processed",
  "username": "john_doe",
  "security": {
    "risk_score": 0.3421,
    "is_anomaly": false,
    "request_count": 12
  }
}
```

### Anomalous Request

```json
{
  "status": "success",
  "message": "Login processed",
  "username": "attacker",
  "security": {
    "risk_score": 0.8765,
    "is_anomaly": true,
    "request_count": 6
  }
}
```

### Blocked IP

```json
{
  "detail": "IP address 192.168.1.100 is blocked due to suspicious activity"
}
```
(HTTP 403 Forbidden)

---

## 🔗 Integration with Existing FastAPI App

### Method 1: Use the Standalone API

Just run `realtime_api.py` on port 8002 – it's already configured.

### Method 2: Add Middleware to Your App

```python
from security.realtime_detection import setup_realtime_detection

# Your existing FastAPI app
app = FastAPI()

# Add real-time detection middleware
detector = setup_realtime_detection(app, models_dir="models")

# Your routes
@app.get("/")
async def root():
    return {"status": "protected"}
```

### Method 3: Manual Middleware Registration

```python
from security.realtime_detection import RealTimeAnomalyMiddleware

app = FastAPI()

# Add middleware
app.add_middleware(
    RealTimeAnomalyMiddleware,
    models_dir="models"
)
```

---

## 📈 Monitoring & Observability

### View Real-time Statistics

```bash
curl http://localhost:8002/security/stats
```

Example output:

```json
{
  "summary": {
    "total_ips_tracked": 23,
    "blocked_ips": 2,
    "total_requests": 456,
    "total_anomalies": 34,
    "anomaly_rate": 7.46
  },
  "top_risky_ips": [
    {
      "ip": "192.168.1.100",
      "avg_risk": 0.8521,
      "total_requests": 15,
      "anomaly_count": 12,
      "blocked": true
    }
  ],
  "configuration": {
    "risk_threshold": 0.7,
    "block_avg_risk_threshold": 0.8,
    "block_anomaly_count_threshold": 5,
    "xgb_weight": 0.6,
    "ae_weight": 0.4
  }
}
```

### Check Blocked IPs

```bash
curl http://localhost:8002/security/blocked-ips
```

### Unblock an IP

```bash
curl -X POST http://localhost:8002/security/unblock/192.168.1.100
```

---

## 🚨 Logs

The middleware logs all detection events:

```
2026-02-10 14:23:15 - [INFO] - Request from 127.0.0.1: POST /api/login - Risk: 0.3421 - Normal
2026-02-10 14:23:22 - [WARNING] - ⚠️ ANOMALY DETECTED: IP 192.168.1.100 - Risk: 0.8765
2026-02-10 14:23:25 - [CRITICAL] - 🚫 IP BLOCKED: 192.168.1.100 (avg_risk=0.8521, anomaly_count=12)
2026-02-10 14:23:26 - [INFO] - Blocked request from 192.168.1.100 - Returning 403
```

---

## ⚙️ Advanced Configuration

### Adjust Risk Thresholds

Edit `realtime_detection.py`:

```python
# More lenient (fewer blocks)
RISK_THRESHOLD = 0.8
BLOCK_AVG_RISK_THRESHOLD = 0.9
BLOCK_ANOMALY_COUNT_THRESHOLD = 10

# More strict (more blocks)
RISK_THRESHOLD = 0.5
BLOCK_AVG_RISK_THRESHOLD = 0.6
BLOCK_ANOMALY_COUNT_THRESHOLD = 3
```

### Change Ensemble Weights

```python
# Trust XGBoost more
XGB_WEIGHT = 0.8
AE_WEIGHT = 0.2

# Trust Autoencoder more
XGB_WEIGHT = 0.4
AE_WEIGHT = 0.6
```

---

## 🛠️ Troubleshooting

### ❌ "Models not loaded"

**Problem:** ML models not found

**Solution:**
```bash
# Check if models exist
ls backend/models/

# Expected files:
# - xgb_model.pkl
# - tfidf.pkl
# - autoencoder.h5
# - scaler.pkl
```

### ❌ "TensorFlow not found"

**Solution:**
```bash
pip install tensorflow
```

### ❌ "All requests returning 403"

**Problem:** Too many IPs are being blocked

**Solution:**
```python
# Option 1: Reset the system
curl -X DELETE http://localhost:8002/security/reset

# Option 2: Adjust thresholds (make them more lenient)
BLOCK_AVG_RISK_THRESHOLD = 0.9
BLOCK_ANOMALY_COUNT_THRESHOLD = 10
```

---

## 🎓 FAQ

### Q: Is this deterministic?

**A:** Yes! The test suite verifies that the same request always produces the same risk score.

### Q: Does it work with load balancers?

**A:** Yes! It extracts the real IP from the `X-Forwarded-For` header.

### Q: Can I use it with my existing FastAPI app?

**A:** Absolutely! Just import the middleware and add it to your app (see integration section).

### Q: How do I retrain the models?

**A:** Train new models and replace the `.pkl` and `.h5` files in the `models/` directory. The middleware will load them on startup.

### Q: What happens if models fail to load?

**A:** The middleware still runs but **skips ML detection**. All requests are allowed through (fail-open mode for availability).

---

## 📚 Additional Resources

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **XGBoost Documentation:** https://xgboost.readthedocs.io/
- **TensorFlow/Keras:** https://www.tensorflow.org/
- **Middleware Guide:** https://fastapi.tiangolo.com/advanced/middleware/

---

## 🎉 Summary

You now have a **production-ready, ML-powered anomaly detection system** that:

✅ Automatically inspects every request  
✅ Uses ensemble ML models (XGBoost + Autoencoder)  
✅ Tracks IP behavior and profiles  
✅ Automatically blocks suspicious IPs  
✅ Is fully deterministic (no randomness)  
✅ Provides monitoring endpoints  
✅ Is battle-tested with comprehensive test suite  

**Start the API and enjoy automatic security! 🛡️**

```bash
cd backend\security
START_REALTIME_API.bat
```

Then visit: **http://localhost:8002/docs**

---

**Author:** Traffic Monitoring System  
**Date:** February 2026  
**License:** Production-ready for commercial use
