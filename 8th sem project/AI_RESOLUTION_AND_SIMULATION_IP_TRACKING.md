# AI-Powered Resolution System & Simulation IP Tracking

## 🎯 Overview

This document describes the newly implemented features:

1. **AI-Powered Resolution System** - OpenAI GPT-4 generates extremely detailed, technically accurate mitigation strategies
2. **Simulation Mode IP Tracking** - Real-time IP tracking now works for both LIVE and SIMULATION modes

---

## 🤖 AI-Powered Resolution System

### Features

The AI Resolution Engine uses OpenAI GPT-4 to generate comprehensive, production-ready mitigation strategies for detected anomalies.

### What Gets Generated

For **EVERY** detected anomaly, the system automatically generates 9 detailed sections:

#### 1. **Immediate Containment Steps**
- Time-critical actions to execute RIGHT NOW
- Exact commands to stop the threat
- Emergency response procedures

#### 2. **Network-Level Mitigation**
- Specific firewall rules (iptables, UFW)
- Load balancer configuration
- DDoS protection measures
- Network segmentation recommendations

#### 3. **Application-Level Mitigation**
- Code fixes with exact snippets
- Configuration changes with specific values
- Input validation improvements
- Rate limiting implementation

#### 4. **Logging & Forensic Analysis Queries**
- Exact log queries (grep, awk, SQL)
- What to search for in logs
- Log retention recommendations
- SIEM integration suggestions

#### 5. **Detection Improvement Strategy**
- How to detect this faster next time
- New monitoring rules to add
- Alert threshold tuning
- ML model improvements

#### 6. **Technical Risk Explanation**
- Technical details of why this is dangerous
- Detailed attack vector analysis
- Potential impact assessment
- Business risk evaluation

#### 7. **IP Blocking Recommendation**
- Should this IP be permanently blocked?
- Or rate-limited? (with specific limits)
- Whitelist considerations
- Geo-blocking recommendations

#### 8. **Infrastructure Hardening Rules**
- NGINX configuration (exact nginx.conf snippets)
- UFW firewall rules (exact commands)
- iptables rules (exact syntax)
- CloudFlare / WAF rules
- Fail2ban configuration

#### 9. **API-Level Hardening Suggestions**
- Input sanitization code
- Request validation schemas
- Authentication improvements
- Authorization checks
- API versioning recommendations

---

## 📝 How It Works

### Automatic AI Resolution Generation

When an anomaly is detected with `risk_score > 0.7`:

1. **Anomaly Classification**
   - System classifies anomaly type: `sql_injection`, `xss_attack`, `traffic_burst`, etc.
   
2. **Severity Determination**
   - `CRITICAL`: risk_score >= 0.9
   - `HIGH`: risk_score >= 0.8
   - `MEDIUM`: risk_score >= 0.7
   - `LOW`: risk_score < 0.7

3. **AI Prompt Construction**
   - Detailed prompt sent to OpenAI GPT-4
   - Includes anomaly context, endpoint, IP, risk metrics
   
4. **Response Generation**
   - OpenAI generates extremely detailed response
   - All 9 sections populated with production-ready content
   - Specific commands, configurations, code snippets
   
5. **Response Parsing**
   - AI response parsed into structured format
   - Attached to detection result
   - Returned via API

### API Integration

The AI resolution is included in the detection response:

```json
{
  "ip": "192.168.1.100",
  "risk_score": 0.85,
  "is_anomaly": true,
  "ai_resolution": {
    "anomaly_type": "sql_injection",
    "severity": "HIGH",
    "generated_by": "OpenAI GPT-4",
    "timestamp": "2024-02-15T10:30:00",
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
    },
    "full_response": "Complete AI-generated text..."
  }
}
```

---

## 🎲 Simulation Mode IP Tracking

### New Capability

IP tracking from real-time detection **NOW WORKS** in simulation mode!

### How It Works

#### During Simulation

When simulation traffic is generated:

1. **Request Generation**
   - Simulation engine creates request with `ip_address`, `endpoint`, `method`, etc.
   
2. **Real-Time Detection Call**
   ```python
   realtime_detector.track_simulation_request(
       ip_address="SIM-192",
       endpoint="/sim/login",
       method="POST",
       response_time_ms=250.5,
       status_code=200,
       payload_size=1024
   )
   ```

3. **Risk Calculation**
   - ML models analyze the simulated request
   - XGBoost + Autoencoder calculate risk score
   - Same deterministic scoring as live mode

4. **IP Profile Update**
   - IP tracked with `is_simulation=True` flag
   - Profile updated with anomaly counts
   - Average risk calculated
   - **NOT BLOCKED** (simulation IPs never auto-blocked)

5. **Statistics Collection**
   - All simulation IPs tracked separately
   - Can query simulation IP stats via API
   - Combined stats show live + simulation

### Key Differences from Live Mode

| Feature | Live Mode | Simulation Mode |
|---------|-----------|-----------------|
| IP Blocking | ✅ Auto-blocks risky IPs | ❌ Never blocks |
| Tracking | ✅ Tracked | ✅ Tracked |
| Risk Scoring | ✅ ML-based | ✅ ML-based (same) |
| AI Resolutions | ✅ Generated | ✅ Generated |
| Profile Persistence | ✅ Persistent | ✅ Persistent |
| Flag | `is_simulation=False` | `is_simulation=True` |

---

## 🔌 New API Endpoints

### 1. Get Simulation IP Stats
```http
GET /api/security/simulation/ip-stats
```

**Response:**
```json
{
  "summary": {
    "total_simulation_ips": 150,
    "total_simulation_requests": 50000,
    "total_simulation_anomalies": 2500,
    "anomaly_rate": 5.0
  },
  "top_risky_simulation_ips": [
    {
      "ip": "SIM-45",
      "avg_risk": 0.8234,
      "total_requests": 450,
      "anomaly_count": 125,
      "last_seen": "2024-02-15T10:30:00"
    }
  ]
}
```

### 2. Get Combined IP Stats (Live + Simulation)
```http
GET /api/security/combined/ip-stats
```

**Response:**
```json
{
  "live_mode": {
    "total_ips": 50,
    "blocked_ips": 3,
    "total_requests": 10000,
    "total_anomalies": 250,
    "anomaly_rate": 2.5
  },
  "simulation_mode": {
    "total_ips": 150,
    "total_requests": 50000,
    "total_anomalies": 2500,
    "anomaly_rate": 5.0
  },
  "total": {
    "total_ips": 200,
    "total_requests": 60000,
    "total_anomalies": 2750
  }
}
```

### 3. Existing Real-Time Stats (Enhanced)
```http
GET /api/security/realtime/stats
```

Now includes simulation IPs in the overall tracking.

---

## 🔧 Configuration

### OpenAI API Key Setup

The OpenAI API key is configured in `app.py`:

```python
OPENAI_API_KEY = "sk-proj-..."
```

**To Change the API Key:**
1. Open `backend/app.py`
2. Find line ~73: `OPENAI_API_KEY = "..."`
3. Replace with your key
4. Restart backend

### AI Resolution Engine Parameters

Located in `backend/ai_resolution_engine.py`:

```python
# OpenAI Model Configuration
model="gpt-4"
temperature=0.3  # Lower = more consistent
max_tokens=3000  # Maximum response length
```

### Detection Thresholds

Located in `backend/security/realtime_detection.py`:

```python
class RealTimeAnomalyDetector:
    RISK_THRESHOLD = 0.7  # Anomaly threshold
    BLOCK_AVG_RISK_THRESHOLD = 0.8  # Auto-block threshold
    BLOCK_ANOMALY_COUNT_THRESHOLD = 5  # Min anomalies before block
    XGB_WEIGHT = 0.6  # XGBoost weight
    AE_WEIGHT = 0.4  # Autoencoder weight
```

---

## 📊 Monitoring & Visibility

### During Simulation

**Backend Logs Show:**
```
SIMULATION DETECTION | IP: SIM-45 | Endpoint: /sim/login | 
RISK: 0.8234 | Anomaly: True | 
Profile: Avg=0.8234, Count=125/450
```

**AI Resolution Logs:**
```
✅ AI Resolution generated for sql_injection (HIGH)
```

### API Monitoring

**Poll these endpoints for live updates:**
- `/api/security/simulation/ip-stats` - Simulation IP tracking
- `/api/security/realtime/stats` - Overall detection stats
- `/api/security/combined/ip-stats` - Live + Simulation combined

---

## 🚀 Usage Examples

### Example 1: Start Simulation with IP Tracking

```bash
# Start simulation (backend automatically tracks IPs)
curl -X POST http://localhost:8000/api/simulation/start \
  -H "Content-Type: application/json" \
  -d '{
    "duration_seconds": 120,
    "requests_per_second": 200
  }'

# Check simulation IP stats in real-time
curl http://localhost:8000/api/security/simulation/ip-stats
```

### Example 2: View AI Resolution for Anomaly

When an anomaly is detected, check the detection result:

```bash
# Detection result includes AI resolution
curl http://localhost:8000/api/security/realtime/stats
```

Response includes:
```json
{
  "ai_resolution": {
    "resolution_strategy": {
      "immediate_containment": "1. Block IP immediately: sudo ufw deny from 192.168.1.100...",
      "network_mitigation": "# UFW Rules\nsudo ufw limit 80/tcp...",
      "infrastructure_rules": "# NGINX Configuration\nlocation /api {...}",
      ...
    }
  }
}
```

---

## 🧪 Testing

### Test AI Resolution Generation

```bash
# Trigger anomaly detection on live endpoint
curl http://localhost:8000/login \
  -H "X-Forwarded-For: 192.168.1.100" \
  -d "username=admin' OR '1'='1"

# Check if AI resolution was generated
curl http://localhost:8000/api/security/realtime/ip/192.168.1.100
```

### Test Simulation IP Tracking

```bash
# Start simulation
curl -X POST http://localhost:8000/api/simulation/start \
  -d '{"duration_seconds": 60, "requests_per_second": 100}'

# Wait 10 seconds, then check simulation IP stats
sleep 10
curl http://localhost:8000/api/security/simulation/ip-stats

# Should show tracked simulation IPs with risk scores
```

---

## 📁 Files Modified/Created

### New Files
- `backend/ai_resolution_engine.py` - AI-powered resolution system (398 lines)

### Modified Files
- `backend/security/realtime_detection.py`:
  - Added `track_simulation_request()` method
  - Added `get_simulation_ip_stats()` method
  - Added `is_simulation` parameter to `detect_anomaly()`
  - Added AI resolution generation
  - Updated `update_ip_profile()` to track simulation flag
  
- `backend/app.py`:
  - Added OpenAI API key configuration
  - Integrated AI resolution in detection initialization
  - Added `track_simulation_request()` calls in simulation loop
  - Added 2 new endpoints: `/api/security/simulation/ip-stats`, `/api/security/combined/ip-stats`

---

## ⚠️ Important Notes

### AI Resolution Costs

- **Each anomaly detection** generates an OpenAI API call
- GPT-4 costs: ~$0.03 per 1K tokens (input) + ~$0.06 per 1K tokens (output)
- Average cost per resolution: **~$0.10 - $0.20**
- High traffic = high API costs
- **Recommendation**: Monitor OpenAI usage dashboard

### Fallback Behavior

If OpenAI API is unavailable or fails:
- System uses basic fallback resolutions
- Detection continues normally
- No errors thrown to user
- Logs show: `"AI resolution unavailable - using fallback"`

### Simulation IP Blocking

- **Simulation IPs are NEVER auto-blocked**
- This is intentional to avoid interfering with simulation
- They are still tracked and risk-scored
- Their profiles persist for analysis

---

## 🎯 Key Benefits

### For Security Teams
✅ **Production-Ready Mitigation Strategies** - No guesswork, exact commands to execute  
✅ **Forensic Queries** - Know exactly what logs to check  
✅ **Firewall Rules** - Copy-paste ready iptables/UFW rules  
✅ **Risk Assessment** - Technical explanation of threat impact  

### For DevOps Teams
✅ **Infrastructure Hardening** - Nginx, WAF, CDN configurations  
✅ **API Hardening** - Code-level security improvements  
✅ **Monitoring Improvements** - Recommendations for better detection  

### For Management
✅ **Business Risk Explanation** - Understand impact in business terms  
✅ **Decision Support** - Clear block/rate-limit recommendations  
✅ **Audit Trail** - AI-generated documentation for compliance  

### For Simulation Testing
✅ **IP Tracking Visibility** - See which simulated IPs are high-risk  
✅ **Real-Time Monitoring** - Track simulation anomaly detection live  
✅ **Validation** - Verify detection system works correctly  

---

## 🔮 Future Enhancements

Potential improvements:
- Custom AI prompts per anomaly type
- Resolution history tracking
- AI-powered automated remediation
- Integration with ticketing systems (Jira, ServiceNow)
- Resolution quality feedback loop
- Cost optimization (caching similar resolutions)

---

## 📞 Support

For issues or questions:
1. Check backend logs for AI resolution generation
2. Verify OpenAI API key is valid
3. Monitor OpenAI API usage/quotas
4. Check `/api/security/simulation/ip-stats` for simulation tracking

---

**Last Updated**: February 2024  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
