"""
Quick Integration Test for ML Anomaly Detection

This script tests the integration of ML anomaly detection with the main application.
Run this after starting the FastAPI server to verify all endpoints work.
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """Print a section header"""
    print("\n" + "="*70)
    print(title)
    print("="*70)

def test_endpoint(endpoint: str, method: str = "GET", data: Dict = None) -> Any:
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"✗ Unsupported method: {method}")
            return None
        
        if response.status_code == 200:
            print(f"✓ {method} {endpoint} - Status: {response.status_code}")
            return response.json()
        else:
            print(f"✗ {method} {endpoint} - Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection failed - Is the server running at {BASE_URL}?")
        return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None


def main():
    """Run integration tests"""
    print_section("ML ANOMALY DETECTION - INTEGRATION TEST")
    
    print("\nChecking server connection...")
    
    # Test 1: Check ML Anomaly Detector Status
    print_section("TEST 1: ML Anomaly Detector Status")
    status = test_endpoint("/api/ml/anomaly-detector/status")
    
    if status:
        print(f"\nStatus:")
        print(f"  Available: {status.get('available', False)}")
        print(f"  Enabled: {status.get('enabled', False)}")
        
        if status.get('models'):
            print(f"\nModels loaded:")
            print(f"  CIC IDS 2017: {status['models'].get('cic_ids_models', 0)}")
            print(f"  CSIC 2010: {status['models'].get('csic_http_models', 0)}")
            print(f"  Total: {status['models'].get('total_models', 0)}")
        
        if status.get('runtime_stats'):
            print(f"\nRuntime stats:")
            for key, value in status['runtime_stats'].items():
                print(f"  {key}: {value}")
    
    # Test 2: Check Blocked IPs
    print_section("TEST 2: Blocked IPs")
    blocked = test_endpoint("/api/ml/anomaly-detector/blocked-ips")
    
    if blocked:
        print(f"\nTotal blocked IPs: {blocked.get('total_blocked', 0)}")
        
        if blocked.get('blocked_ips'):
            print(f"\nBlocked IP details:")
            for ip_info in blocked['blocked_ips'][:5]:  # Show first 5
                print(f"  {ip_info['ip']}: {ip_info['anomaly_count']} anomalies")
    
    # Test 3: Check Performance Metrics
    print_section("TEST 3: Performance Metrics")
    perf = test_endpoint("/api/ml/anomaly-detector/performance")
    
    if perf:
        print(f"\nEnsemble performance:")
        ensemble = perf.get('ensemble_performance', {})
        for key, value in ensemble.items():
            print(f"  {key}: {value}")
        
        print(f"\nProtocol breakdown:")
        protocol = perf.get('protocol_breakdown', {})
        for key, value in protocol.items():
            print(f"  {key}: {value}")
    
    # Test 4: Check Enhanced Detection Status
    print_section("TEST 4: Enhanced Detection Status")
    enhanced = test_endpoint("/api/ml/enhanced-detection/status")
    
    if enhanced:
        print(f"\nEnhanced Detection:")
        print(f"  Available: {enhanced.get('available', False)}")
        print(f"  Enabled: {enhanced.get('enabled', False)}")
        
        if enhanced.get('stats'):
            print(f"\nStats:")
            for key, value in enhanced['stats'].items():
                print(f"  {key}: {value}")
    
    # Test 5: Check Real-time Detection Status (if available)
    print_section("TEST 5: Real-time Detection Status")
    realtime = test_endpoint("/api/ml/status")
    
    if realtime:
        print(f"\nReal-time Detection:")
        for key, value in realtime.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
    
    # Test 6: Check Live Mode Stats
    print_section("TEST 6: Live Mode Stats")
    stats = test_endpoint("/api/stats")
    
    if stats:
        print(f"\nOverall system stats:")
        for key, value in list(stats.items())[:10]:  # Show first 10
            print(f"  {key}: {value}")
    
    # Summary
    print_section("INTEGRATION TEST SUMMARY")
    print("\nAll tests completed!")
    print("\nTo verify ML anomaly detection is working:")
    print("  1. Start the backend server: python app.py")
    print("  2. Generate some traffic through the API endpoints")
    print("  3. Check /api/ml/anomaly-detector/status for detection stats")
    print("  4. Monitor /api/ml/anomaly-detector/blocked-ips for blocked IPs")
    print("\nAPI Documentation:")
    print(f"  {BASE_URL}/docs")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
