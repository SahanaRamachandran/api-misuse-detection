"""
IP Manager - FastAPI Integration Example
-----------------------------------------
Demonstrates how to use the IP risk manager in a FastAPI application.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from security.ip_manager import get_ip_manager, is_ip_blocked

app = FastAPI(title="Traffic Monitoring with IP Risk Management")

# Get the global IP manager instance
ip_manager = get_ip_manager()


# Middleware to check blocked IPs
@app.middleware("http")
async def ip_blocking_middleware(request: Request, call_next):
    """
    Middleware to automatically reject requests from blocked IPs.
    This runs before every request.
    """
    # Extract client IP
    client_ip = request.client.host
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        return JSONResponse(
            status_code=403,
            content={
                "error": "Access Denied",
                "message": "Your IP address has been blocked due to suspicious activity",
                "ip": client_ip
            }
        )
    
    # Process the request
    response = await call_next(request)
    return response


@app.post("/api/analyze")
async def analyze_traffic(request: Request):
    """
    Example endpoint that analyzes traffic and updates IP risk.
    
    In your actual implementation, you would:
    1. Extract features from the request
    2. Run your ML models (XGBoost, TF-IDF, Autoencoder)
    3. Calculate a risk score
    4. Update the IP risk manager
    """
    client_ip = request.client.host
    
    # TODO: Replace this with your actual ML model inference
    # Example: risk_score = predict_with_models(request_data)
    risk_score = 0.75  # Placeholder risk score
    
    # Update IP risk and check if it was blocked
    was_blocked = ip_manager.update_ip_risk(client_ip, risk_score)
    
    if was_blocked:
        # IP was just blocked, return 403
        raise HTTPException(
            status_code=403,
            detail=f"IP {client_ip} has been blocked due to high risk activity"
        )
    
    # Get current IP stats
    ip_stats = ip_manager.get_ip_stats(client_ip)
    
    return {
        "status": "analyzed",
        "ip": client_ip,
        "current_risk": risk_score,
        "average_risk": ip_stats['average_risk'],
        "request_count": ip_stats['request_count'],
        "blocked": ip_stats['blocked']
    }


@app.get("/api/security/ip-stats")
async def get_ip_statistics():
    """
    Get statistics for all tracked IPs.
    Admin endpoint to monitor IP risk scores.
    """
    all_stats = ip_manager.get_all_ip_stats()
    
    return {
        "total_ips": len(all_stats),
        "blocked_ips": len(ip_manager.get_blocked_ips()),
        "ip_details": all_stats
    }


@app.get("/api/security/ip/{ip_address}")
async def get_specific_ip_stats(ip_address: str):
    """
    Get statistics for a specific IP address.
    """
    stats = ip_manager.get_ip_stats(ip_address)
    
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"No tracking data found for IP: {ip_address}"
        )
    
    return {
        "ip": ip_address,
        "stats": stats
    }


@app.post("/api/security/unblock/{ip_address}")
async def unblock_ip(ip_address: str):
    """
    Admin endpoint to manually unblock an IP address.
    This resets all statistics for the IP.
    """
    if not is_ip_blocked(ip_address):
        raise HTTPException(
            status_code=400,
            detail=f"IP {ip_address} is not currently blocked"
        )
    
    ip_manager.reset_ip(ip_address)
    
    return {
        "status": "success",
        "message": f"IP {ip_address} has been unblocked and reset",
        "ip": ip_address
    }


@app.get("/api/security/blocked-ips")
async def get_blocked_ips():
    """
    Get list of all currently blocked IPs.
    """
    blocked_ips = ip_manager.get_blocked_ips()
    
    return {
        "count": len(blocked_ips),
        "blocked_ips": list(blocked_ips)
    }


@app.delete("/api/security/reset-all")
async def reset_all_security_data():
    """
    Admin endpoint to reset all IP tracking data.
    Use with caution - this clears all statistics and unblocks all IPs.
    """
    ip_manager.clear_all()
    
    return {
        "status": "success",
        "message": "All IP tracking data has been cleared"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
