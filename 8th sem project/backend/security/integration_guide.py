"""
Integration Guide: Adding IP Risk Engine to Existing FastAPI App
------------------------------------------------------------------
This file demonstrates how to integrate the IP risk management system
into your existing app.py or main FastAPI application.

Author: Traffic Monitoring System
Date: February 2026
"""

# ============================================================================
# METHOD 1: Add to Existing app.py
# ============================================================================

"""
In your existing app.py, add the following:
"""

from fastapi import FastAPI, Request
from security.ip_manager import get_ip_manager, update_ip_risk, is_ip_blocked
from security.middleware import IPExtractionMiddleware

# Your existing app
app = FastAPI(title="Traffic Monitoring System")

# Get IP manager instance
ip_manager = get_ip_manager()

# Add IP extraction middleware (IMPORTANT: Add this early in middleware chain)
app.add_middleware(IPExtractionMiddleware)

# Your existing endpoints...
# Now you can access client IP via request.state.client_ip


# ============================================================================
# METHOD 2: Protect Specific Endpoints
# ============================================================================

"""
Protect individual endpoints by checking IP risk:
"""

@app.post("/api/analyze-traffic")
async def analyze_traffic(request: Request):
    """Example: Protected endpoint with IP risk checking"""
    
    # Get client IP (set by IPExtractionMiddleware)
    client_ip = request.state.client_ip
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        return JSONResponse(
            status_code=403,
            content={"error": "IP blocked", "ip": client_ip}
        )
    
    # Your existing traffic analysis logic
    # ...
    analysis_result = perform_analysis()
    
    # Calculate risk from your ML models
    risk_score = calculate_risk_with_ml_models(analysis_result)
    
    # Update IP risk (auto-blocks if thresholds exceeded)
    was_blocked = update_ip_risk(client_ip, risk_score)
    
    if was_blocked:
        return JSONResponse(
            status_code=403,
            content={"error": "IP blocked due to suspicious activity"}
        )
    
    return analysis_result


# ============================================================================
# METHOD 3: Global IP Blocking Middleware
# ============================================================================

"""
Add automatic blocking for ALL endpoints:
"""

from security.middleware import IPBlockingMiddleware

# Add to your app (after IPExtractionMiddleware)
app.add_middleware(IPBlockingMiddleware, ip_manager=ip_manager)

# Now ALL requests from blocked IPs will be rejected automatically


# ============================================================================
# METHOD 4: Integration with Existing Anomaly Detection
# ============================================================================

"""
If you have existing anomaly detection (e.g., in anomaly_detection.py):
"""

from security.ip_manager import update_ip_risk

def detect_anomalies(request_data: dict, client_ip: str):
    """Your existing anomaly detection function"""
    
    # Your existing detection logic
    is_anomaly = check_for_anomalies(request_data)
    anomaly_score = calculate_anomaly_score(request_data)
    
    # Convert anomaly score to risk score (0.0 to 1.0)
    if is_anomaly:
        risk_score = min(1.0, anomaly_score)  # Ensure it's 0-1
    else:
        risk_score = max(0.0, anomaly_score * 0.5)  # Lower risk for normal traffic
    
    # Update IP risk tracking
    was_blocked = update_ip_risk(client_ip, risk_score)
    
    return {
        "is_anomaly": is_anomaly,
        "risk_score": risk_score,
        "ip_blocked": was_blocked
    }


# ============================================================================
# METHOD 5: Database Integration
# ============================================================================

"""
Store IP risk data in your database:
"""

from security.ip_manager import get_all_ip_stats
from database import SessionLocal  # Your database session

@app.get("/api/sync-ip-data")
async def sync_ip_data_to_database():
    """Sync IP risk data to database for persistence"""
    
    all_stats = get_all_ip_stats()
    db = SessionLocal()
    
    try:
        for ip, stats in all_stats.items():
            # Check if IP exists in database
            ip_record = db.query(IPRiskRecord).filter_by(ip=ip).first()
            
            if ip_record:
                # Update existing record
                ip_record.total_risk = stats['total_risk']
                ip_record.request_count = stats['request_count']
                ip_record.average_risk = stats['average_risk']
                ip_record.last_seen = stats['last_seen']
                ip_record.blocked = stats['blocked']
            else:
                # Create new record
                ip_record = IPRiskRecord(
                    ip=ip,
                    total_risk=stats['total_risk'],
                    request_count=stats['request_count'],
                    average_risk=stats['average_risk'],
                    last_seen=stats['last_seen'],
                    blocked=stats['blocked']
                )
                db.add(ip_record)
        
        db.commit()
        return {"status": "success", "synced_ips": len(all_stats)}
    
    finally:
        db.close()


# ============================================================================
# METHOD 6: WebSocket Integration
# ============================================================================

"""
Real-time IP risk updates via WebSocket:
"""

from fastapi import WebSocket
import json

@app.websocket("/ws/ip-monitor")
async def websocket_ip_monitor(websocket: WebSocket):
    """Send real-time IP risk updates to connected clients"""
    await websocket.accept()
    
    try:
        while True:
            # Get current stats
            all_stats = get_all_ip_stats()
            blocked_ips = ip_manager.get_blocked_ips()
            
            # Prepare data
            data = {
                "total_ips": len(all_stats),
                "blocked_count": len(blocked_ips),
                "recent_blocks": list(blocked_ips)[-10:],  # Last 10 blocked
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to client
            await websocket.send_json(data)
            
            # Wait before next update
            await asyncio.sleep(5)
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()


# ============================================================================
# METHOD 7: Complete Integration Example
# ============================================================================

"""
Full example showing complete integration:
"""

from fastapi import FastAPI, Request, Depends
from security.ip_manager import get_ip_manager, update_ip_risk, is_ip_blocked
from security.middleware import IPExtractionMiddleware, IPBlockingMiddleware

# Create app
app = FastAPI(title="Traffic Monitoring with IP Risk Management")

# Get IP manager
ip_manager = get_ip_manager()

# Add middlewares (ORDER MATTERS!)
app.add_middleware(IPExtractionMiddleware)
# Optionally add automatic blocking:
# app.add_middleware(IPBlockingMiddleware, ip_manager=ip_manager)


# Dependency to get client IP
def get_client_ip(request: Request) -> str:
    """Dependency to extract client IP from request state"""
    return getattr(request.state, "client_ip", "unknown")


@app.post("/api/ml-analysis")
async def ml_analysis(
    request: Request,
    client_ip: str = Depends(get_client_ip)
):
    """
    Example endpoint with ML model integration and IP risk tracking
    """
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        return JSONResponse(
            status_code=403,
            content={"error": "IP blocked", "ip": client_ip}
        )
    
    # Get request data
    request_data = await request.json()
    
    # ========================================
    # Your ML Model Integration Here
    # ========================================
    
    # Example: Load and use your models
    # xgb_score = xgb_model.predict_proba(features)[0][1]
    # tfidf_features = tfidf.transform([text])
    # ae_error = calculate_autoencoder_error(features)
    
    # For now, simulate
    ml_risk_score = 0.75  # Replace with actual ML prediction
    
    # ========================================
    # Update IP Risk
    # ========================================
    
    was_blocked = update_ip_risk(client_ip, ml_risk_score)
    
    if was_blocked:
        return JSONResponse(
            status_code=403,
            content={
                "error": "IP blocked",
                "message": "This IP has been blocked due to repeated suspicious activity",
                "ip": client_ip
            }
        )
    
    # Get updated stats
    ip_stats = ip_manager.get_ip_stats(client_ip)
    
    # Return response
    return {
        "status": "analyzed",
        "client_ip": client_ip,
        "risk_score": ml_risk_score,
        "ip_statistics": {
            "average_risk": ip_stats['average_risk'],
            "request_count": ip_stats['request_count'],
            "blocked": ip_stats['blocked']
        },
        "analysis_result": {
            # Your analysis results here
            "anomaly_detected": ml_risk_score > 0.7,
            "confidence": ml_risk_score
        }
    }


# Add monitoring endpoints
@app.get("/api/security/dashboard")
async def security_dashboard():
    """Dashboard data for frontend"""
    all_stats = get_all_ip_stats()
    blocked_ips = ip_manager.get_blocked_ips()
    
    return {
        "summary": {
            "total_ips": len(all_stats),
            "blocked_ips": len(blocked_ips),
            "active_monitoring": True
        },
        "top_risky_ips": sorted(
            all_stats.items(),
            key=lambda x: x[1]['average_risk'],
            reverse=True
        )[:10],
        "recent_blocks": list(blocked_ips)
    }


# ============================================================================
# CONFIGURATION TIPS
# ============================================================================

"""
1. Adjust blocking thresholds in ip_manager.py:
   
   class IPRiskManager:
       BLOCK_THRESHOLD_AVG_RISK = 0.8      # Adjust based on your needs
       BLOCK_THRESHOLD_REQUEST_COUNT = 5    # Adjust based on traffic volume

2. Add IP whitelisting:
   
   WHITELISTED_IPS = {"127.0.0.1", "192.168.1.1"}
   
   if client_ip in WHITELISTED_IPS:
       # Skip risk tracking
       pass

3. Persist IP data by periodically calling:
   
   - save_to_database()
   - export_to_file()
   
4. Monitor blocked IPs:
   
   - Set up alerts when IPs are blocked
   - Review blocked IPs daily
   - Implement auto-unblock after time period
"""


# ============================================================================
# TESTING YOUR INTEGRATION
# ============================================================================

"""
Test the integration:

1. Start your server:
   uvicorn app:app --reload

2. Test with curl:
   curl -X POST http://localhost:8000/api/ml-analysis \
     -H "X-Forwarded-For: 192.168.1.100" \
     -H "Content-Type: application/json" \
     -d '{"data": "test"}'

3. Check IP stats:
   curl http://localhost:8000/suspicious-ips

4. Monitor in real-time:
   - Check logs
   - Use /api/security/dashboard
   - Monitor WebSocket endpoint
"""

if __name__ == "__main__":
    print("Integration Guide for IP Risk Engine")
    print("=" * 60)
    print("\nThis file shows various integration methods.")
    print("Choose the method that best fits your architecture.")
    print("\nRefer to comments in the code for implementation details.")
