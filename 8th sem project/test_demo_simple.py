"""
Simple Demo IP Blocking Test (ASCII only for Windows compatibility)
"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("DEMO IP BLOCKING TEST")
print("=" * 70)
print()

# Step 1: Start simulation
print("Starting SQL injection simulation...")
print("  Endpoint: /sim/login")
print("  Duration: 15 seconds")
print("  Requests: 50")
print("  Expected: Multiple IPs will be blocked\n")

try:
    response = requests.post(
        f"{BASE_URL}/simulation/start",
        params={
            'simulated_endpoint': '/sim/login',
            'duration_seconds': 15,
            'requests_per_window': 50
        }
    )
    
    if response.status_code == 200:
        print("SUCCESS: Simulation started\n")
    else:
        print(f"ERROR: Failed to start simulation (Status: {response.status_code})\n")
        exit(1)
        
except Exception as e:
    print(f"ERROR: {e}\n")
    exit(1)

# Step 2: Wait
print("Waiting 16 seconds for completion...")
for i in range(16):
    time.sleep(1)
    print(f"  {i+1}/16 seconds", end='\r')
print("\nSimulation complete!\n")

# Step 3: Check blocked IPs
print("Checking blocked IPs...\n")
try:
    response = requests.get(f"{BASE_URL}/api/security/realtime/blocked-ips")
    data = response.json()
    blocked_ips = data.get('blocked_ips', [])
    
    print("=" * 70)
    print(f"RESULT: {len(blocked_ips)} IPs BLOCKED")
    print("=" * 70)
    print()
    
    if len(blocked_ips) > 0:
        print("Blocked IP Details:")
        print("-" * 70)
        print(f"{'IP':<15} {'Anomalies':<12} {'Avg Risk':<12} {'Total Requests':<15}")
        print("-" * 70)
        
        for ip in blocked_ips:
            print(f"{ip['ip']:<15} {ip['anomaly_count']:<12} {ip['avg_risk']:<12.2f} {ip['total_requests']:<15}")
        
        print("\nSUCCESS: Demo IP blocking is working!")
        print("\nWhat happened:")
        print("  1. Simulation generated SQL injection attacks")
        print("  2. Same IPs (SIM-1 to SIM-30) made multiple malicious requests")
        print("  3. When any IP hit 5 anomalies, it was auto-blocked")
        print("  4. Blocked IPs now receive 403 Forbidden on all requests")
        
    else:
        print("WARNING: No IPs were blocked")
        print("\nPossible reasons:")
        print("  - Random distribution didn't concentrate anomalies")
        print("  - Try running the test again")
        print("  - Or increase duration to 30 seconds")
        
except Exception as e:
    print(f"ERROR: {e}\n")
    exit(1)

print()
print("=" * 70)
print("View blocked IPs in dashboard: http://localhost:3000/admin")
print("=" * 70)
