# IP Risk Engine - Quick Start Guide

Production-ready FastAPI application for IP risk tracking and automated blocking.

## 🚀 Quick Start

### 1️⃣ Start the Server

**Option A: Using the batch file**
```bash
cd backend/security
START_RISK_ENGINE.bat
```

**Option B: Manual start**
```bash
cd backend
python -m uvicorn security.risk_engine:app --host 0.0.0.0 --port 8000 --reload
```

### 2️⃣ Access the API

- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

### 3️⃣ Test the API

**Option A: Using the test script**
```bash
cd backend/security
python test_api.py
```

**Option B: Using curl**
```bash
# Health check
curl http://localhost:8000/health

# Analyze request (simulated risk)
curl -X POST http://localhost:8000/api \
  -H "X-Forwarded-For: 192.168.1.100"

# Get suspicious IPs
curl http://localhost:8000/suspicious-ips
```

**Option C: Using the interactive docs**
1. Go to http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Click "Execute"

---

## 📚 API Endpoints

### Core Endpoints

#### `POST /api` - Risk Analysis
Analyze request and update IP risk score.

**Request:**
```bash
curl -X POST http://localhost:8000/api \
  -H "X-Forwarded-For: 192.168.1.100"
```

**Response (200 OK):**
```json
{
  "ip": "192.168.1.100",
  "risk_score": 0.4523,
  "blocked_status": false,
  "request_count": 3,
  "average_risk": 0.4125,
  "timestamp": "2026-02-23T14:30:00.123456"
}
```

**Response (403 Blocked):**
```json
{
  "error": "IP blocked",
  "message": "Your IP has been blocked due to suspicious activity",
  "ip": "192.168.1.100"
}
```

#### `GET /suspicious-ips` - Get All Tracked IPs
Retrieve complete tracking data.

**Response:**
```json
{
  "total_ips_tracked": 5,
  "blocked_ips_count": 1,
  "tracking_data": {
    "192.168.1.100": {
      "total_risk": 4.5,
      "request_count": 10,
      "average_risk": 0.45,
      "last_seen": "2026-02-23T14:30:00.123456",
      "blocked": false
    },
    "10.0.0.50": {
      "total_risk": 4.8,
      "request_count": 5,
      "average_risk": 0.96,
      "last_seen": "2026-02-23T14:29:00.123456",
      "blocked": true
    }
  }
}
```

### Admin Endpoints

#### `GET /admin/blocked-ips` - Get Blocked IPs
```bash
curl http://localhost:8000/admin/blocked-ips
```

#### `POST /admin/unblock/{ip}` - Unblock IP
```bash
curl -X POST http://localhost:8000/admin/unblock/192.168.1.100
```

#### `GET /admin/ip/{ip}` - Get IP Details
```bash
curl http://localhost:8000/admin/ip/192.168.1.100
```

#### `DELETE /admin/reset-all` - Reset All Data
```bash
curl -X DELETE http://localhost:8000/admin/reset-all
```

---

## 🔧 How It Works

### Middleware Pipeline

```
Request
  ↓
[IPExtractionMiddleware]
  ├─ Checks X-Forwarded-For header
  ├─ Checks X-Real-IP header
  ├─ Falls back to request.client.host
  └─ Stores IP in request.state.client_ip
  ↓
[Route Handler: POST /api]
  ├─ Gets IP from request.state.client_ip
  ├─ Checks if IP is blocked
  ├─ Calculates risk score (currently random, replace with ML)
  ├─ Calls update_ip_risk(ip, risk)
  └─ Returns analysis result
  ↓
Response
```

### Automatic Blocking

An IP is **automatically blocked** when:
- ✅ Average risk > **0.8**
- ✅ Request count >= **5**

Example:
```
Request 1: risk=0.9 → avg=0.9, count=1 → NOT BLOCKED (count < 5)
Request 2: risk=0.9 → avg=0.9, count=2 → NOT BLOCKED
Request 3: risk=0.9 → avg=0.9, count=3 → NOT BLOCKED
Request 4: risk=0.9 → avg=0.9, count=4 → NOT BLOCKED
Request 5: risk=0.9 → avg=0.9, count=5 → ⚠️ BLOCKED!
```

---

## 🧪 Testing Scenarios

### Scenario 1: Normal Traffic
```python
import requests

# Send 10 low-risk requests
for i in range(10):
    response = requests.post(
        "http://localhost:8000/api",
        headers={"X-Forwarded-For": "192.168.1.100"}
    )
    print(f"Request {i+1}: {response.json()}")
```

### Scenario 2: Multiple IPs
```python
ips = ["10.0.0.1", "10.0.0.2", "10.0.0.3"]

for ip in ips:
    response = requests.post(
        "http://localhost:8000/api",
        headers={"X-Forwarded-For": ip}
    )
    print(f"IP {ip}: {response.json()}")
```

### Scenario 3: Check Tracking Data
```python
response = requests.get("http://localhost:8000/suspicious-ips")
data = response.json()

print(f"Tracking {data['total_ips_tracked']} IPs")
print(f"Blocked: {data['blocked_ips_count']}")

for ip, stats in data['tracking_data'].items():
    print(f"{ip}: avg_risk={stats['average_risk']:.2f}, blocked={stats['blocked']}")
```

---

## 🔌 Integration with ML Models

Currently, the risk score is simulated with `random.uniform(0, 1)`. Replace this with your ML models:

### In `risk_engine.py`, find this section:

```python
# Line ~150 in POST /api endpoint
# Step 3: Simulate risk scoring
# TODO: Replace with actual ML model inference
risk_score = random.uniform(0, 1)
```

### Replace with:

```python
import joblib
from tensorflow import keras

# Load models (do this at startup, not per request)
xgb_model = joblib.load('../models/xgb_model.pkl')
tfidf = joblib.load('../models/tfidf.pkl')
autoencoder = keras.models.load_model('../models/autoencoder.h5')

# In the endpoint:
async def analyze_request(request: Request):
    # ... existing code ...
    
    # Extract features from request
    request_data = await request.json()  # or however you get data
    features = extract_features(request_data)
    
    # XGBoost prediction
    xgb_score = xgb_model.predict_proba(features)[0][1]
    
    # TF-IDF text analysis (if applicable)
    text_features = tfidf.transform([request_data.get('text', '')])
    text_score = analyze_text_anomaly(text_features)
    
    # Autoencoder reconstruction error
    ae_reconstruction = autoencoder.predict(features)
    ae_score = calculate_reconstruction_error(features, ae_reconstruction)
    
    # Combine scores (weighted average)
    risk_score = (xgb_score * 0.5 + text_score * 0.3 + ae_score * 0.2)
    
    # Rest of the code remains the same
    was_blocked = update_ip_risk(client_ip, risk_score)
    # ...
```

---

## 📊 Monitoring Dashboard Integration

Add these endpoints to your existing dashboard:

```javascript
// React example
const fetchIPStats = async () => {
  const response = await fetch('http://localhost:8000/suspicious-ips');
  const data = await response.json();
  
  // Display in your dashboard
  setTotalIPs(data.total_ips_tracked);
  setBlockedIPs(data.blocked_ips_count);
  setTrackingData(data.tracking_data);
};
```

---

## 🛡️ Production Deployment

### Security Checklist

- [ ] Add authentication to admin endpoints
- [ ] Configure CORS for specific origins
- [ ] Enable HTTPS/TLS
- [ ] Set up rate limiting
- [ ] Add request logging
- [ ] Configure firewall rules
- [ ] Set up monitoring/alerting
- [ ] Review and adjust blocking thresholds

### Configuration Changes

```python
# In risk_engine.py

# CORS - restrict to your domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # ← Change this
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Blocking thresholds - adjust in ip_manager.py
class IPRiskManager:
    BLOCK_THRESHOLD_AVG_RISK = 0.8      # Increase for less aggressive blocking
    BLOCK_THRESHOLD_REQUEST_COUNT = 5    # Increase to require more requests
```

---

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Try a different port
uvicorn security.risk_engine:app --port 8001
```

### IP not being extracted
- Check middleware order (IPExtractionMiddleware must be first)
- Verify X-Forwarded-For header is being sent
- Check logs for IP extraction messages

### IPs not getting blocked
- Risk scores may be too low (they're random in this version)
- Increase request count to trigger blocking
- Check blocking thresholds in `ip_manager.py`

---

## 📁 File Structure

```
security/
├── __init__.py              # Package exports
├── ip_manager.py            # Core IP tracking logic
├── middleware.py            # FastAPI middleware
├── risk_engine.py           # Main FastAPI application ⭐
├── test_api.py              # Automated tests
├── START_RISK_ENGINE.bat    # Startup script
├── QUICK_START.md           # This file
└── README.md                # Module documentation
```

---

## ✅ Next Steps

1. **Start the server:** Run `START_RISK_ENGINE.bat`
2. **Test it:** Run `python test_api.py`
3. **Explore API:** Visit http://localhost:8000/docs
4. **Integrate ML:** Replace `random.uniform()` with your models
5. **Deploy:** Follow production deployment checklist

---

**Need Help?**
- View interactive docs: http://localhost:8000/docs
- Check logs for detailed error messages
- Review the main README.md for architecture details

🚀 **You're all set!** The IP Risk Engine is production-ready and waiting for your ML models.
