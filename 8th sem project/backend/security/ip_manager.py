"""
IP Risk Management Module
--------------------------
Production-ready IP tracking and risk scoring system for FastAPI applications.
Automatically blocks IPs based on risk scores and request patterns.

Author: Traffic Monitoring System
Date: February 2026
"""

from collections import defaultdict
from datetime import datetime
from typing import Dict, Optional
import threading


class IPRiskManager:
    """
    Thread-safe IP risk management system.
    
    Tracks IP addresses, calculates risk scores, and automatically blocks
    high-risk IPs based on configurable thresholds.
    """
    
    # Class-level configuration
    BLOCK_THRESHOLD_AVG_RISK = 0.8  # Average risk threshold for blocking
    BLOCK_THRESHOLD_REQUEST_COUNT = 5  # Minimum requests before blocking
    
    def __init__(self):
        """Initialize the IP risk manager with thread-safe data structures."""
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # Set to store blocked IPs
        self._blocked_ips = set()
        
        # Dictionary to track IP statistics
        # Structure: {
        #     'ip_address': {
        #         'total_risk': float,
        #         'request_count': int,
        #         'average_risk': float,
        #         'last_seen': str (ISO format),
        #         'blocked': bool
        #     }
        # }
        self._ip_stats = defaultdict(lambda: {
            'total_risk': 0.0,
            'request_count': 0,
            'average_risk': 0.0,
            'last_seen': None,
            'blocked': False
        })
    
    def update_ip_risk(self, ip: str, risk: float) -> bool:
        """
        Update the risk score for an IP address and check for auto-block conditions.
        
        Args:
            ip (str): Client IP address
            risk (float): Risk score for the current request (0.0 to 1.0)
        
        Returns:
            bool: True if IP was blocked due to this update, False otherwise
        
        Example:
            >>> manager = IPRiskManager()
            >>> was_blocked = manager.update_ip_risk('192.168.1.100', 0.85)
            >>> if was_blocked:
            ...     print("IP has been blocked!")
        """
        with self._lock:
            # Validate input
            if not ip:
                raise ValueError("IP address cannot be empty")
            
            if not 0.0 <= risk <= 1.0:
                raise ValueError("Risk score must be between 0.0 and 1.0")
            
            # Get or initialize IP stats
            stats = self._ip_stats[ip]
            
            # Update statistics
            stats['total_risk'] += risk
            stats['request_count'] += 1
            stats['average_risk'] = stats['total_risk'] / stats['request_count']
            stats['last_seen'] = datetime.now().isoformat()
            
            # Check if IP should be blocked
            should_block = (
                stats['average_risk'] > self.BLOCK_THRESHOLD_AVG_RISK and
                stats['request_count'] >= self.BLOCK_THRESHOLD_REQUEST_COUNT
            )
            
            # Block IP if conditions are met and not already blocked
            if should_block and not stats['blocked']:
                stats['blocked'] = True
                self._blocked_ips.add(ip)
                return True
            
            return False
    
    def is_ip_blocked(self, ip: str) -> bool:
        """
        Check if an IP address is currently blocked.
        
        Args:
            ip (str): Client IP address to check
        
        Returns:
            bool: True if IP is blocked, False otherwise
        
        Example:
            >>> manager = IPRiskManager()
            >>> if manager.is_ip_blocked('192.168.1.100'):
            ...     raise HTTPException(status_code=403, detail="IP blocked")
        """
        with self._lock:
            return ip in self._blocked_ips
    
    def get_all_ip_stats(self) -> Dict[str, dict]:
        """
        Retrieve statistics for all tracked IP addresses.
        
        Returns:
            dict: Dictionary mapping IP addresses to their statistics
        
        Example:
            >>> manager = IPRiskManager()
            >>> stats = manager.get_all_ip_stats()
            >>> for ip, data in stats.items():
            ...     print(f"{ip}: {data['average_risk']:.2f}")
        """
        with self._lock:
            # Return a deep copy to prevent external modifications
            return {
                ip: {
                    'total_risk': stats['total_risk'],
                    'request_count': stats['request_count'],
                    'average_risk': stats['average_risk'],
                    'last_seen': stats['last_seen'],
                    'blocked': stats['blocked']
                }
                for ip, stats in self._ip_stats.items()
            }
    
    def reset_ip(self, ip: str) -> None:
        """
        Reset all statistics and unblock a specific IP address.
        
        Args:
            ip (str): IP address to reset
        
        Example:
            >>> manager = IPRiskManager()
            >>> manager.reset_ip('192.168.1.100')
            >>> print("IP has been reset and unblocked")
        """
        with self._lock:
            # Remove from blocked set
            self._blocked_ips.discard(ip)
            
            # Remove from stats dictionary
            if ip in self._ip_stats:
                del self._ip_stats[ip]
    
    def get_blocked_ips(self) -> set:
        """
        Get the set of all currently blocked IPs.
        
        Returns:
            set: Set of blocked IP addresses
        
        Example:
            >>> manager = IPRiskManager()
            >>> blocked = manager.get_blocked_ips()
            >>> print(f"Currently blocking {len(blocked)} IPs")
        """
        with self._lock:
            return self._blocked_ips.copy()
    
    def get_ip_stats(self, ip: str) -> Optional[dict]:
        """
        Get statistics for a specific IP address.
        
        Args:
            ip (str): IP address to query
        
        Returns:
            dict or None: IP statistics or None if IP not tracked
        
        Example:
            >>> manager = IPRiskManager()
            >>> stats = manager.get_ip_stats('192.168.1.100')
            >>> if stats:
            ...     print(f"Average risk: {stats['average_risk']:.2f}")
        """
        with self._lock:
            if ip not in self._ip_stats:
                return None
            
            stats = self._ip_stats[ip]
            return {
                'total_risk': stats['total_risk'],
                'request_count': stats['request_count'],
                'average_risk': stats['average_risk'],
                'last_seen': stats['last_seen'],
                'blocked': stats['blocked']
            }
    
    def clear_all(self) -> None:
        """
        Clear all IP statistics and unblock all IPs.
        
        Warning: This will reset the entire tracking system.
        
        Example:
            >>> manager = IPRiskManager()
            >>> manager.clear_all()
            >>> print("All IP data cleared")
        """
        with self._lock:
            self._blocked_ips.clear()
            self._ip_stats.clear()


# Singleton instance for global use
_ip_manager_instance = None


def get_ip_manager() -> IPRiskManager:
    """
    Get or create the global IPRiskManager singleton instance.
    
    Returns:
        IPRiskManager: The global IP risk manager instance
    
    Example:
        >>> from security.ip_manager import get_ip_manager
        >>> manager = get_ip_manager()
        >>> manager.update_ip_risk('192.168.1.100', 0.75)
    """
    global _ip_manager_instance
    if _ip_manager_instance is None:
        _ip_manager_instance = IPRiskManager()
    return _ip_manager_instance


# Convenience functions for direct module-level access
def update_ip_risk(ip: str, risk: float) -> bool:
    """Module-level convenience function. See IPRiskManager.update_ip_risk()"""
    return get_ip_manager().update_ip_risk(ip, risk)


def is_ip_blocked(ip: str) -> bool:
    """Module-level convenience function. See IPRiskManager.is_ip_blocked()"""
    return get_ip_manager().is_ip_blocked(ip)


def get_all_ip_stats() -> Dict[str, dict]:
    """Module-level convenience function. See IPRiskManager.get_all_ip_stats()"""
    return get_ip_manager().get_all_ip_stats()


def reset_ip(ip: str) -> None:
    """Module-level convenience function. See IPRiskManager.reset_ip()"""
    return get_ip_manager().reset_ip(ip)


if __name__ == "__main__":
    # Demonstration and testing code
    print("IP Risk Manager - Demonstration")
    print("=" * 50)
    
    manager = IPRiskManager()
    
    # Test Case 1: Normal traffic
    print("\nTest Case 1: Normal Traffic")
    for i in range(10):
        blocked = manager.update_ip_risk("192.168.1.100", 0.3)
        print(f"  Request {i+1}: Risk=0.3, Blocked={blocked}")
    
    stats = manager.get_ip_stats("192.168.1.100")
    print(f"  Final Stats: Avg Risk={stats['average_risk']:.2f}, Count={stats['request_count']}")
    
    # Test Case 2: High risk traffic (should trigger block)
    print("\nTest Case 2: High Risk Traffic")
    for i in range(10):
        blocked = manager.update_ip_risk("192.168.1.200", 0.9)
        if blocked:
            print(f"  Request {i+1}: Risk=0.9, ⚠️ IP BLOCKED!")
            break
        else:
            print(f"  Request {i+1}: Risk=0.9, Not blocked yet")
    
    stats = manager.get_ip_stats("192.168.1.200")
    print(f"  Final Stats: Avg Risk={stats['average_risk']:.2f}, Count={stats['request_count']}, Blocked={stats['blocked']}")
    
    # Test Case 3: Check blocked status
    print("\nTest Case 3: Checking Blocked Status")
    print(f"  192.168.1.100 blocked: {manager.is_ip_blocked('192.168.1.100')}")
    print(f"  192.168.1.200 blocked: {manager.is_ip_blocked('192.168.1.200')}")
    
    # Test Case 4: Reset IP
    print("\nTest Case 4: Resetting IP")
    print(f"  Before reset - 192.168.1.200 blocked: {manager.is_ip_blocked('192.168.1.200')}")
    manager.reset_ip("192.168.1.200")
    print(f"  After reset - 192.168.1.200 blocked: {manager.is_ip_blocked('192.168.1.200')}")
    
    # Display all IP stats
    print("\nAll IP Statistics:")
    print("-" * 50)
    all_stats = manager.get_all_ip_stats()
    for ip, data in all_stats.items():
        print(f"  {ip}:")
        print(f"    Average Risk: {data['average_risk']:.4f}")
        print(f"    Request Count: {data['request_count']}")
        print(f"    Blocked: {data['blocked']}")
        print(f"    Last Seen: {data['last_seen']}")
