# Endpoint-to-Attack Mapping

This document shows which security attack is assigned to each endpoint in the system.

## Attack Types

The system detects three types of security attacks:

1. **SQL Injection** - Database compromise attempts
   - Severity: CRITICAL
   - Impact Score: 0.95
   - Failure Probability: 80%

2. **DDoS Attack** - Distributed Denial of Service
   - Severity: CRITICAL
   - Impact Score: 0.98
   - Failure Probability: 90%

3. **XSS Attack** - Cross-Site Scripting
   - Severity: HIGH
   - Impact Score: 0.85
   - Failure Probability: 65%

## Endpoint Mappings

### SQL Injection Endpoints
These endpoints will inject SQL injection attack patterns:
- `/sim/login` - Login authentication with SQL injection attempts
- `/sim/payment` - Payment processing with SQL injection
- `/sim/signup` - User registration with SQL injection
- `/sim/api/posts` - Posts API with SQL injection

**Attack Patterns:**
- `' OR '1'='1`
- `'; DROP TABLE users--`
- `' UNION SELECT NULL--`
- `admin'--`
- `1' AND '1'='1`

### DDoS Attack Endpoints
These endpoints will inject high-volume traffic patterns:
- `/sim/search` - Search functionality under DDoS load
- `/sim/api/users` - Users API with DDoS traffic

**Attack Characteristics:**
- 50x normal traffic volume
- 1000+ concurrent connections
- 3x slower response times
- 30% request failure rate

### XSS Attack Endpoints
These endpoints will inject cross-site scripting patterns:
- `/sim/profile` - User profile with XSS injection
- `/sim/logout` - Logout process with XSS
- `/sim/api/data` - Data API with XSS attempts
- `/sim/api/comments` - Comments API with XSS

**Attack Patterns:**
- `<script>alert("XSS")</script>`
- `<img src=x onerror=alert("XSS")>`
- `javascript:alert("XSS")`
- `<iframe src="malicious.com">`
- `<body onload=alert("XSS")>`

## Testing Different Attacks

To test different attacks, use the simulation mode and access different endpoints:

```bash
# Test SQL Injection
curl http://localhost:8000/sim/login
curl http://localhost:8000/sim/payment

# Test DDoS Attack
curl http://localhost:8000/sim/search
curl http://localhost:8000/sim/api/users

# Test XSS Attack
curl http://localhost:8000/sim/profile
curl http://localhost:8000/sim/api/comments
```

## Model Integration

The system uses the following ML models to detect these attacks:

1. **XGBoost** (`xgboost.pkl` or `xgboost_model.pkl`)
   - HTTP request anomaly detection
   - Trained on CSIC 2010 dataset

2. **Autoencoder** (`model.weights.h5`)
   - Reconstruction-based anomaly detection
   - TensorFlow/Keras model

3. **Isolation Forest** (runtime trained)
   - Unsupervised anomaly detection
   - Real-time adaptation

4. **Random Forest** (runtime trained)
   - Failure probability prediction
   - Pattern classification

## How It Works

1. Each endpoint has **exactly one** attack type assigned
2. When simulation mode is active, attacks are injected into traffic
3. ML models analyze the traffic patterns
4. Anomalies are detected based on:
   - Malicious payload patterns
   - Traffic volume anomalies
   - Response time degradation
   - Status code patterns

The system ensures **different attacks for different endpoints** to provide comprehensive testing coverage.
