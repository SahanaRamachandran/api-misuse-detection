"""
Custom Middleware for IP Extraction and Tracking
-------------------------------------------------
Production-ready middleware for FastAPI applications to extract and store
client IP addresses with support for proxy headers.

Author: Traffic Monitoring System
Date: February 2026
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

# Configure logging
logger = logging.getLogger(__name__)


class IPExtractionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract client IP address from requests.
    
    Supports:
    - Direct client IP (request.client.host)
    - X-Forwarded-For header (for proxied requests)
    - X-Real-IP header (common in nginx setups)
    
    The extracted IP is stored in request.state.client_ip for
    downstream handlers to access.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process each request to extract and store client IP.
        
        Priority order for IP extraction:
        1. X-Forwarded-For (first IP in chain)
        2. X-Real-IP
        3. request.client.host (direct connection)
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in chain
        
        Returns:
            Response from the next handler
        """
        client_ip = None
        
        # Method 1: Check X-Forwarded-For header (most common with proxies)
        # Format: "client, proxy1, proxy2" - we want the first (client) IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Extract the first IP from comma-separated list
            client_ip = forwarded_for.split(",")[0].strip()
            logger.debug(f"IP extracted from X-Forwarded-For: {client_ip}")
        
        # Method 2: Check X-Real-IP header (common in nginx)
        if not client_ip:
            real_ip = request.headers.get("X-Real-IP")
            if real_ip:
                client_ip = real_ip.strip()
                logger.debug(f"IP extracted from X-Real-IP: {client_ip}")
        
        # Method 3: Direct client connection (no proxy)
        if not client_ip:
            if request.client:
                client_ip = request.client.host
                logger.debug(f"IP extracted from direct connection: {client_ip}")
            else:
                # Fallback for testing or unusual configurations
                client_ip = "127.0.0.1"
                logger.warning("Unable to determine client IP, using fallback: 127.0.0.1")
        
        # Store IP in request state for access in route handlers
        request.state.client_ip = client_ip
        
        # Continue processing the request
        response = await call_next(request)
        
        # Optional: Add client IP to response headers for debugging
        response.headers["X-Client-IP"] = client_ip
        
        return response


class IPBlockingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically block requests from flagged IPs.
    
    This middleware should be added AFTER IPExtractionMiddleware
    to ensure request.state.client_ip is available.
    """
    
    def __init__(self, app, ip_manager):
        """
        Initialize the blocking middleware.
        
        Args:
            app: FastAPI application instance
            ip_manager: IPRiskManager instance for checking blocked IPs
        """
        super().__init__(app)
        self.ip_manager = ip_manager
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Check if client IP is blocked before processing request.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in chain
        
        Returns:
            403 error response if blocked, otherwise continues processing
        """
        # Get client IP from request state (set by IPExtractionMiddleware)
        client_ip = getattr(request.state, "client_ip", None)
        
        if not client_ip:
            logger.error("client_ip not found in request.state - ensure IPExtractionMiddleware runs first")
            client_ip = "unknown"
        
        # Check if IP is blocked
        if self.ip_manager.is_ip_blocked(client_ip):
            logger.warning(f"Blocked request from IP: {client_ip}")
            
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Access Denied",
                    "message": "Your IP address has been blocked due to suspicious activity",
                    "ip": client_ip,
                    "status": "blocked"
                }
            )
        
        # IP not blocked, continue processing
        response = await call_next(request)
        return response
