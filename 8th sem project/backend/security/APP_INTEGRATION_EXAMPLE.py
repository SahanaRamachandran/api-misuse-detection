"""
Integration Guide: Add Real-time Anomaly Detection to Main Backend
====================================================================

This guide shows how to integrate the RealTimeAnomalyDetector middleware
with your existing app.py FastAPI application.

Author: Traffic Monitoring System
Date: February 2026
"""

# ============================================================================
# OPTION 1: Quick Integration (Recommended)
# ============================================================================
# Add these lines to your app.py:

from security.realtime_detection import setup_realtime_detection

# After creating your FastAPI app:
app = FastAPI()

# Add real-time detection middleware (ONE LINE!)
detector = setup_realtime_detection(app, models_dir="models")

# That's it! All routes are now protected.


# ============================================================================
# OPTION 2: Manual Middleware Registration
# ============================================================================

from security.realtime_detection import RealTimeAnomalyMiddleware

app = FastAPI()

# Add middleware
app.add_middleware(
    RealTimeAnomalyMiddleware,
    models_dir="models"
)


# ============================================================================
# COMPLETE INTEGRATION EXAMPLE
# ============================================================================

"""
File: app.py (Modified to include real-time detection)
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from security.realtime_detection import setup_realtime_detection, get_detector
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="Traffic Monitoring API",
    description="Real-time traffic monitoring with anomaly detection",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 🛡️ ADD REAL-TIME ANOMALY DETECTION MIDDLEWARE
# ============================================================================
detector = setup_realtime_detection(app, models_dir="models")
logger.info("✅ Real-time anomaly detection middleware enabled")

# ============================================================================
# ACCESSING DETECTION RESULTS IN YOUR ROUTES
# ============================================================================

@app.post("/api/login")
async def login(request: Request, credentials: dict):
    # Get detection results
    detection = getattr(request.state, 'anomaly_detection', None)
    
    if detection:
        risk_score = detection['risk_score']
        is_anomaly = detection['is_anomaly']
        
        # Log high-risk requests
        if is_anomaly:
            logger.warning(f"High-risk login attempt: {risk_score}")
    
    return {"status": "success"}


# ============================================================================
# NEW SECURITY ENDPOINTS
# ============================================================================

@app.get("/api/security/stats")
async def security_stats():
    """Get real-time security statistics."""
    detector = get_detector()
    
    if not detector:
        return {"error": "Detector not initialized"}
    
    profiles = detector.get_all_profiles()
    blocked = detector.get_blocked_ips()
    
    total_requests = sum(p['total_requests'] for p in profiles.values())
    total_anomalies = sum(p['anomaly_count'] for p in profiles.values())
    
    return {
        "summary": {
            "total_ips": len(profiles),
            "blocked_ips": len(blocked),
            "total_requests": total_requests,
            "total_anomalies": total_anomalies
        }
    }


@app.get("/api/security/blocked-ips")
async def get_blocked_ips():
    """Get all blocked IPs."""
    detector = get_detector()
    
    if not detector:
        return {"error": "Detector not initialized"}
    
    blocked = detector.get_blocked_ips()
    profiles = detector.get_all_profiles()
    
    blocked_details = []
    for ip in blocked:
        if ip in profiles:
            profile = profiles[ip]
            blocked_details.append({
                "ip": ip,
                "total_requests": profile['total_requests'],
                "anomaly_count": profile['anomaly_count'],
                "avg_risk": round(profile['avg_risk'], 4)
            })
    
    return {
        "count": len(blocked),
        "blocked_ips": blocked_details
    }


@app.post("/api/security/unblock/{ip_address}")
async def unblock_ip(ip_address: str):
    """Manually unblock an IP."""
    detector = get_detector()
    
    if not detector:
        return {"error": "Detector not initialized"}
    
    success = detector.unblock_ip(ip_address)
    
    if success:
        return {
            "status": "success",
            "message": f"IP {ip_address} has been unblocked"
        }
    else:
        return {
            "error": "IP not blocked"
        }


# ============================================================================
# NOTES & BEST PRACTICES
# ============================================================================

"""
✅ Best Practices:

1. **Middleware Order**
   - Add RealTimeAnomalyMiddleware AFTER CORSMiddleware

2. **Model Loading**
   - Models are loaded once at startup (singleton pattern)
   - If models fail to load, middleware runs in "fail-open" mode

3. **Thread Safety**
   - All IP profile operations are thread-safe
   - Safe for production use with multiple workers

4. **Logging**
   - All anomalies and blocks are logged
   - Monitor logs for security events

5. **Testing**
   - Test with TEST_REALTIME_API.ps1 script
   - Verify deterministic behavior
"""
