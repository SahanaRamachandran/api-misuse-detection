# ✅ Real-time Anomaly Detection - Setup Checklist

Use this checklist to verify your real-time anomaly detection system is properly set up.

---

## 📋 Pre-Flight Checklist

### 1. ✅ Files Created

Check that all these files exist in `backend/security/`:

- [ ] `realtime_detection.py` (Core middleware - 500+ lines)
- [ ] `realtime_api.py` (Standalone FastAPI app)
- [ ] `START_REALTIME_API.bat` (Windows launcher)
- [ ] `QUICK_START_REALTIME.ps1` (Interactive setup)
- [ ] `TEST_REALTIME_API.ps1` (Test suite)
- [ ] `REALTIME_DETECTION_README.md` (User guide)
- [ ] `APP_INTEGRATION_EXAMPLE.py` (Integration examples)
- [ ] `REALTIME_DETECTION_SUMMARY.md` (Project summary)
- [ ] `SETUP_CHECKLIST.md` (This file)

**Verify:**
```powershell
cd backend\security
dir *.py, *.bat, *.ps1, *.md
```

---

### 2. ✅ ML Models

Check that models exist in `backend/models/`:

- [ ] `xgb_model.pkl` (XGBoost classifier)
- [ ] `tfidf.pkl` (TF-IDF vectorizer)
- [ ] `autoencoder.h5` (Keras autoencoder)
- [ ] `scaler.pkl` (MinMaxScaler)
- [ ] `ae_threshold.pkl` (Optional - reconstruction threshold)

**Verify:**
```powershell
cd backend\models
dir *.pkl, *.h5
```

**If models are missing:**
- ⚠️ System will run in "fail-open" mode (no ML detection)
- ⚠️ All requests will be allowed through
- ℹ️ You need to train models or obtain pre-trained ones

---

### 3. ✅ Python Dependencies

Check that all required packages are installed:

- [ ] `fastapi` (Web framework)
- [ ] `uvicorn` (ASGI server)
- [ ] `tensorflow` or `keras` (Autoencoder)
- [ ] `xgboost` (XGBoost classifier)
- [ ] `scikit-learn` (TF-IDF, Scaler)
- [ ] `numpy` (Array operations)
- [ ] `joblib` (Model loading)

**Verify:**
```powershell
python -c "import fastapi, uvicorn, tensorflow, xgboost, sklearn, numpy, joblib; print('✓ All packages installed')"
```

**If packages are missing:**
```powershell
pip install fastapi uvicorn tensorflow xgboost scikit-learn numpy joblib
```

---

## 🚀 Startup Checklist

### 1. ✅ Start the API

**Option A: Interactive Setup**
```powershell
cd backend\security
.\QUICK_START_REALTIME.ps1
```

**Option B: Batch File**
```powershell
cd backend\security
.\START_REALTIME_API.bat
```

**Option C: Manual**
```powershell
cd backend
python -m uvicorn security.realtime_api:app --host 0.0.0.0 --port 8002 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8002
INFO:     Application startup complete.
✅ Real-time anomaly detection middleware enabled
🛡️ Detection Active: True
```

---

### 2. ✅ Verify API is Running

**Open in browser:**
- [ ] http://localhost:8002 (Root endpoint)
- [ ] http://localhost:8002/docs (Interactive docs)
- [ ] http://localhost:8002/health (Health check)

**Expected response from `/health`:**
```json
{
  "status": "healthy",
  "models_loaded": true,
  "statistics": {
    "total_ips_tracked": 0,
    "blocked_ips": 0,
    "active_ips": 0
  }
}
```

---

## 🧪 Testing Checklist

### 1. ✅ Run Test Suite

```powershell
cd backend\security
.\TEST_REALTIME_API.ps1
```

**Expected Results:**
- [ ] Test 1: Health Check - ✓ PASSED
- [ ] Test 2: Root Endpoint - ✓ PASSED
- [ ] Test 3: Login Endpoint - ✓ PASSED
- [ ] Test 4: Payment Endpoint - ✓ PASSED
- [ ] Test 5: Search Endpoint - ✓ PASSED
- [ ] Test 6: Multiple Requests - ✓ PASSED
- [ ] Test 7: Security Statistics - ✓ PASSED
- [ ] Test 8: Blocked IPs - ✓ PASSED
- [ ] Test 9: Deterministic Behavior - ✓ PASSED

---

### 2. ✅ Manual Testing

**Test 1: Send a request**
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/api/login" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"username":"test","password":"test123"}'
```

**Expected:**
```json
{
  "status": "success",
  "message": "Login processed",
  "security": {
    "risk_score": 0.4523,
    "is_anomaly": false,
    "request_count": 1
  }
}
```

---

**Test 2: Check security stats**
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/security/stats" -Method Get
```

**Expected:**
```json
{
  "summary": {
    "total_ips_tracked": 1,
    "blocked_ips": 0,
    "total_requests": 1,
    "total_anomalies": 0
  }
}
```

---

**Test 3: Verify deterministic behavior**

Send the same request 3 times and verify the risk score is identical:

```powershell
# Request 1
$r1 = Invoke-RestMethod -Uri "http://localhost:8002/api/login" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"username":"deterministic","password":"test"}'

# Request 2
$r2 = Invoke-RestMethod -Uri "http://localhost:8002/api/login" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"username":"deterministic","password":"test"}'

# Request 3
$r3 = Invoke-RestMethod -Uri "http://localhost:8002/api/login" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"username":"deterministic","password":"test"}'

# Compare
Write-Host "Risk 1: $($r1.security.risk_score)"
Write-Host "Risk 2: $($r2.security.risk_score)"
Write-Host "Risk 3: $($r3.security.risk_score)"
```

**Expected:**
```
Risk 1: 0.4523
Risk 2: 0.4523
Risk 3: 0.4523
```

✅ All three should be **identical** (deterministic)

---

## 🔗 Integration Checklist

### Option 1: Use Standalone API

- [ ] API running on port 8002
- [ ] Frontend connects to `http://localhost:8002`
- [ ] All endpoints accessible

**No integration needed!** The standalone API is ready to use.

---

### Option 2: Integrate with Main App

**1. Modify `backend/app.py`:**

Add these two lines:
```python
from security.realtime_detection import setup_realtime_detection

# After creating app:
detector = setup_realtime_detection(app, models_dir="models")
```

**Full example:**
```python
from fastapi import FastAPI
from security.realtime_detection import setup_realtime_detection

app = FastAPI()

# Add middleware
detector = setup_realtime_detection(app, models_dir="models")

# Your routes
@app.get("/")
async def root():
    return {"status": "protected"}
```

**2. Restart main backend:**
```powershell
cd backend
python app.py
```

**3. Verify middleware is active:**

Check logs for:
```
✅ Real-time anomaly detection middleware enabled
🛡️ Detection Active: True
```

**4. Test protection:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/traffic" -Method Get
```

Should see detection info in logs.

---

## 📊 Monitoring Checklist

### 1. ✅ Check Logs

**Look for these log messages:**

**Normal request:**
```
[INFO] - Request from 127.0.0.1: POST /api/login - Risk: 0.3421 - Normal
```

**Anomaly detected:**
```
[WARNING] - ⚠️ ANOMALY DETECTED: IP 192.168.1.100 - Risk: 0.8765
```

**IP blocked:**
```
[CRITICAL] - 🚫 IP BLOCKED: 192.168.1.100 (avg_risk=0.8521, anomaly_count=12)
```

**Blocked request:**
```
[INFO] - Blocked request from 192.168.1.100 - Returning 403
```

---

### 2. ✅ Monitor Endpoints

**Security Statistics:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/security/stats" -Method Get
```

**Blocked IPs:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/security/blocked-ips" -Method Get
```

**Specific IP Profile:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8002/security/ip/127.0.0.1" -Method Get
```

---

## ⚙️ Configuration Checklist

### 1. ✅ Verify Configuration

Open `backend/security/realtime_detection.py` and check:

```python
# Risk Thresholds
RISK_THRESHOLD = 0.7                    # ← Mark as anomaly if > 0.7
BLOCK_AVG_RISK_THRESHOLD = 0.8          # ← Block if avg_risk > 0.8
BLOCK_ANOMALY_COUNT_THRESHOLD = 5       # ← AND anomaly_count > 5

# Ensemble Weights
XGB_WEIGHT = 0.6                        # ← Weight for XGBoost
AE_WEIGHT = 0.4                         # ← Weight for Autoencoder
```

---

### 2. ✅ Adjust if Needed

**Too many false positives? (Too strict)**

Make it more lenient:
```python
RISK_THRESHOLD = 0.8
BLOCK_AVG_RISK_THRESHOLD = 0.9
BLOCK_ANOMALY_COUNT_THRESHOLD = 10
```

**Too many attacks getting through? (Too lenient)**

Make it more strict:
```python
RISK_THRESHOLD = 0.5
BLOCK_AVG_RISK_THRESHOLD = 0.6
BLOCK_ANOMALY_COUNT_THRESHOLD = 3
```

---

## 🔧 Troubleshooting Checklist

### ❌ Problem: "Models not loaded"

**Symptoms:**
- Logs show: `"Models not loaded - running in fail-open mode"`
- `models_loaded: false` in `/health` response

**Solutions:**
- [ ] Check that `backend/models/` directory exists
- [ ] Verify model files exist (xgb_model.pkl, tfidf.pkl, etc.)
- [ ] Check file permissions (readable)
- [ ] Verify model files are not corrupted

---

### ❌ Problem: "All requests returning 403"

**Symptoms:**
- Every request blocked
- Too many IPs in blocked list

**Solutions:**
- [ ] Reset the system: `curl -X DELETE http://localhost:8002/security/reset`
- [ ] Adjust thresholds (make more lenient)
- [ ] Check if models are producing valid risk scores

---

### ❌ Problem: "No anomalies detected"

**Symptoms:**
- All risk scores are 0
- No anomalies in logs

**Solutions:**
- [ ] Check if models are loaded (`models_loaded: true`)
- [ ] Verify models are trained correctly
- [ ] Send obviously malicious payloads to test
- [ ] Check ensemble weights (not all zero)

---

### ❌ Problem: "Import errors"

**Symptoms:**
- `ModuleNotFoundError: No module named 'tensorflow'`

**Solutions:**
- [ ] Install missing packages: `pip install tensorflow xgboost scikit-learn`
- [ ] Activate virtual environment if using one
- [ ] Check Python version (3.8+ recommended)

---

## ✅ Final Verification

### Complete System Check

**Run all these commands:**

```powershell
# 1. Check files exist
cd backend\security
dir realtime_detection.py, realtime_api.py

# 2. Check models exist
cd ..\models
dir *.pkl, *.h5

# 3. Check dependencies
python -c "import fastapi, uvicorn, tensorflow, xgboost, sklearn, numpy, joblib; print('✓ All packages installed')"

# 4. Start the API
cd ..\security
.\QUICK_START_REALTIME.ps1

# 5. In a new terminal, run tests
cd backend\security
.\TEST_REALTIME_API.ps1

# 6. Check health endpoint
Invoke-RestMethod -Uri "http://localhost:8002/health" -Method Get

# 7. Send test request
Invoke-RestMethod -Uri "http://localhost:8002/api/login" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"username":"test","password":"test123"}'

# 8. Check security stats
Invoke-RestMethod -Uri "http://localhost:8002/security/stats" -Method Get
```

---

## 🎉 Success Criteria

Your system is ready when:

- ✅ All files created and exist
- ✅ ML models loaded successfully (`models_loaded: true`)
- ✅ API running on port 8002
- ✅ All 9 tests passing
- ✅ Health endpoint returns `"status": "healthy"`
- ✅ Deterministic behavior verified (same request = same risk)
- ✅ Security stats accessible
- ✅ Logs showing detection events

---

## 📚 Next Steps

Once everything is verified:

1. **Integration:** Add middleware to main `app.py`
2. **Customization:** Adjust thresholds based on your needs
3. **Monitoring:** Set up alerts for blocked IPs
4. **Optimization:** Fine-tune ensemble weights
5. **Production:** Deploy with proper model training on your data

---

## 📞 Support

If you encounter issues:

1. **Check this checklist** for troubleshooting steps
2. **Review logs** for detailed error messages
3. **Consult documentation:**
   - `REALTIME_DETECTION_README.md` - User guide
   - `APP_INTEGRATION_EXAMPLE.py` - Integration examples
   - `REALTIME_DETECTION_SUMMARY.md` - Project summary

---

**System Status:** [ ] Not Started  [ ] In Progress  [ ] ✅ Complete

---

**Last Updated:** February 2026  
**Version:** 1.0.0
