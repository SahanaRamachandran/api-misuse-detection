# ⚡ QUICK REFERENCE: AI Resolutions & Simulation IP Tracking

## 🚀 Quick Start

### Check If Features Are Active
```bash
# Check backend startup logs
# Should see:
# ✅ Real-time detection middleware enabled!
# ✅ AI Resolution Engine initialized
```

### View Simulation IP Tracking
```bash
curl http://localhost:8000/api/security/simulation/ip-stats | jq
```

### View AI Resolutions
AI resolutions are automatically generated when anomalies are detected.
Check detection results in `/api/security/realtime/stats`.

---

## 📋 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/security/simulation/ip-stats` | GET | Simulation IP statistics |
| `/api/security/combined/ip-stats` | GET | Live + Simulation combined stats |
| `/api/security/realtime/stats` | GET | Real-time detection stats (includes AI resolutions) |
| `/api/security/realtime/blocked-ips` | GET | List of blocked IPs |
| `/api/security/realtime/ip/{ip}` | GET | Specific IP profile |
| `/api/security/realtime/unblock/{ip}` | POST | Unblock an IP |
| `/api/security/realtime/reset` | DELETE | Reset all tracking |

---

## 🎯 Quick Tests

### Test 1: Simulation IP Tracking
```powershell
# Start simulation
Invoke-RestMethod -Uri "http://localhost:8000/api/simulation/start" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"duration_seconds": 30, "requests_per_second": 100}'

# Wait 5 seconds
Start-Sleep -Seconds 5

# Check simulation IP stats
Invoke-RestMethod -Uri "http://localhost:8000/api/security/simulation/ip-stats" | ConvertTo-Json -Depth 10
```

**Expected Output:**
```json
{
  "summary": {
    "total_simulation_ips": 50,
    "total_simulation_requests": 500,
    "total_simulation_anomalies": 25,
    "anomaly_rate": 5.0
  },
  "top_risky_simulation_ips": [...]
}
```

### Test 2: AI Resolution Generation
```powershell
# Trigger anomaly on live endpoint
Invoke-RestMethod -Uri "http://localhost:8000/login" `
  -Method POST `
  -Headers @{"X-Forwarded-For"="192.168.1.100"} `
  -Body (@{username="admin' OR '1'='1"; password="test"} | ConvertTo-Json)

# Check if AI resolution was generated
Invoke-RestMethod -Uri "http://localhost:8000/api/security/realtime/stats"
```

---

## 🔍 What to Look For

### In Backend Logs

**Simulation IP Tracking:**
```
SIMULATION DETECTION | IP: SIM-45 | Endpoint: /sim/login | 
RISK: 0.8234 | Anomaly: True | 
Profile: Avg=0.8234, Count=125/450
```

**AI Resolution:**
```
✅ AI Resolution generated for sql_injection (HIGH)
```

**Startup:**
```
[REALTIME DETECTION] ✅ Real-time detection middleware enabled!
   - XGBoost + Autoencoder ensemble
   - Automatic IP profiling and blocking
   - Deterministic risk scoring
   - AI-powered resolution suggestions (OpenAI GPT-4)
```

### In API Responses

**AI Resolution Structure:**
```json
{
  "ai_resolution": {
    "anomaly_type": "sql_injection",
    "severity": "HIGH",
    "generated_by": "OpenAI GPT-4",
    "resolution_strategy": {
      "immediate_containment": "...",
      "network_mitigation": "...",
      "application_mitigation": "...",
      "forensic_analysis": "...",
      "detection_improvement": "...",
      "risk_explanation": "...",
      "ip_blocking_recommendation": "...",
      "infrastructure_rules": "...",
      "api_hardening": "..."
    }
  }
}
```

---

## 🛠️ Configuration Quick Reference

### OpenAI API Key
**File:** `backend/app.py` (line ~73)
```python
OPENAI_API_KEY = "sk-proj-..."
```

### Detection Thresholds
**File:** `backend/security/realtime_detection.py`
```python
RISK_THRESHOLD = 0.7  # Anomaly threshold
BLOCK_AVG_RISK_THRESHOLD = 0.8  # Auto-block
BLOCK_ANOMALY_COUNT_THRESHOLD = 5  # Min anomalies
```

### AI Model Configuration
**File:** `backend/ai_resolution_engine.py`
```python
model="gpt-4"
temperature=0.3
max_tokens=3000
```

---

## ⚡ Common Commands

### Start Backend with AI Resolution
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install openai  # If not already installed
python app.py
```

### Monitor Simulation IP Tracking
```powershell
# Continuous monitoring (refresh every 2 seconds)
while ($true) {
    Clear-Host
    Write-Host "=== SIMULATION IP STATS ===" -ForegroundColor Cyan
    Invoke-RestMethod -Uri "http://localhost:8000/api/security/simulation/ip-stats" | ConvertTo-Json -Depth 5
    Start-Sleep -Seconds 2
}
```

### View Combined Stats
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/security/combined/ip-stats" | ConvertTo-Json -Depth 10
```

---

## 🔧 Troubleshooting

### AI Resolutions Not Generating

**Check 1:** OpenAI API Key
```powershell
# In backend/app.py, verify OPENAI_API_KEY is set
# Should see in logs: "✅ AI Resolution Engine initialized"
```

**Check 2:** OpenAI Package Installed
```powershell
pip show openai
# If not installed: pip install openai
```

**Check 3:** API Key Valid
```powershell
# Test API key manually
pip install openai
python -c "import openai; openai.api_key='YOUR_KEY'; print(openai.Model.list())"
```

### Simulation IPs Not Being Tracked

**Check 1:** Real-Time Detection Active
```powershell
# Should see in logs:
# [REALTIME DETECTION] ✅ Real-time detection middleware enabled!
```

**Check 2:** Simulation Running
```bash
# Check simulation status
curl http://localhost:8000/api/simulation/status
```

**Check 3:** Backend Logs
```powershell
# Look for: "SIMULATION DETECTION | IP: SIM-..."
```

---

## 📊 Monitoring Dashboard Queries

### Top 5 Risky Simulation IPs
```powershell
$stats = Invoke-RestMethod -Uri "http://localhost:8000/api/security/simulation/ip-stats"
$stats.top_risky_simulation_ips | Select-Object -First 5 | Format-Table
```

### Anomaly Rate Comparison (Live vs Simulation)
```powershell
$combined = Invoke-RestMethod -Uri "http://localhost:8000/api/security/combined/ip-stats"
Write-Host "Live Anomaly Rate: $($combined.live_mode.anomaly_rate)%"
Write-Host "Simulation Anomaly Rate: $($combined.simulation_mode.anomaly_rate)%"
```

### All Blocked IPs
```powershell
$blocked = Invoke-RestMethod -Uri "http://localhost:8000/api/security/realtime/blocked-ips"
$blocked.blocked_ips | Format-Table
```

---

## 💡 Pro Tips

1. **Cost Management**: AI resolutions cost ~$0.10-$0.20 per anomaly. Monitor OpenAI usage.

2. **Simulation Testing**: Run simulation with different anomaly types to see varied AI resolutions.

3. **Resolution Export**: Save AI resolutions for documentation:
   ```powershell
   $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/security/realtime/stats"
   $stats | ConvertTo-Json -Depth 20 | Out-File "resolutions.json"
   ```

4. **IP Analysis**: Compare live vs simulation IP patterns to validate detection accuracy.

5. **Threshold Tuning**: Adjust `RISK_THRESHOLD` in realtime_detection.py to control sensitivity.

---

## 📖 Full Documentation

For comprehensive documentation, see:
- **AI_RESOLUTION_AND_SIMULATION_IP_TRACKING.md** - Complete feature documentation

---

**Last Updated**: February 2024  
**Status**: ✅ Active
