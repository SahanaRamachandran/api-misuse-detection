# 🎯 SECURITY ATTACKS - QUICK TEST REFERENCE

## ✅ ONLY 3 ATTACK TYPES IN SIMULATION

1. **SQL Injection** (CRITICAL - 95% confidence)
2. **DDoS Attack** (CRITICAL - 95% confidence)
3. **XSS Attack** (HIGH - 90% confidence)

---

## 🚀 Quick Test Commands

### SQL Injection → `/sim/login`
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/sim/login", "duration_seconds": 120}'
```

### DDoS Attack → `/sim/search`
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/sim/search", "duration_seconds": 120}'
```

### XSS Attack → `/sim/profile`
```bash
curl -X POST http://localhost:8000/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"endpoint": "/sim/profile", "duration_seconds": 90}'
```

---

## 📊 All Security Attack Endpoints

| Endpoint | Attack Type | Pattern Example |
|----------|-------------|-----------------|
| `/sim/login` | SQL Injection | `admin' OR '1'='1` |
| `/sim/payment` | SQL Injection | `UNION SELECT password` |
| `/sim/signup` | SQL Injection | `DROP TABLE users--` |
| `/sim/api/posts` | SQL Injection | `1' AND 1=1--` |
| `/sim/search` | DDoS | 500+ req/min, 100+ IPs |
| `/sim/api/users` | DDoS | High concurrency flood |
| `/sim/profile` | XSS | `<script>alert("XSS")` |
| `/sim/logout` | XSS | `<img onerror=alert()>` |
| `/sim/api/data` | XSS | `javascript:alert()` |
| `/sim/api/comments` | XSS | `<iframe src=evil>` |

---

## 🔍 Check Detection Results

```bash
# View all detected anomalies
curl http://localhost:8000/api/anomalies/logs

# ML detector status
curl http://localhost:8000/api/ml/anomaly-detector/status

# Blocked IPs
curl http://localhost:8000/api/ml/anomaly-detector/blocked-ips
```

---

## ⏱️ Detection Timeline

1. **Start simulation** → Immediate
2. **Traffic generation** → Continuous (70% attack, 30% normal)
3. **Wait for detection** → 60 seconds (periodic cycle)
4. **Check results** → Anomaly logged with CRITICAL/HIGH severity

---

## ✅ Expected Output

```json
{
  "is_anomaly": true,
  "anomaly_type": "sql_injection" | "ddos_attack" | "xss_attack",
  "severity": "CRITICAL" | "HIGH",
  "confidence": 0.90-0.95,
  "malicious_pattern": "SQL_INJECTION" | "DDOS_ATTACK" | "XSS_ATTACK"
}
```

---

## 🎯 Injection Rate: 70%

- ✅ **70% of requests** = Attack patterns
- ⚪ **30% of requests** = Normal traffic

---

## 📝 Console Success Indicators

```
✓ SIMULATION STARTED (shows endpoint + attack type)
✓ ANOMALY DETECTED (shows CRITICAL/HIGH severity)
✓ ML ensemble detected anomaly (92%+ confidence)
✓ IP blocked (shows blocked IP addresses)
```

---

**Full guide:** `SECURITY_ATTACKS_SIMULATION_GUIDE.md`
