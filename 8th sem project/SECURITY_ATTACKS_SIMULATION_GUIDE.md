# 🔐 Security Attacks Simulation Guide

## ✅ SIMULATION MODE - SECURITY ATTACKS ONLY

The simulation system is now configured to **ONLY generate and detect these 3 critical security attacks**:

1. ✅ **SQL Injection** (CRITICAL)
2. ✅ **DDoS Attack** (CRITICAL)  
3. ✅ **XSS Attack** (HIGH)

---

## 🎯 Endpoint → Attack Type Mapping

### **SQL Injection Endpoints:**
| Endpoint | Attack Type | Injection Rate | Sample Pattern |
|----------|-------------|----------------|----------------|
| `/sim/login` | SQL_INJECTION | 70% | `username=admin' OR '1'='1` |
| `/sim/payment` | SQL_INJECTION | 70% | `id=1' UNION SELECT password` |
| `/sim/signup` | SQL_INJECTION | 70% | `search='; DROP TABLE users--` |
| `/sim/api/posts` | SQL_INJECTION | 70% | `query=1' AND 1=1--` |

### **DDoS Attack Endpoints:**
| Endpoint | Attack Type | Injection Rate | Characteristics |
|----------|-------------|----------------|-----------------|
| `/sim/search` | DDOS_ATTACK | 70% | 500-2000 requests/min, 500+ IPs |
| `/sim/api/users` | DDOS_ATTACK | 70% | High concurrency, service degradation |

### **XSS Attack Endpoints:**
| Endpoint | Attack Type | Injection Rate | Sample Pattern |
|----------|-------------|----------------|----------------|
| `/sim/profile` | XSS_ATTACK | 70% | `<script>alert("XSS")</script>` |
| `/sim/logout` | XSS_ATTACK | 70% | `<img src=x onerror=alert("XSS")>` |
| `/sim/api/data` | XSS_ATTACK | 70% | `javascript:alert("XSS")` |
| `/sim/api/comments` | XSS_ATTACK | 70% | `<iframe src="malicious.com">` |

---

## 🧪 Testing Each Attack Type

### **1. Test SQL Injection Attack**

#### **Simulate on Login Endpoint:**
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "/sim/login",
    "duration_seconds": 120
  }'
```

#### **Expected Attack Patterns Generated:**
```
username=admin' OR '1'='1&password=x
id=1' UNION SELECT password FROM users--
search='; DROP TABLE users--
username=admin'--&password=anything
query=1' AND 1=1--
```

#### **Detection Output:**
```json
{
  "is_anomaly": true,
  "anomaly_type": "sql_injection",
  "severity": "CRITICAL",
  "confidence": 0.95,
  "malicious_pattern": "SQL_INJECTION",
  "sql_keywords_count": 5,
  "endpoint": "/sim/login"
}
```

---

### **2. Test DDoS Attack**

#### **Simulate on Search Endpoint:**
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "/sim/search",
    "duration_seconds": 120
  }'
```

#### **Expected Attack Characteristics:**
```
Request Volume: 500-2000 requests per minute
Unique IPs: 100-500 different source IPs
Status Codes: 503, 504, 429 (service overloaded)
Response Time: 800-2000ms (degraded performance)
```

#### **Detection Output:**
```json
{
  "is_anomaly": true,
  "anomaly_type": "ddos_attack",
  "severity": "CRITICAL",
  "confidence": 0.95,
  "request_count": 1500,
  "unique_ips": 250,
  "endpoint": "/sim/search"
}
```

---

### **3. Test XSS Attack**

#### **Simulate on Profile Endpoint:**
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "/sim/profile",
    "duration_seconds": 90
  }'
```

#### **Expected Attack Patterns Generated:**
```
comment=<script>alert("XSS")</script>
search=<img src=x onerror=alert("XSS")>
input=<iframe src="malicious.com"></iframe>
name=<body onload=alert("XSS")>
data=javascript:alert("XSS")
```

#### **Detection Output:**
```json
{
  "is_anomaly": true,
  "anomaly_type": "xss_attack",
  "severity": "HIGH",
  "confidence": 0.90,
  "malicious_pattern": "XSS_ATTACK",
  "xss_keywords_count": 3,
  "endpoint": "/sim/profile"
}
```

---

## 📊 Attack Detection Criteria

### **SQL Injection Detection:**
✅ SQL keywords detected > 3 (`OR`, `AND`, `SELECT`, `DROP`, `UNION`, `--`, `'`)  
✅ Malicious pattern flag: `SQL_INJECTION`  
✅ Severity: **CRITICAL**  
✅ Confidence: **95%**  
✅ Auto-block IP: **YES**

### **DDoS Attack Detection:**
✅ Request rate > 200 requests/minute  
✅ OR: 100+ requests from 50+ unique IPs  
✅ High request_count in logs  
✅ Severity: **CRITICAL**  
✅ Confidence: **95%**  
✅ Auto-block IP: **YES**

### **XSS Attack Detection:**
✅ XSS keywords detected > 2 (`<script>`, `<img`, `javascript:`, `<iframe>`, `onerror=`)  
✅ Malicious pattern flag: `XSS_ATTACK`  
✅ Severity: **HIGH**  
✅ Confidence: **90%**  
✅ Auto-block IP: **YES**

---

## 🔄 Complete Test Workflow

### **Step 1: Start Backend**
```bash
cd "8th sem project/backend"
python app.py
```

### **Step 2: Run SQL Injection Simulation**
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/sim/login", "duration_seconds": 120}'
```

### **Step 3: Monitor Detection (60 seconds)**
Detection runs every 60 seconds. Wait for the periodic detection cycle.

### **Step 4: Check Results**
```bash
# View all detected anomalies
curl http://localhost:8000/api/anomalies/logs

# Check ML detector statistics
curl http://localhost:8000/api/ml/anomaly-detector/status

# View blocked IPs
curl http://localhost:8000/api/ml/anomaly-detector/blocked-ips

# Get simulation status
curl http://localhost:8000/api/anomalies/stats
```

### **Step 5: Test Other Attacks**
```bash
# Test DDoS
curl -X POST http://localhost:8000/api/simulate \
  -d '{"endpoint": "/sim/search", "duration_seconds": 120}'

# Test XSS
curl -X POST http://localhost:8000/api/simulate \
  -d '{"endpoint": "/sim/profile", "duration_seconds": 90}'
```

---

## 📈 What You'll See in Logs

### **Console Output:**
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
   IPs involved: 15
   SQL keywords: 7
   Severity: CRITICAL

[ML ANOMALY] ⚠️ ML ensemble detected anomaly!
   Protocol: http
   Confidence: 92%
   Models voted: 6/8
   Failure probability: 85%

[ML ANOMALY] 🚫 IP blocked: SIM-12 (confidence: 92%)
[ML ANOMALY] 🚫 IP blocked: SIM-8 (confidence: 95%)
```

### **Database Records:**
```sql
-- APILog table shows:
endpoint: /sim/login
malicious_pattern: SQL_INJECTION
query_params: username=admin' OR '1'='1&password=x
status_code: 403
is_simulation: true

-- AnomalyLog table shows:
anomaly_type: sql_injection
severity: CRITICAL
confidence: 0.95
is_anomaly: true
```

---

## 🎯 Injection Rate: 70%

**70% of simulated requests will contain attack patterns**, ensuring high detection rates while maintaining some normal traffic baseline.

- ✅ 70% of requests → Inject malicious patterns
- ⚪ 30% of requests → Normal benign traffic

This ratio provides:
- Clear attack signals for ML models
- Realistic mix of malicious/benign traffic
- High anomaly detection confidence

---

## 🔧 Attack Pattern Variations

### **SQL Injection - 5 Different Patterns:**
```python
patterns = [
    "username=admin' OR '1'='1&password=x",           # Classic bypass
    "id=1' UNION SELECT password FROM users--",       # Data extraction
    "search='; DROP TABLE users--",                   # Destructive
    "username=admin'--&password=anything",            # Comment injection
    "query=1' AND 1=1--"                              # Boolean-based
]
```

### **XSS - 5 Different Patterns:**
```python
patterns = [
    'comment=<script>alert("XSS")</script>',          # Script injection
    'search=<img src=x onerror=alert("XSS")>',        # Image tag exploit
    'input=<iframe src="malicious.com"></iframe>',    # Frame injection
    'name=<body onload=alert("XSS")>',                # Event handler
    'data=javascript:alert("XSS")'                    # JavaScript protocol
]
```

### **DDoS - Volume-Based:**
```python
characteristics = {
    'request_count': random.randint(500, 2000),       # High volume
    'unique_ips': 100-500,                            # Distributed
    'response_time_ms': 800-2000,                     # Degraded service
    'status_code': [503, 504, 429, 200]               # Overload indicators
}
```

---

## 🚀 Quick Test All Attacks

### **One-Line Test Script:**
```bash
# SQL Injection
curl -X POST http://localhost:8000/api/simulate -H "Content-Type: application/json" -d '{"endpoint": "/sim/login", "duration_seconds": 90}' & \

# DDoS Attack  
sleep 5 && curl -X POST http://localhost:8000/api/simulate -H "Content-Type: application/json" -d '{"endpoint": "/sim/search", "duration_seconds": 90}' & \

# XSS Attack
sleep 10 && curl -X POST http://localhost:8000/api/simulate -H "Content-Type: application/json" -d '{"endpoint": "/sim/profile", "duration_seconds": 90}'

# Check results after 60 seconds
sleep 60 && curl http://localhost:8000/api/anomalies/logs
```

---

## ✅ Verification Checklist

**Before Testing:**
- [x] Backend is running (`python app.py`)
- [x] Virtual environment activated
- [x] Database initialized (auto-created on first run)
- [x] ML models loaded (check console for model loading messages)

**During Simulation:**
- [x] Console shows "SIMULATION STARTED" message
- [x] Requests being generated (watch request counter)
- [x] Attack patterns in logs (malicious_pattern field set)
- [x] No errors in console

**After Detection (60 seconds):**
- [x] "ANOMALY DETECTED" message appears
- [x] Anomaly type matches endpoint mapping
- [x] Confidence ≥ 90% for attacks
- [x] IPs are blocked (check blocked-ips endpoint)
- [x] Anomaly logs saved to database

---

## 📚 Related Configuration Files

| File | What Changed | Purpose |
|------|--------------|---------|
| `anomaly_injection.py` | Endpoint mappings updated | Maps endpoints to security attacks only |
| `app.py` | Simulation code simplified | Generates only SQL/DDoS/XSS patterns |
| `anomaly_detection.py` | Detection logic active | Detects all 3 attack types |
| `feature_engineering.py` | Pattern extraction | Extracts malicious patterns from logs |
| `database.py` | Schema extended | Stores attack indicators |

---

## 🎓 Understanding Detection Flow

```
1. SIMULATION STARTS
   └─> /sim/login selected
   └─> Mapped to: SQL_INJECTION
   └─> 70% injection rate

2. TRAFFIC GENERATION
   └─> Generate 50 requests/batch
   └─> 35 with SQL injection patterns
   └─> 15 normal requests
   └─> Save to database with malicious_pattern

3. FEATURE EXTRACTION (every 60s)
   └─> Extract features from 1-minute window
   └─> Count SQL keywords in query_params
   └─> Detect malicious_pattern flags
   └─> Calculate error rate, response times

4. ANOMALY DETECTION
   Rule-Based:
   └─> SQL keywords > 3? ✓
   └─> malicious_pattern = 'SQL_INJECTION'? ✓
   └─> Confidence: 95%, Severity: CRITICAL
   
   ML Ensemble:
   └─> CSIC XGBoost model: ANOMALY
   └─> CSIC Autoencoder: ANOMALY
   └─> CIC IDS models: 4/6 vote ANOMALY
   └─> Ensemble confidence: 92%

5. RESPONSE ACTIONS
   └─> Log to AnomalyLog table
   └─> Block IPs with confidence ≥ 70%
   └─> Generate AI mitigation strategies
   └─> Send email alerts (if configured)
   └─> Update dashboard statistics
```

---

## ✅ SUCCESS CRITERIA

**Your simulation is working correctly if:**

1. ✅ Endpoint mapping shows correct attack type
2. ✅ 70% of logs have `malicious_pattern` set
3. ✅ `query_params` contains attack payloads
4. ✅ Detection confidence ≥ 90%
5. ✅ Anomaly type matches endpoint assignment
6. ✅ IPs get auto-blocked after threshold
7. ✅ Both rule-based and ML detectors agree
8. ✅ No performance anomalies (latency_spike, etc.) detected in simulation

---

## 🔗 Next Steps

1. **Test each attack type** using the curl commands above
2. **Monitor detection rates** - Should see 70%+ detection accuracy
3. **Check IP blocking** - Verify IPs are blocked after repeated attacks
4. **Review ML model predictions** - Check ensemble voting results
5. **Tune thresholds** if needed (in `anomaly_detection.py`)

---

## 💡 Pro Tips

- **Run simulations for 90-120 seconds** to generate enough data for detection
- **Wait 60 seconds** after starting simulation for first detection cycle
- **Use different endpoints** to test all three attack types
- **Check database** directly if you want to see raw attack data
- **Monitor console output** for real-time detection feedback

---

## 🎯 SIMULATION MODE IS NOW 100% FOCUSED ON SECURITY ATTACKS

✅ SQL Injection detection active  
✅ DDoS attack detection active  
✅ XSS attack detection active  
✅ Performance anomalies removed from simulation  
✅ 70% injection rate ensures high detection  
✅ ML models + rule-based detection both active  

**Your system is ready to detect real security threats! 🛡️**
