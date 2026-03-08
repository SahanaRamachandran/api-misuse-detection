"""
API Testing Script
------------------
Test the IP Risk Engine API endpoints.

Usage:
    python test_api.py
"""

import requests
import time
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TEST_ITERATIONS = 10


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_response(response: requests.Response):
    """Pretty print response"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


def test_health_check():
    """Test health check endpoint"""
    print_section("Test 1: Health Check")
    
    response = requests.get(f"{BASE_URL}/health")
    print_response(response)
    
    assert response.status_code == 200, "Health check failed"
    print("✓ Health check passed")


def test_api_endpoint():
    """Test the main /api endpoint"""
    print_section("Test 2: Risk Analysis Endpoint")
    
    # Test with normal requests
    print("\nSending 5 normal risk requests...")
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/api",
            headers={"X-Forwarded-For": "192.168.1.100"}
        )
        print(f"\nRequest {i+1}:")
        print_response(response)
        time.sleep(0.5)
    
    print("\n✓ Normal requests completed")


def test_high_risk_blocking():
    """Test automatic IP blocking with simulated high risk"""
    print_section("Test 3: High Risk IP Blocking")
    
    print("\nSending requests from potentially risky IP...")
    print("(Risk scores are random, may need multiple runs to trigger block)")
    
    blocked = False
    for i in range(TEST_ITERATIONS):
        response = requests.post(
            f"{BASE_URL}/api",
            headers={"X-Forwarded-For": "10.0.0.50"}
        )
        
        print(f"\nRequest {i+1}:")
        print_response(response)
        
        if response.status_code == 403:
            print("⚠️  IP was blocked!")
            blocked = True
            break
        
        time.sleep(0.3)
    
    if not blocked:
        print("\n⚠️  IP was not blocked (risk scores were too low)")
        print("   This is expected due to random risk simulation")


def test_suspicious_ips_endpoint():
    """Test the suspicious IPs tracking endpoint"""
    print_section("Test 4: Suspicious IPs Tracking")
    
    response = requests.get(f"{BASE_URL}/suspicious-ips")
    print_response(response)
    
    assert response.status_code == 200, "Failed to retrieve suspicious IPs"
    
    data = response.json()
    print(f"\n✓ Tracking {data['total_ips_tracked']} IPs")
    print(f"✓ {data['blocked_ips_count']} IPs are blocked")


def test_admin_endpoints():
    """Test admin endpoints"""
    print_section("Test 5: Admin Endpoints")
    
    # Get blocked IPs
    print("\nGetting blocked IPs list...")
    response = requests.get(f"{BASE_URL}/admin/blocked-ips")
    print_response(response)
    
    data = response.json()
    blocked_ips = data.get('blocked_ips', [])
    
    if blocked_ips:
        # Try to unblock the first blocked IP
        ip_to_unblock = blocked_ips[0]
        print(f"\nUnblocking IP: {ip_to_unblock}")
        response = requests.post(f"{BASE_URL}/admin/unblock/{ip_to_unblock}")
        print_response(response)
        
        # Verify it was unblocked
        print(f"\nVerifying {ip_to_unblock} was unblocked...")
        response = requests.get(f"{BASE_URL}/admin/ip/{ip_to_unblock}")
        if response.status_code == 404:
            print("✓ IP successfully unblocked and removed from tracking")
        else:
            print_response(response)
    else:
        print("\n⚠️  No blocked IPs to test unblocking")


def test_x_forwarded_for():
    """Test X-Forwarded-For header support"""
    print_section("Test 6: X-Forwarded-For Header Support")
    
    test_ips = [
        "203.0.113.1",
        "198.51.100.2",
        "192.0.2.3"
    ]
    
    for ip in test_ips:
        print(f"\nTesting with IP: {ip}")
        response = requests.post(
            f"{BASE_URL}/api",
            headers={"X-Forwarded-For": ip}
        )
        
        data = response.json()
        if response.status_code == 200:
            extracted_ip = data.get('ip')
            print(f"Extracted IP: {extracted_ip}")
            assert extracted_ip == ip, f"IP mismatch: expected {ip}, got {extracted_ip}"
            print("✓ IP correctly extracted")
        else:
            print_response(response)
        
        time.sleep(0.3)


def run_all_tests():
    """Run all test cases"""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  IP Risk Engine API - Comprehensive Test Suite".center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    
    try:
        # Check if server is running
        print("\nChecking if server is running...")
        response = requests.get(f"{BASE_URL}/", timeout=2)
        if response.status_code != 200:
            raise Exception("Server not responding correctly")
        print("✓ Server is running")
        
        # Run tests
        test_health_check()
        test_api_endpoint()
        test_suspicious_ips_endpoint()
        test_x_forwarded_for()
        test_high_risk_blocking()
        test_admin_endpoints()
        
        # Final summary
        print_section("Test Summary")
        print("\n✓ All tests completed successfully!")
        print("\nNext Steps:")
        print("1. Integrate your ML models (XGBoost, TF-IDF, Autoencoder)")
        print("2. Replace random.uniform() with actual risk prediction")
        print("3. Add authentication to admin endpoints")
        print("4. Configure CORS for production")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API server")
        print("Make sure the server is running:")
        print("   python -m uvicorn security.risk_engine:app --reload")
        print("\nOr run: START_RISK_ENGINE.bat")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
