"""
Risk Engine - FastAPI Application
----------------------------------
Production-ready FastAPI application for IP risk tracking and management.

Features:
- Automatic client IP extraction via middleware
- Real-time risk scoring and IP blocking
- Comprehensive API endpoints for monitoring
- Integration with ML models (ready for XGBoost, TF-IDF, Autoencoder)

Author: Traffic Monitoring System
Date: February 2026
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import random
import logging
from datetime import datetime

# Import custom modules
from .ip_manager import get_ip_manager, update_ip_risk, is_ip_blocked, get_all_ip_stats, reset_ip
from .middleware import IPExtractionMiddleware, IPBlockingMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="IP Risk Engine API",
    description="Production-ready API for IP risk tracking and automated blocking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Get global IP manager instance
ip_manager = get_ip_manager()

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add IP extraction middleware (MUST be first)
app.add_middleware(IPExtractionMiddleware)

# Add IP blocking middleware (runs after IP extraction)
# Note: Commenting out auto-blocking middleware to allow /api endpoint to handle blocking logic
# Uncomment below to enable automatic blocking before request processing
# app.add_middleware(IPBlockingMiddleware, ip_manager=ip_manager)


# ============================================================================
# PYDANTIC MODELS (Request/Response schemas)
# ============================================================================

class RiskAnalysisResponse(BaseModel):
    """Response model for risk analysis endpoint"""
    ip: str = Field(..., description="Client IP address")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Calculated risk score (0.0-1.0)")
    blocked_status: bool = Field(..., description="Whether IP is currently blocked")
    request_count: int = Field(..., description="Total requests from this IP")
    average_risk: float = Field(..., description="Average risk score for this IP")
    timestamp: str = Field(..., description="Timestamp of analysis")


class IPStatsResponse(BaseModel):
    """Response model for IP statistics"""
    total_ips_tracked: int = Field(..., description="Total number of tracked IPs")
    blocked_ips_count: int = Field(..., description="Number of currently blocked IPs")
    tracking_data: Dict[str, Any] = Field(..., description="Detailed tracking data for all IPs")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    ip: Optional[str] = Field(None, description="Client IP if available")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint.
    Returns API status and basic information.
    """
    return {
        "status": "online",
        "service": "IP Risk Engine API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "analyze": "POST /api",
            "suspicious_ips": "GET /suspicious-ips",
            "health": "GET /health"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Detailed health check with system statistics.
    """
    all_stats = get_all_ip_stats()
    blocked_count = len(ip_manager.get_blocked_ips())
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_ips_tracked": len(all_stats),
            "blocked_ips": blocked_count,
            "active_ips": len(all_stats) - blocked_count
        }
    }


@app.post(
    "/api",
    response_model=RiskAnalysisResponse,
    responses={
        200: {"description": "Risk analysis completed successfully"},
        403: {"description": "IP blocked due to suspicious activity", "model": ErrorResponse}
    },
    tags=["Risk Analysis"]
)
async def analyze_request(request: Request):
    """
    Analyze incoming request and update IP risk score.
    
    This endpoint:
    1. Extracts client IP from request state
    2. Checks if IP is currently blocked
    3. Simulates risk scoring (replace with ML models in production)
    4. Updates IP risk and auto-blocks if thresholds exceeded
    5. Returns analysis results
    
    **Production Integration:**
    Replace the simulated risk score with actual ML model inference:
    - Load XGBoost model for classification
    - Use TF-IDF vectorizer for text features
    - Calculate autoencoder reconstruction error
    - Combine scores with weighted average
    
    Example:
    ```python
    xgb_score = xgb_model.predict_proba(features)[0][1]
    text_score = analyze_text_features(request)
    ae_score = autoencoder_anomaly_score(features)
    risk_score = (xgb_score * 0.5 + text_score * 0.3 + ae_score * 0.2)
    ```
    """
    try:
        # Step 1: Get client IP from request state (set by middleware)
        client_ip = getattr(request.state, "client_ip", None)
        
        if not client_ip:
            logger.error("client_ip not found in request.state")
            raise HTTPException(
                status_code=500,
                detail="Unable to determine client IP address"
            )
        
        logger.info(f"Processing request from IP: {client_ip}")
        
        # Step 2: Check if IP is currently blocked
        if is_ip_blocked(client_ip):
            logger.warning(f"Request rejected - IP already blocked: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "IP blocked",
                    "message": "Your IP has been blocked due to suspicious activity",
                    "ip": client_ip
                }
            )
        
        # Step 3: Simulate risk scoring
        # TODO: Replace with actual ML model inference
        # Example: risk_score = predict_with_ml_models(request)
        risk_score = random.uniform(0, 1)
        logger.info(f"Calculated risk score for {client_ip}: {risk_score:.4f}")
        
        # Step 4: Update IP risk and check for auto-blocking
        was_blocked = update_ip_risk(client_ip, risk_score)
        
        if was_blocked:
            logger.warning(f"IP {client_ip} was automatically blocked (risk: {risk_score:.4f})")
        
        # Step 5: Get updated IP statistics
        ip_stats = ip_manager.get_ip_stats(client_ip)
        
        if not ip_stats:
            # Edge case: stats should exist after update_ip_risk
            logger.error(f"Failed to retrieve stats for {client_ip}")
            ip_stats = {
                'request_count': 1,
                'average_risk': risk_score,
                'blocked': was_blocked
            }
        
        # Step 6: Return analysis response
        response_data = {
            "ip": client_ip,
            "risk_score": round(risk_score, 4),
            "blocked_status": ip_stats['blocked'],
            "request_count": ip_stats['request_count'],
            "average_risk": round(ip_stats['average_risk'], 4),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Analysis complete for {client_ip}: {response_data}")
        return response_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get(
    "/suspicious-ips",
    response_model=IPStatsResponse,
    tags=["Monitoring"]
)
async def get_suspicious_ips():
    """
    Retrieve complete IP tracking data.
    
    Returns comprehensive statistics for all tracked IPs including:
    - Total risk scores
    - Request counts
    - Average risk per IP
    - Last seen timestamps
    - Block status
    
    This endpoint is useful for:
    - Security monitoring dashboards
    - Audit logs
    - Threat analysis
    - IP reputation scoring
    """
    try:
        # Get all IP tracking data
        all_stats = get_all_ip_stats()
        blocked_ips = ip_manager.get_blocked_ips()
        
        logger.info(f"Retrieved stats for {len(all_stats)} IPs, {len(blocked_ips)} blocked")
        
        return {
            "total_ips_tracked": len(all_stats),
            "blocked_ips_count": len(blocked_ips),
            "tracking_data": all_stats
        }
    
    except Exception as e:
        logger.error(f"Error retrieving IP stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve IP statistics: {str(e)}"
        )


# ============================================================================
# ADMIN ENDPOINTS (Optional - add authentication in production)
# ============================================================================

@app.get("/admin/blocked-ips", tags=["Admin"])
async def get_blocked_ips_list():
    """
    Get list of all currently blocked IPs.
    
    **Production Note:** Add authentication/authorization middleware
    """
    blocked_ips = ip_manager.get_blocked_ips()
    return {
        "count": len(blocked_ips),
        "blocked_ips": list(blocked_ips),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/admin/unblock/{ip_address}", tags=["Admin"])
async def unblock_ip_address(ip_address: str):
    """
    Manually unblock an IP address and reset its statistics.
    
    **Production Note:** Add authentication/authorization middleware
    
    Args:
        ip_address: IP address to unblock
    """
    if not is_ip_blocked(ip_address):
        raise HTTPException(
            status_code=400,
            detail=f"IP {ip_address} is not currently blocked"
        )
    
    reset_ip(ip_address)
    logger.info(f"Admin action: Unblocked IP {ip_address}")
    
    return {
        "status": "success",
        "message": f"IP {ip_address} has been unblocked",
        "ip": ip_address,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/admin/ip/{ip_address}", tags=["Admin"])
async def get_ip_details(ip_address: str):
    """
    Get detailed statistics for a specific IP address.
    
    **Production Note:** Add authentication/authorization middleware
    """
    stats = ip_manager.get_ip_stats(ip_address)
    
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"No tracking data found for IP: {ip_address}"
        )
    
    return {
        "ip": ip_address,
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    }


@app.delete("/admin/reset-all", tags=["Admin"])
async def reset_all_tracking():
    """
    Reset all IP tracking data and unblock all IPs.
    
    **WARNING:** This clears all historical data.
    **Production Note:** Add authentication/authorization middleware
    """
    ip_manager.clear_all()
    logger.warning("Admin action: All IP tracking data cleared")
    
    return {
        "status": "success",
        "message": "All IP tracking data has been cleared",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# APPLICATION STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks.
    """
    logger.info("=" * 60)
    logger.info("IP Risk Engine API Starting...")
    logger.info("=" * 60)
    logger.info(f"Documentation: http://localhost:8000/docs")
    logger.info(f"Health Check: http://localhost:8000/health")
    logger.info("Ready to accept requests")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks.
    """
    logger.info("IP Risk Engine API Shutting down...")
    # Add cleanup tasks here if needed


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "risk_engine:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Disable in production
        log_level="info"
    )
