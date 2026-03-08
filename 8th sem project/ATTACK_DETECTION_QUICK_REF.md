# 🚨 Attack Detection Quick Reference

## Supported Attack Types

| Attack | Endpoint | Severity | Confidence | Auto-Block |
|--------|----------|----------|------------|------------|
| **SQL Injection** | `/login`, `/sim/login` | CRITICAL | 95% | ✅ Yes |
| **DDoS Attack** | `/api/users`, `/sim/api/users` | CRITICAL | 95% | ✅ Yes |
| **XSS Attack** | `/api/data`, `/sim/api/data` | HIGH | 90% | ✅ Yes |
| Latency Spike | `/payment`, `/sim/payment` | HIGH | 75% | ⚠️ Conditional |
| Error Spike | `/logout` | CRITICAL | 90% | ✅ Yes |
| Traffic Burst | `/search`, `/sim/search` | MEDIUM | 60% | ❌ No |
| Resource Exhaustion | `/signup`, `/sim/signup` | CRITICAL | 95% | ✅ Yes |
| Timeout | `/profile`, `/sim/profile` | HIGH | 80% | ⚠️ Conditional |

---

## Quick Test Commands

### Test SQL Injection
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/sim/login", "duration_seconds": 120}'
```

### Test DDoS Attack
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/sim/api/users", "duration_seconds": 120}'
```

### Test XSS Attack
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/sim/api/data", "duration_seconds": 90}'
```

### Check Detection Status
```bash
# View all anomalies
curl http://localhost:8000/api/anomalies/logs

# ML detector status
curl http://localhost:8000/api/ml/anomaly-detector/status

# Blocked IPs
curl http://localhost:8000/api/ml/anomaly-detector/blocked-ips
```

---

## Attack Patterns Detected

### SQL Injection Keywords:
- `'`, `OR`, `AND`, `SELECT`, `DROP`, `UNION`, `--`, `admin`
- Pattern: `username=admin' OR '1'='1`

### XSS Patterns:
- `<script>`, `<img`, `javascript:`, `<iframe>`, `onerror=`, `onload=`
- Pattern: `<script>alert("XSS")</script>`

### DDoS Indicators:
- Request rate > 200/min
- 100+ requests + 50+ unique IPs
- Concurrent connections > 1000

---

## Detection Thresholds

```python
SQL Injection:   sql_keywords > 3 OR malicious_pattern == 'SQL_INJECTION'
DDoS Attack:     request_rate > 200 OR (req_count > 100 AND unique_ips > 50)
XSS Attack:      xss_keywords > 2 OR malicious_pattern == 'XSS_ATTACK'
Latency Spike:   avg_response_time > 600ms (3x baseline)
Error Spike:     error_rate > 25%
```

---

## Files Modified

✅ `anomaly_injection.py` - Added SQL/DDoS/XSS attack types  
✅ `anomaly_detection.py` - Added detection logic  
✅ `feature_engineering.py` - Extract attack patterns  
✅ `database.py` - Added malicious_pattern field  
✅ `app.py` - Simulation & logging updated  
✅ `ml_anomaly_detection.py` - Already integrated ✅

---

## System Architecture

```
Traffic → Database → Feature Extraction → Detection
                                           ↓
                                    ┌──────┴──────┐
                                    │             │
                              Rule-Based        ML Models
                              Detector          (Ensemble)
                                    │             │
                                    └──────┬──────┘
                                           ↓
                                   IP Blocking &
                                   Alert System
```

---

## Quick Verification

1. **Start backend:** `python app.py`
2. **Simulate attack:** Use curl commands above
3. **Wait 60 seconds:** Detection runs every minute
4. **Check logs:** `curl http://localhost:8000/api/anomalies/logs`
5. **Verify detection:** Look for `anomaly_type: "sql_injection"` etc.

---

## Need Help?

- Full documentation: `ML_ATTACK_DETECTION_COMPLETE.md`
- ML models guide: `ML_ANOMALY_DETECTION_README.md`
- Integration guide: `INTEGRATION_COMPLETE.md`
