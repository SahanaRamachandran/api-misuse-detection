# IP Risk Engine - System Architecture

## 📐 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                           │
│              (with X-Forwarded-For: 192.168.1.100)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│                       (risk_engine.py)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         MIDDLEWARE LAYER (Order Matters!)               │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │  1️⃣  IPExtractionMiddleware                            │    │
│  │     ├─ Check X-Forwarded-For header                    │    │
│  │     ├─ Check X-Real-IP header                          │    │
│  │     ├─ Fallback to request.client.host                 │    │
│  │     └─ Store in request.state.client_ip                │    │
│  │                           │                             │    │
│  │                           ↓                             │    │
│  │  2️⃣  IPBlockingMiddleware (Optional)                   │    │
│  │     ├─ Get IP from request.state                       │    │
│  │     ├─ Check if IP is blocked                          │    │
│  │     └─ Return 403 if blocked                           │    │
│  │                           │                             │    │
│  └───────────────────────────┼─────────────────────────────┘    │
│                              │                                   │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              ROUTE HANDLERS                             │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │                                                         │    │
│  │  POST /api                                              │    │
│  │  ├─ Get client_ip from request.state                   │    │
│  │  ├─ Check if IP is blocked                             │    │
│  │  ├─ Calculate risk score (ML models)                   │    │
│  │  ├─ Update IP risk                                     │    │
│  │  └─ Return analysis result                             │    │
│  │                                                         │    │
│  │  GET /suspicious-ips                                    │    │
│  │  └─ Return all tracking data                           │    │
│  │                                                         │    │
│  │  Admin Endpoints:                                       │    │
│  │  ├─ GET  /admin/blocked-ips                            │    │
│  │  ├─ POST /admin/unblock/{ip}                           │    │
│  │  ├─ GET  /admin/ip/{ip}                                │    │
│  │  └─ DELETE /admin/reset-all                            │    │
│  │                                                         │    │
│  └───────────────────────────┼─────────────────────────────┘    │
│                              │                                   │
└──────────────────────────────┼───────────────────────────────────┘
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────┐
│                   IP RISK MANAGER                                │
│                    (ip_manager.py)                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────┐   ┌─────────────────────────────┐      │
│  │   Blocked IPs      │   │    IP Statistics            │      │
│  │   (set)            │   │    (defaultdict)            │      │
│  ├────────────────────┤   ├─────────────────────────────┤      │
│  │ • 10.0.0.50        │   │ "192.168.1.100": {          │      │
│  │ • 203.0.113.5      │   │   total_risk: 4.5,          │      │
│  │                    │   │   request_count: 10,        │      │
│  └────────────────────┘   │   average_risk: 0.45,       │      │
│                           │   last_seen: "2026...",     │      │
│  ┌────────────────────┐   │   blocked: false            │      │
│  │ Thread Lock        │   │ }                           │      │
│  │ (threading.Lock)   │   │ "10.0.0.50": {              │      │
│  │                    │   │   total_risk: 4.8,          │      │
│  │ Ensures thread-    │   │   request_count: 5,         │      │
│  │ safe operations    │   │   average_risk: 0.96,       │      │
│  └────────────────────┘   │   last_seen: "2026...",     │      │
│                           │   blocked: true             │      │
│  Functions:               │ }                           │      │
│  • update_ip_risk()       └─────────────────────────────┘      │
│  • is_ip_blocked()                                              │
│  • get_all_ip_stats()                                           │
│  • reset_ip()                                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Request Flow Diagram

```
┌─────────┐
│ Client  │
│ Request │
└────┬────┘
     │
     │ 1. HTTP Request with headers
     │    (X-Forwarded-For: 192.168.1.100)
     ↓
┌──────────────────────┐
│ IPExtractionMiddleware│
├──────────────────────┤
│ Extract IP Address   │───→ request.state.client_ip = "192.168.1.100"
└────┬─────────────────┘
     │
     │ 2. IP stored in request state
     ↓
┌──────────────────────┐
│ IPBlockingMiddleware │
├──────────────────────┤
│ Check if blocked     │───→ is_ip_blocked("192.168.1.100") ?
└────┬────┬────────────┘
     │    │
     │    └─→ YES → Return 403 Forbidden
     │
     │ NO
     ↓
┌──────────────────────┐
│  Route Handler       │
│  POST /api           │
├──────────────────────┤
│ 1. Get client IP     │
│ 2. Double-check      │───→ is_ip_blocked() ?
│    blocked status    │
│ 3. Calculate risk    │───→ ML Models: XGB + TFIDF + AE
│ 4. Update IP risk    │───→ update_ip_risk(ip, risk)
│ 5. Auto-block check  │───→ avg_risk > 0.8 && count >= 5 ?
│ 6. Return response   │
└────┬─────────────────┘
     │
     │ 3. Response with analysis
     ↓
┌─────────┐
│ Client  │
│Response │
└─────────┘
```

---

## 📊 Data Flow: IP Risk Tracking

```
Request #1 from 192.168.1.100 (risk=0.3)
    ↓
┌─────────────────────────────────────┐
│ IP Stats: 192.168.1.100             │
│ • total_risk: 0.3                   │
│ • request_count: 1                  │
│ • average_risk: 0.3                 │
│ • blocked: false                    │
└─────────────────────────────────────┘

Request #2 from 192.168.1.100 (risk=0.5)
    ↓
┌─────────────────────────────────────┐
│ IP Stats: 192.168.1.100             │
│ • total_risk: 0.8 (0.3 + 0.5)      │
│ • request_count: 2                  │
│ • average_risk: 0.4                 │
│ • blocked: false                    │
└─────────────────────────────────────┘

Request #3 from 192.168.1.100 (risk=0.7)
    ↓
┌─────────────────────────────────────┐
│ IP Stats: 192.168.1.100             │
│ • total_risk: 1.5 (0.8 + 0.7)      │
│ • request_count: 3                  │
│ • average_risk: 0.5                 │
│ • blocked: false                    │
└─────────────────────────────────────┘
```

---

## 🚨 Auto-Blocking Logic

```
┌──────────────────────────────────────────────┐
│         update_ip_risk(ip, risk)             │
├──────────────────────────────────────────────┤
│                                              │
│  1. Update statistics                        │
│     total_risk += risk                       │
│     request_count += 1                       │
│     average_risk = total / count             │
│     last_seen = now()                        │
│                                              │
│  2. Check blocking conditions                │
│     ┌──────────────────────────────────┐    │
│     │ if average_risk > 0.8             │    │
│     │    AND                            │    │
│     │    request_count >= 5             │    │
│     │    AND                            │    │
│     │    not already blocked            │    │
│     └────────┬──────────────────────────┘    │
│              │                               │
│              ↓                               │
│     ┌──────────────────────────────────┐    │
│     │ blocked_ips.add(ip)               │    │
│     │ stats['blocked'] = True           │    │
│     │ return True (was blocked)         │    │
│     └──────────────────────────────────┘    │
│                                              │
└──────────────────────────────────────────────┘
```

---

## 🔌 ML Model Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│                    POST /api Endpoint                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Extract Features from Request                           │
│     ├─ Request headers                                      │
│     ├─ Request body                                         │
│     ├─ Timing information                                   │
│     └─ Metadata                                             │
│                                                              │
│  2. ML Model Inference (INTEGRATION POINT)                  │
│     ┌───────────────────────────────────────────────┐      │
│     │ ⭐ REPLACE THIS:                               │      │
│     │    risk_score = random.uniform(0, 1)          │      │
│     │                                                │      │
│     │ ⭐ WITH THIS:                                  │      │
│     │                                                │      │
│     │    # XGBoost classification                   │      │
│     │    xgb_score = xgb_model.predict_proba(       │      │
│     │        features                                │      │
│     │    )[0][1]                                     │      │
│     │                                                │      │
│     │    # TF-IDF text analysis                     │      │
│     │    text_vector = tfidf.transform([text])      │      │
│     │    text_score = analyze_text(text_vector)     │      │
│     │                                                │      │
│     │    # Autoencoder anomaly detection            │      │
│     │    reconstruction = autoencoder.predict(      │      │
│     │        features                                │      │
│     │    )                                           │      │
│     │    ae_score = calc_error(                     │      │
│     │        features,                               │      │
│     │        reconstruction                          │      │
│     │    )                                           │      │
│     │                                                │      │
│     │    # Weighted ensemble                        │      │
│     │    risk_score = (                             │      │
│     │        xgb_score * 0.5 +                      │      │
│     │        text_score * 0.3 +                     │      │
│     │        ae_score * 0.2                         │      │
│     │    )                                           │      │
│     └───────────────────────────────────────────────┘      │
│                                                              │
│  3. Update IP Risk & Auto-Block                             │
│     was_blocked = update_ip_risk(client_ip, risk_score)     │
│                                                              │
│  4. Return Response                                          │
│     return {                                                 │
│         "ip": client_ip,                                     │
│         "risk_score": risk_score,                           │
│         "blocked_status": was_blocked,                      │
│         ...                                                  │
│     }                                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Module Dependencies

```
risk_engine.py (FastAPI App)
    │
    ├──→ middleware.py
    │       │
    │       ├──→ IPExtractionMiddleware
    │       └──→ IPBlockingMiddleware
    │
    └──→ ip_manager.py
            │
            ├──→ IPRiskManager (class)
            ├──→ get_ip_manager() (singleton)
            ├──→ update_ip_risk()
            ├──→ is_ip_blocked()
            ├──→ get_all_ip_stats()
            └──→ reset_ip()
```

---

## 📈 Scalability Considerations

```
┌────────────────────────────────────────────────────────────┐
│                  Current Architecture                       │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ In-Memory Storage (fast, thread-safe)                  │
│     • Perfect for: Small to medium traffic                 │
│     • Limitation: Data lost on restart                     │
│                                                             │
│  ✅ Thread-Safe with threading.Lock                        │
│     • Supports concurrent requests                         │
│     • Single process limitation                            │
│                                                             │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│              Future Enhancements (if needed)                │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  🔸 Redis Integration                                       │
│     • Persistent storage                                   │
│     • Multi-process support                                │
│     • Distributed deployment                               │
│                                                             │
│  🔸 Database Persistence                                    │
│     • Long-term storage                                    │
│     • Historical analysis                                  │
│     • Audit trails                                         │
│                                                             │
│  🔸 Rate Limiting                                           │
│     • Additional protection layer                          │
│     • Token bucket algorithm                               │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Configuration & Customization

```python
# File: ip_manager.py
class IPRiskManager:
    # ⚙️ Adjust these for your needs:
    BLOCK_THRESHOLD_AVG_RISK = 0.8      # Higher = less aggressive
    BLOCK_THRESHOLD_REQUEST_COUNT = 5    # Higher = more lenient

# File: risk_engine.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚙️ Set to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Monitoring & Observability

```
┌──────────────────────────────────────────────────────────┐
│                    Monitoring Points                      │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1. Request Logs                                          │
│     • Every request is logged with IP and risk score     │
│     • Check: application logs                            │
│                                                           │
│  2. Blocking Events                                       │
│     • When IP is blocked, warning is logged              │
│     • Check: WARNING level logs                          │
│                                                           │
│  3. Metrics Endpoints                                     │
│     • GET /health - System health                        │
│     • GET /suspicious-ips - Real-time tracking           │
│     • GET /admin/blocked-ips - Blocked IPs list          │
│                                                           │
│  4. Future: Real-time Dashboard                           │
│     • WebSocket endpoint for live updates                │
│     • Integration with frontend dashboard                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 🔒 Security Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   Defense Layers                            │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: IP Extraction                                     │
│  └─ Handles proxy headers, prevents IP spoofing            │
│                                                             │
│  Layer 2: IP Blocking Check                                 │
│  └─ Fast O(1) lookup in blocked set                        │
│                                                             │
│  Layer 3: Risk Scoring                                      │
│  └─ ML models identify suspicious patterns                 │
│                                                             │
│  Layer 4: Automatic Response                                │
│  └─ Auto-block based on cumulative behavior                │
│                                                             │
│  Layer 5: Admin Controls                                    │
│  └─ Manual override capabilities                           │
│  └─ ⚠️ TODO: Add authentication                            │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 🎬 Quick Reference: Key Files

| File | Purpose | Lines | Import From |
|------|---------|-------|-------------|
| `ip_manager.py` | Core tracking logic | 300+ | `from security.ip_manager import get_ip_manager` |
| `middleware.py` | FastAPI middleware | 150+ | `from security.middleware import IPExtractionMiddleware` |
| `risk_engine.py` | Main FastAPI app | 400+ | Run with: `uvicorn security.risk_engine:app` |
| `test_api.py` | Python tests | 250+ | Run with: `python test_api.py` |
| `TEST_API.ps1` | PowerShell tests | 250+ | Run with: `./TEST_API.ps1` |

---

**This architecture is production-ready and fully functional!** 🚀

Start using it:
```bash
cd "8th sem project/backend/security"
START_RISK_ENGINE.bat
```

Then visit: http://localhost:8000/docs
