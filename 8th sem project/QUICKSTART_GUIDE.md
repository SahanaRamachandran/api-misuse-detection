# 🚀 QUICK START GUIDE - Security Attack Detection System

## ✅ SYSTEM OVERVIEW

**ONLY 3 Security Attack Types Detected:**
1. **SQL Injection** (CRITICAL - 95% confidence)
2. **DDoS Attack** (CRITICAL - 95% confidence)  
3. **XSS Attack** (HIGH - 90% confidence)

**Different Endpoints = Different Anomaly Types**

---

## 🎯 STEP 1: START THE SYSTEM

### Option A: Start Everything (Recommended)
**Double-click:** `RUN_FULL_SYSTEM.bat`

This will:
- ✅ Start backend on http://localhost:8000
- ✅ Start frontend on http://localhost:5173
- ✅ Open both in separate windows

### Option B: Start Manually
1. **Start Backend:** Double-click `START_BACKEND.bat`
2. **Start Frontend:** Double-click `START_FRONTEND.bat`

---

## 📍 ENDPOINT → ATTACK TYPE MAPPING

### SQL Injection Endpoints (4 endpoints)
| Endpoint | Attack Type | Status |
|----------|-------------|--------|
| `/sim/login` | SQL Injection | ✅ Active |
| `/sim/payment` | SQL Injection | ✅ Active |
| `/sim/signup` | SQL Injection | ✅ Active |
| `/sim/api/posts` | SQL Injection | ✅ Active |

### DDoS Attack Endpoints (2 endpoints)
| Endpoint | Attack Type | Status |
|----------|-------------|--------|
| `/sim/search` | DDoS Attack | ✅ Active |
| `/sim/api/users` | DDoS Attack | ✅ Active |

### XSS Attack Endpoints (4 endpoints)
| Endpoint | Attack Type | Status |
|----------|-------------|--------|
| `/sim/profile` | XSS Attack | ✅ Active |
| `/sim/logout` | XSS Attack | ✅ Active |
| `/sim/api/data` | XSS Attack | ✅ Active |
| `/sim/api/comments` | XSS Attack | ✅ Active |

---

## 🧪 STEP 2: TEST EACH ATTACK TYPE

### Test SQL Injection on `/sim/login`
```bash
curl -X POST http://localhost:8000/api/simulate ^
  -H "Content-Type: application/json" ^
  -d "{\"endpoint\": \"/sim/login\", \"duration_seconds\": 120}"
```

**Expected Attack Patterns:**
- `username=admin' OR '1'='1&password=x`
- `id=1' UNION SELECT password FROM users--`
- `search='; DROP TABLE users--`
- `username=admin'--&password=anything`

### Test DDoS Attack on `/sim/search`
```bash
curl -X POST http://localhost:8000/api/simulate ^
  -H "Content-Type: application/json" ^
  -d "{\"endpoint\": \"/sim/search\", \"duration_seconds\": 120}"
```

**Expected Characteristics:**
- 500-2000 requests per minute
- 100-500 unique source IPs
- Status codes: 503, 504, 429 (overload)
- Response time: 800-2000ms (degraded)

### Test XSS Attack on `/sim/profile`
```bash
curl -X POST http://localhost:8000/api/simulate ^
  -H "Content-Type: application/json" ^
  -d "{\"endpoint\": \"/sim/profile\", \"duration_seconds\": 90}"
```

**Expected Attack Patterns:**
- `comment=<script>alert("XSS")</script>`
- `search=<img src=x onerror=alert("XSS")>`
- `input=<iframe src="malicious.com"></iframe>`
- `name=<body onload=alert("XSS")>`

---

## 📊 STEP 3: MONITOR DETECTION

### View Detection Results

#### Via Browser:
**Frontend Dashboard:** http://localhost:5173
- Real-time anomaly display
- Attack type visualization
- IP blocking status

**API Documentation:** http://localhost:8000/docs
- Interactive API testing
- Endpoint exploration

#### Via API:
```bash
# View all detected anomalies
curl http://localhost:8000/api/anomalies/logs

# Check ML detector status
curl http://localhost:8000/api/ml/anomaly-detector/status

# View blocked IPs
curl http://localhost:8000/api/ml/anomaly-detector/blocked-ips

# Get simulation status
curl http://localhost:8000/api/anomalies/stats
```

---

## 🔍 STEP 4: VERIFY DETECTION

### What You Should See:

#### Console Output:
```
🎬 SIMULATION STARTED
======================================================================
   Endpoint: /sim/login
   Anomaly Type: sql_injection
   Duration: 120s
======================================================================

[ANOMALY DETECTED] ⚠️  CRITICAL anomaly detected!
   Endpoint: /sim/login
   Type: sql_injection
   Confidence: 95%
   SQL keywords: 7
   Severity: CRITICAL

[ML ANOMALY] ⚠️ ML ensemble detected anomaly!
   Protocol: http
   Confidence: 92%
   Models voted: 6/8
   Failure probability: 85%

[ML ANOMALY] 🚫 IP blocked: SIM-12 (confidence: 92%)
```

#### API Response:
```json
{
  "is_anomaly": true,
  "anomaly_type": "sql_injection",
  "severity": "CRITICAL",
  "confidence": 0.95,
  "malicious_pattern": "SQL_INJECTION",
  "sql_keywords_count": 7,
  "endpoint": "/sim/login"
}
```

---

## 🎯 COMPLETE TEST SEQUENCE

### Test All 3 Attack Types (5 minutes)

```bash
# 1. SQL Injection (120 seconds)
curl -X POST http://localhost:8000/api/simulate -H "Content-Type: application/json" -d "{\"endpoint\": \"/sim/login\", \"duration_seconds\": 120}"

# Wait 60 seconds for detection cycle...

# 2. DDoS Attack (120 seconds)
curl -X POST http://localhost:8000/api/simulate -H "Content-Type: application/json" -d "{\"endpoint\": \"/sim/search\", \"duration_seconds\": 120}"

# Wait 60 seconds for detection cycle...

# 3. XSS Attack (90 seconds)
curl -X POST http://localhost:8000/api/simulate -H "Content-Type: application/json" -d "{\"endpoint\": \"/sim/profile\", \"duration_seconds\": 90}"

# Check all results
curl http://localhost:8000/api/anomalies/logs
```

---

## 📈 DETECTION TIMELINE

```
0:00  → Start simulation (e.g., /sim/login)
0:01  → Traffic generation begins (70% attack, 30% normal)
1:00  → Detection cycle runs ✓
1:01  → Anomaly detected and logged!
1:01  → IPs blocked (if confidence ≥ 70%)
2:00  → Simulation ends
```

**Key Point:** Detection runs every **60 seconds**, so wait at least 1 minute after starting simulation.

---

## ✅ SUCCESS INDICATORS

**System is working correctly if you see:**

### ✓ In Console:
- [x] "SIMULATION STARTED" with endpoint + attack type
- [x] "ANOMALY DETECTED" with CRITICAL/HIGH severity
- [x] "ML ensemble detected anomaly" with 90%+ confidence
- [x] "IP blocked" messages for attacking IPs

### ✓ In API Response:
- [x] `"is_anomaly": true`
- [x] `"anomaly_type"` matches endpoint mapping
- [x] `"confidence"` ≥ 0.90 (90%+)
- [x] `"malicious_pattern"` is set
- [x] SQL/XSS keyword counts > 0

### ✓ In Dashboard:
- [x] Anomaly appears in real-time
- [x] Attack type correctly identified
- [x] Severity shown as CRITICAL or HIGH
- [x] IP addresses listed and blocked

---

## 🔧 ENDPOINT TESTING MATRIX

| Endpoint | Attack Type | Test Command |
|----------|-------------|--------------|
| `/sim/login` | SQL Injection | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/login\", \"duration_seconds\": 120}"` |
| `/sim/payment` | SQL Injection | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/payment\", \"duration_seconds\": 120}"` |
| `/sim/signup` | SQL Injection | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/signup\", \"duration_seconds\": 120}"` |
| `/sim/api/posts` | SQL Injection | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/api/posts\", \"duration_seconds\": 120}"` |
| `/sim/search` | DDoS Attack | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/search\", \"duration_seconds\": 120}"` |
| `/sim/api/users` | DDoS Attack | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/api/users\", \"duration_seconds\": 120}"` |
| `/sim/profile` | XSS Attack | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/profile\", \"duration_seconds\": 90}"` |
| `/sim/logout` | XSS Attack | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/logout\", \"duration_seconds\": 90}"` |
| `/sim/api/data` | XSS Attack | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/api/data\", \"duration_seconds\": 90}"` |
| `/sim/api/comments` | XSS Attack | `curl -X POST http://localhost:8000/api/simulate -d "{\"endpoint\": \"/sim/api/comments\", \"duration_seconds\": 90}"` |

---

## 🎓 HOW IT WORKS

### 1. Traffic Generation (70% Attack Rate)
- Simulation generates realistic attack patterns
- 70% of requests contain malicious payloads
- 30% are normal benign traffic

### 2. Feature Extraction (Every 60s)
- Analyzes 1-minute time windows
- Extracts SQL/XSS keywords from query parameters
- Counts request volume and unique IPs for DDoS

### 3. Dual Detection System
**Rule-Based Detector:**
- SQL keywords > 3 → SQL Injection
- Request rate > 200/min → DDoS
- XSS keywords > 2 → XSS Attack

**ML Ensemble (8 Models):**
- CIC IDS 2017: 6 models for network attacks
- CSIC 2010: 2 models for HTTP attacks
- Majority voting for final decision

### 4. Automated Response
- Log anomaly to database
- Block IPs with confidence ≥ 70%
- Generate AI mitigation strategies
- Send email alerts (if configured)

---

## 🚨 TROUBLESHOOTING

### Backend won't start?
```bash
cd "8th sem project/backend"
..\.venv\Scripts\activate
python app.py
```

### Frontend won't start?
```bash
cd "8th sem project/frontend"
npm install
npm run dev
```

### No anomalies detected?
- ✓ Wait at least 60 seconds after starting simulation
- ✓ Check console for "SIMULATION STARTED" message
- ✓ Verify endpoint name is correct (case-sensitive)
- ✓ Ensure backend is running without errors

### Low confidence scores?
- This is expected for legitimate variations
- Security attacks should have 90%+ confidence
- Check malicious_pattern field is set correctly

---

## 📚 ADDITIONAL RESOURCES

- **Full Guide:** `SECURITY_ATTACKS_SIMULATION_GUIDE.md`
- **Quick Reference:** `SECURITY_ATTACKS_QUICK_REF.md`
- **Attack Detection:** `ATTACK_DETECTION_QUICK_REF.md`
- **ML Models:** `ML_ATTACK_DETECTION_COMPLETE.md`

---

## ✅ SYSTEM IS READY!

**Everything is configured for security attack detection:**
- ✅ Only SQL Injection, DDoS, and XSS attacks detected
- ✅ Different endpoints have different attack types
- ✅ 70% injection rate ensures strong detection
- ✅ ML models + rule-based detection active
- ✅ Auto IP blocking on high confidence

**Start testing now with `RUN_FULL_SYSTEM.bat`! 🚀**
