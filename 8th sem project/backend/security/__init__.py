"""
Security Module
---------------
Production-ready security components for FastAPI traffic monitoring system.

Components:
    - ip_manager: IP risk tracking and automatic blocking system
    - middleware: Custom middleware for IP extraction and blocking
    - risk_engine: FastAPI application with risk analysis endpoints
"""

from .ip_manager import (
    IPRiskManager,
    get_ip_manager,
    update_ip_risk,
    is_ip_blocked,
    get_all_ip_stats,
    reset_ip
)

from .middleware import (
    IPExtractionMiddleware,
    IPBlockingMiddleware
)

__all__ = [
    'IPRiskManager',
    'get_ip_manager',
    'update_ip_risk',
    'is_ip_blocked',
    'get_all_ip_stats',
    'reset_ip',
    'IPExtractionMiddleware',
    'IPBlockingMiddleware'
]

__version__ = '1.0.0'
