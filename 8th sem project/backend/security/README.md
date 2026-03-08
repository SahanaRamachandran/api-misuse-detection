# IP Risk Manager - Security Module

Production-ready IP tracking and risk management system for FastAPI applications.

## 📋 Overview

The IP Risk Manager automatically tracks and scores client IP addresses based on risk levels. When an IP exhibits suspicious behavior patterns, it is automatically blocked from accessing your API.

## ✅ Features

- **Thread-safe operations** - Safe for concurrent FastAPI requests
- **Automatic blocking** - IPs blocked when average risk > 0.8 and request count ≥ 5
- **Real-time tracking** - Monitors total risk, request count, average risk, and last seen timestamp
- **Easy integration** - Drop-in middleware for FastAPI
- **No external dependencies** - Uses only Python standard library
- **Production-ready** - Comprehensive error handling and logging

## 📁 Module Structure

```
security/
├── __init__.py                      # Package initialization
├── ip_manager.py                    # Core IP risk management
├── fastapi_integration_example.py   # FastAPI integration examples
└── README.md                        # This file
```

## 🚀 Quick Start

### Basic Usage

```python
from security.ip_manager import get_ip_manager

# Get the global IP manager instance
manager = get_ip_manager()

# Update IP risk (returns True if IP was blocked)
was_blocked = manager.update_ip_risk('192.168.1.100', 0.85)

# Check if IP is blocked
if manager.is_ip_blocked('192.168.1.100'):
    print("IP is blocked!")

# Get stats for specific IP
stats = manager.get_ip_stats('192.168.1.100')
print(f"Average risk: {stats['average_risk']:.2f}")

# Reset an IP (unblock and clear stats)
manager.reset_ip('192.168.1.100')
```

### FastAPI Integration

```python
from fastapi import FastAPI, Request, HTTPException
from security.ip_manager import get_ip_manager, is_ip_blocked

app = FastAPI()
ip_manager = get_ip_manager()

@app.middleware("http")
async def ip_blocking_middleware(request: Request, call_next):
    """Block requests from flagged IPs"""
    client_ip = request.client.host
    
    if is_ip_blocked(client_ip):
        return JSONResponse(
            status_code=403,
            content={"error": "IP blocked due to suspicious activity"}
        )
    
    response = await call_next(request)
    return response

@app.post("/api/analyze")
async def analyze_request(request: Request):
    """Analyze request and update IP risk"""
    client_ip = request.client.host
    
    # Your ML model inference here
    risk_score = predict_risk(request)  # 0.0 to 1.0
    
    # Update risk and auto-block if needed
    was_blocked = ip_manager.update_ip_risk(client_ip, risk_score)
    
    if was_blocked:
        raise HTTPException(status_code=403, detail="IP blocked")
    
    return {"status": "ok", "risk": risk_score}
```

## 📊 Data Structure

Each tracked IP stores:

```python
{
    'total_risk': 4.5,              # Sum of all risk scores
    'request_count': 10,             # Number of requests
    'average_risk': 0.45,            # total_risk / request_count
    'last_seen': '2026-02-23T14:30:00.123456',  # ISO timestamp
    'blocked': False                 # Block status
}
```

## 🔒 Blocking Logic

An IP is automatically blocked when **BOTH** conditions are met:

1. **Average risk > 0.8** (configurable via `BLOCK_THRESHOLD_AVG_RISK`)
2. **Request count ≥ 5** (configurable via `BLOCK_THRESHOLD_REQUEST_COUNT`)

### Example Blocking Scenario

```python
# First 4 requests - not blocked (count < 5)
manager.update_ip_risk('10.0.0.1', 0.9)  # Avg: 0.9, Count: 1
manager.update_ip_risk('10.0.0.1', 0.9)  # Avg: 0.9, Count: 2
manager.update_ip_risk('10.0.0.1', 0.9)  # Avg: 0.9, Count: 3
manager.update_ip_risk('10.0.0.1', 0.9)  # Avg: 0.9, Count: 4

# 5th request - IP BLOCKED! (avg > 0.8 AND count >= 5)
was_blocked = manager.update_ip_risk('10.0.0.1', 0.9)
print(was_blocked)  # True
```

## 🛠️ API Reference

### Core Functions

#### `update_ip_risk(ip: str, risk: float) -> bool`
Update IP risk score and check for auto-block.

**Parameters:**
- `ip` (str): Client IP address
- `risk` (float): Risk score between 0.0 and 1.0

**Returns:**
- `bool`: True if IP was blocked by this update

**Raises:**
- `ValueError`: If IP is empty or risk not in [0.0, 1.0]

#### `is_ip_blocked(ip: str) -> bool`
Check if an IP is currently blocked.

**Parameters:**
- `ip` (str): IP address to check

**Returns:**
- `bool`: True if blocked

#### `get_all_ip_stats() -> dict`
Get statistics for all tracked IPs.

**Returns:**
- `dict`: Mapping of IP addresses to their statistics

#### `reset_ip(ip: str) -> None`
Reset and unblock a specific IP.

**Parameters:**
- `ip` (str): IP address to reset

### Additional Methods

#### `get_ip_stats(ip: str) -> Optional[dict]`
Get statistics for a specific IP.

#### `get_blocked_ips() -> set`
Get set of all blocked IPs.

#### `clear_all() -> None`
Clear all IP data and unblock all IPs (use with caution).

## 🧪 Testing

Run the built-in test suite:

```bash
cd backend/security
python ip_manager.py
```

Expected output:
```
IP Risk Manager - Demonstration
==================================================

Test Case 1: Normal Traffic
  Request 1: Risk=0.3, Blocked=False
  Request 2: Risk=0.3, Blocked=False
  ...
  Final Stats: Avg Risk=0.30, Count=10

Test Case 2: High Risk Traffic
  Request 1: Risk=0.9, Not blocked yet
  ...
  Request 5: Risk=0.9, ⚠️ IP BLOCKED!
  Final Stats: Avg Risk=0.90, Count=5, Blocked=True
```

## 🔧 Configuration

Modify blocking thresholds in `ip_manager.py`:

```python
class IPRiskManager:
    BLOCK_THRESHOLD_AVG_RISK = 0.8      # Change average risk threshold
    BLOCK_THRESHOLD_REQUEST_COUNT = 5    # Change minimum request count
```

## 📈 Integration with ML Models

When integrating with your XGBoost, TF-IDF, and Autoencoder models:

```python
from security.ip_manager import get_ip_manager
import joblib
from tensorflow import keras

# Load your models
xgb_model = joblib.load('models/xgb_model.pkl')
tfidf = joblib.load('models/tfidf.pkl')
autoencoder = keras.models.load_model('models/autoencoder.h5')

manager = get_ip_manager()

@app.post("/analyze")
async def analyze_traffic(request: Request):
    client_ip = request.client.host
    
    # Extract features from request
    features = extract_features(request)
    
    # Run ML models
    xgb_score = xgb_model.predict_proba(features)[0][1]
    text_features = tfidf.transform([request.body])
    autoencoder_loss = calculate_reconstruction_error(autoencoder, features)
    
    # Combine scores (example: weighted average)
    final_risk = (xgb_score * 0.5 + 
                  text_anomaly_score * 0.3 + 
                  autoencoder_loss * 0.2)
    
    # Update IP risk
    was_blocked = manager.update_ip_risk(client_ip, final_risk)
    
    return {"risk": final_risk, "blocked": was_blocked}
```

## 🔐 Security Best Practices

1. **Rate Limiting**: Use alongside rate limiting middleware
2. **Logging**: Log all block events for audit trails
3. **Monitoring**: Track blocked IPs in your dashboard
4. **Whitelist**: Implement IP whitelist for trusted sources
5. **Review**: Periodically review blocked IPs

## 📝 License

Part of the Traffic Monitoring System project.

## 🤝 Contributing

This module is production-ready and follows Python best practices:
- PEP 8 compliant
- Type hints for all public methods
- Comprehensive docstrings
- Thread-safe operations
- Error handling

---

**Ready to integrate!** 🚀

For questions or issues, refer to the main project documentation.
