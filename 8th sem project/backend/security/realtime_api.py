"""
Real-time Anomaly Detection API
--------------------------------
FastAPI application with automatic anomaly detection middleware.

Usage:
    python realtime_api.py
    
    or
    
    uvicorn security.realtime_api:app --host 0.0.0.0 --port 8002 --reload

Author: Traffic Monitoring System
Date: February 2026
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from .realtime_detection import setup_realtime_detection, get_detector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Real-time Anomaly Detection API",
    description="Production-ready API with automatic anomaly detection and IP blocking",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup real-time anomaly detection middleware
# This will automatically inspect ALL requests
detector = setup_realtime_detection(app, models_dir="../models")


# ============================================================================
# Pydantic Models
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class PaymentRequest(BaseModel):
    amount: float
    card_number: str
    cvv: str


class SearchQuery(BaseModel):
    query: str
    filters: Optional[dict] = None


# ============================================================================
# API Endpoints (Protected by Middleware)
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Real-time Anomaly Detection API",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Automatic anomaly detection",
            "IP profiling and tracking",
            "Automatic IP blocking",
            "XGBoost + Autoencoder ensemble",
            "Real-time risk scoring"
        ],
        "endpoints": {
            "health": "GET /health",
            "login": "POST /api/login",
            "payment": "POST /api/payment",
            "search": "POST /api/search",
            "security_stats": "GET /security/stats",
            "blocked_ips": "GET /security/blocked-ips"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    profiles = detector.get_all_profiles()
    blocked = detector.get_blocked_ips()
    
    return {
        "status": "healthy",
        "models_loaded": detector.models_loaded,
        "statistics": {
            "total_ips_tracked": len(profiles),
            "blocked_ips": len(blocked),
            "active_ips": len(profiles) - len(blocked)
        }
    }


@app.post("/api/login")
async def login(request: Request, credentials: LoginRequest):
    """
    Login endpoint - automatically protected by anomaly detection.
    
    The middleware will:
    1. Extract IP and request data
    2. Run ML models to calculate risk
    3. Update IP profile
    4. Block IP if suspicious
    5. Return 403 if blocked
    """
    # Access detection results from request state
    detection = getattr(request.state, 'anomaly_detection', None)
    
    # Simulate login logic
    response = {
        "status": "success",
        "message": "Login processed",
        "username": credentials.username
    }
    
    # Include detection info if available
    if detection:
        response["security"] = {
            "risk_score": detection.get('risk_score'),
            "is_anomaly": detection.get('is_anomaly'),
            "request_count": detection.get('profile', {}).get('total_requests')
        }
    
    return response


@app.post("/api/payment")
async def process_payment(request: Request, payment: PaymentRequest):
    """Payment endpoint - protected by anomaly detection."""
    detection = getattr(request.state, 'anomaly_detection', None)
    
    return {
        "status": "success",
        "message": "Payment processed",
        "amount": payment.amount,
        "security": {
            "risk_score": detection.get('risk_score') if detection else None,
            "verified": True
        }
    }


@app.post("/api/search")
async def search(request: Request, query: SearchQuery):
    """Search endpoint - protected by anomaly detection."""
    detection = getattr(request.state, 'anomaly_detection', None)
    
    return {
        "status": "success",
        "query": query.query,
        "results": [],
        "security": {
            "risk_score": detection.get('risk_score') if detection else None
        }
    }


# ============================================================================
# Security Management Endpoints
# ============================================================================

@app.get("/security/stats")
async def get_security_stats():
    """Get comprehensive security statistics."""
    profiles = detector.get_all_profiles()
    blocked = detector.get_blocked_ips()
    
    # Calculate statistics
    total_requests = sum(p['total_requests'] for p in profiles.values())
    total_anomalies = sum(p['anomaly_count'] for p in profiles.values())
    
    # Get top risky IPs
    risky_ips = sorted(
        profiles.items(),
        key=lambda x: x[1]['avg_risk'],
        reverse=True
    )[:10]
    
    return {
        "summary": {
            "total_ips_tracked": len(profiles),
            "blocked_ips": len(blocked),
            "total_requests": total_requests,
            "total_anomalies": total_anomalies,
            "anomaly_rate": round(total_anomalies / total_requests * 100, 2) if total_requests > 0 else 0
        },
        "top_risky_ips": [
            {
                "ip": ip,
                "avg_risk": round(profile['avg_risk'], 4),
                "total_requests": profile['total_requests'],
                "anomaly_count": profile['anomaly_count'],
                "blocked": profile['blocked']
            }
            for ip, profile in risky_ips
        ],
        "configuration": {
            "risk_threshold": detector.RISK_THRESHOLD,
            "block_avg_risk_threshold": detector.BLOCK_AVG_RISK_THRESHOLD,
            "block_anomaly_count_threshold": detector.BLOCK_ANOMALY_COUNT_THRESHOLD,
            "xgb_weight": detector.XGB_WEIGHT,
            "ae_weight": detector.AE_WEIGHT
        }
    }


@app.get("/security/blocked-ips")
async def get_blocked_ips():
    """Get list of all blocked IPs with their profiles."""
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
                "avg_risk": round(profile['avg_risk'], 4),
                "last_seen": profile['last_seen']
            })
    
    return {
        "count": len(blocked),
        "blocked_ips": blocked_details
    }


@app.get("/security/ip/{ip_address}")
async def get_ip_profile(ip_address: str):
    """Get detailed profile for a specific IP."""
    profiles = detector.get_all_profiles()
    
    if ip_address not in profiles:
        return JSONResponse(
            status_code=404,
            content={"error": "IP not found in tracking system"}
        )
    
    profile = profiles[ip_address]
    return {
        "ip": ip_address,
        "profile": {
            "total_requests": profile['total_requests'],
            "anomaly_count": profile['anomaly_count'],
            "avg_risk": round(profile['avg_risk'], 4),
            "total_risk": round(profile['total_risk'], 4),
            "last_seen": profile['last_seen'],
            "blocked": profile['blocked']
        }
    }


@app.post("/security/unblock/{ip_address}")
async def unblock_ip(ip_address: str):
    """Manually unblock an IP address."""
    success = detector.unblock_ip(ip_address)
    
    if success:
        return {
            "status": "success",
            "message": f"IP {ip_address} has been unblocked",
            "ip": ip_address
        }
    else:
        return JSONResponse(
            status_code=400,
            content={
                "error": "IP not blocked",
                "message": f"IP {ip_address} is not currently blocked"
            }
        )


@app.delete("/security/reset")
async def reset_security_system():
    """
    Reset the entire security system (clear all profiles and blocks).
    
    ⚠️ USE WITH CAUTION - This clears all tracking data
    """
    with detector._lock:
        detector.ip_profiles.clear()
        detector.blocked_ips.clear()
    
    logger.warning("🔄 Security system reset - all profiles and blocks cleared")
    
    return {
        "status": "success",
        "message": "Security system has been reset",
        "warning": "All IP profiles and blocks have been cleared"
    }


# ============================================================================
# Application Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info("=" * 60)
    logger.info("Real-time Anomaly Detection API Starting...")
    logger.info("=" * 60)
    logger.info(f"Models Loaded: {detector.models_loaded}")
    logger.info(f"Detection Active: {detector.models_loaded}")
    logger.info("=" * 60)
    logger.info("API is ready to accept requests")
    logger.info("All endpoints are protected by real-time anomaly detection")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    profiles = detector.get_all_profiles()
    blocked = detector.get_blocked_ips()
    
    logger.info("=" * 60)
    logger.info("Shutting down Real-time Anomaly Detection API")
    logger.info(f"Final Statistics:")
    logger.info(f"  - Total IPs Tracked: {len(profiles)}")
    logger.info(f"  - Blocked IPs: {len(blocked)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("Real-time Anomaly Detection API")
    print("=" * 60)
    print("\nStarting server on http://0.0.0.0:8002")
    print("\nEndpoints:")
    print("  • Interactive Docs: http://localhost:8002/docs")
    print("  • Health Check: http://localhost:8002/health")
    print("  • Security Stats: http://localhost:8002/security/stats")
    print("\n" + "=" * 60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
