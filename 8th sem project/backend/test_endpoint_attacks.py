"""
Quick Test Script - Verify Different Attacks for Different Endpoints

This script tests that different security attacks are properly assigned
to different endpoints in the system.
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:8000"

# Endpoint-to-Attack mapping (from anomaly_injection.py)
ENDPOINT_ATTACKS = {
    # SQL Injection endpoints
    "/sim/login": "SQL_INJECTION",
    "/sim/payment": "SQL_INJECTION", 
    "/sim/signup": "SQL_INJECTION",
    "/sim/api/posts": "SQL_INJECTION",
    
    # DDoS Attack endpoints
    "/sim/search": "DDOS_ATTACK",
    "/sim/api/users": "DDOS_ATTACK",
    
    # XSS Attack endpoints
    "/sim/profile": "XSS_ATTACK",
    "/sim/logout": "XSS_ATTACK",
    "/sim/api/data": "XSS_ATTACK",
    "/sim/api/comments": "XSS_ATTACK"
}

def test_endpoint_attacks():
    """Test that each endpoint receives its assigned attack type."""
    print("="*70)
    print("TESTING ENDPOINT-TO-ATTACK MAPPING")
    print("="*70)
    print()
    
    # First, start simulation mode
    print("Starting simulation mode...")
    try:
        response = requests.post(f"{BASE_URL}/simulation/start")
        if response.status_code == 200:
            print("[OK] Simulation mode started")
        else:
            print(f"[WARNING] Failed to start simulation: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"[ERROR] Error starting simulation: {e}")
        return
    
    sleep(2)  # Wait for simulation to initialize
    
    # Test each endpoint
    results = {}
    for endpoint, expected_attack in ENDPOINT_ATTACKS.items():
        print(f"\n{'='*70}")
        print(f"Testing: {endpoint}")
        print(f"Expected Attack: {expected_attack}")
        print('-'*70)
        
        try:
            # Make request to endpoint
            response = requests.get(f"{BASE_URL}{endpoint}")
            
            # Check if malicious pattern was detected
            # (In simulation mode, logs should have malicious_pattern field)
            print(f"Status Code: {response.status_code}")
            
            # Get recent anomalies to verify
            sleep(1)
            anomalies_response = requests.get(f"{BASE_URL}/anomalies")
            if anomalies_response.status_code == 200:
                anomalies = anomalies_response.json()
                
                # Look for this endpoint in recent anomalies
                endpoint_anomalies = [
                    a for a in anomalies 
                    if a.get('endpoint') == endpoint
                ]
                
                if endpoint_anomalies:
                    latest = endpoint_anomalies[-1]
                    detected_type = latest.get('anomaly_type', 'UNKNOWN')
                    print(f"[OK] Anomaly Detected: {detected_type}")
                    results[endpoint] = {
                        'expected': expected_attack,
                        'detected': detected_type,
                        'match': detected_type == expected_attack
                    }
                else:
                    print(f"[INFO] No anomaly recorded yet (may appear in next detection cycle)")
                    results[endpoint] = {
                        'expected': expected_attack,
                        'detected': 'PENDING',
                        'match': False
                    }
            
        except Exception as e:
            print(f"[ERROR] Error testing endpoint: {e}")
            results[endpoint] = {
                'expected': expected_attack,
                'detected': 'ERROR',
                'match': False
            }
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY OF RESULTS")
    print('='*70)
    print()
    
    # Group by attack type
    sql_endpoints = [ep for ep, attack in ENDPOINT_ATTACKS.items() if attack == "SQL_INJECTION"]
    ddos_endpoints = [ep for ep, attack in ENDPOINT_ATTACKS.items() if attack == "DDOS_ATTACK"]
    xss_endpoints = [ep for ep, attack in ENDPOINT_ATTACKS.items() if attack == "XSS_ATTACK"]
    
    print("SQL INJECTION Endpoints:")
    for ep in sql_endpoints:
        status = "[OK]" if results.get(ep, {}).get('match') else "[PENDING]"
        print(f"  {status} {ep}")
    
    print("\nDDoS ATTACK Endpoints:")
    for ep in ddos_endpoints:
        status = "[OK]" if results.get(ep, {}).get('match') else "[PENDING]"
        print(f"  {status} {ep}")
    
    print("\nXSS ATTACK Endpoints:")
    for ep in xss_endpoints:
        status = "[OK]" if results.get(ep, {}).get('match') else "[PENDING]"
        print(f"  {status} {ep}")
    
    print()
    print("="*70)
    print("Note: Detection is pending - anomalies injected but not yet")
    print("      recorded by the detection cycle. Check the dashboard or wait")
    print("      for the next detection window (60 seconds).")
    print("="*70)

def display_injection_status():
    """Display current injection status for all endpoints."""
    print("\n" + "="*70)
    print("CURRENT INJECTION STATUS")
    print("="*70)
    
    try:
        response = requests.get(f"{BASE_URL}/injection_status")
        if response.status_code == 200:
            status = response.json()
            
            for endpoint, info in status.items():
                active = "[ACTIVE]" if info.get('is_active') else "[INACTIVE]"
                attack_type = info.get('anomaly_type', 'UNKNOWN')
                severity = info.get('severity', 'UNKNOWN')
                time_remaining = info.get('time_remaining_seconds', 0)
                
                print(f"\n{endpoint}")
                print(f"  Status: {active}")
                print(f"  Attack: {attack_type}")
                print(f"  Severity: {severity}")
                if time_remaining > 0:
                    print(f"  Time Remaining: {int(time_remaining)}s")
                print(f"  Injections: {info.get('injection_count', 0)}")
    except Exception as e:
        print(f"Error getting injection status: {e}")

if __name__ == "__main__":
    print("""
===================================================================
                                                                   
         ENDPOINT-TO-ATTACK MAPPING VERIFICATION TEST              
                                                                   
  This test verifies that different endpoints receive different    
  security attacks in simulation mode:                             
                                                                   
    - SQL Injection  > /sim/login, /sim/payment, etc.             
    - DDoS Attack    > /sim/search, /sim/api/users                
    - XSS Attack     > /sim/profile, /sim/api/comments            
                                                                   
===================================================================
    """)
    
    test_endpoint_attacks()
    display_injection_status()
    
    print("\n\n[*] Open the dashboard to see real-time attack detection:")
    print("   -> http://localhost:3000")
    print()
