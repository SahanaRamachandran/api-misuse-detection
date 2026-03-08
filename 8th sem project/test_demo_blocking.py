"""
Test Demo IP Blocking Functionality
"""
import requests
import time
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"

def test_demo_ip_blocking():
    print("="*70)
    print("TESTING DEMO IP BLOCKING")
    print("="*70)
    print()
    
    # Step 1: Check initial state
    print("Step 1: Checking initial blocked IPs...")
    try:
        response = requests.get(f"{BASE_URL}/api/security/realtime/blocked-ips")
        initial_data = response.json()
        initial_blocked = len(initial_data.get('blocked_ips', []))
        print(f"   ✓ Initial blocked IPs: {initial_blocked}")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Step 2: Start simulation
    print("Step 2: Starting SQL injection simulation...")
    print("   Endpoint: /sim/login")
    print("   Duration: 15 seconds")
    print("   Requests: 50 per window")
    print("   Anomaly Rate: ~70%")
    print("   IP Range: SIM-1 to SIM-30 (concentrated)")
    print()
    
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
            print(f"   ✓ Simulation started successfully")
            print(f"   Response: {response.json()}")
            print()
        else:
            print(f"   ✗ Failed to start simulation: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Step 3: Wait for simulation to run
    print("Step 3: Waiting for simulation to complete...")
    for i in range(16):
        print(f"   ⏳ {i+1}/16 seconds...", end='\r')
        time.sleep(1)
    print()
    print("   ✓ Simulation complete!")
    print()
    
    # Step 4: Check blocked IPs
    print("Step 4: Checking blocked IPs after simulation...")
    try:
        response = requests.get(f"{BASE_URL}/api/security/realtime/blocked-ips")
        final_data = response.json()
        final_blocked = final_data.get('blocked_ips', [])
        
        print(f"   ✓ Final blocked IPs: {len(final_blocked)}")
        print()
        
        if len(final_blocked) > initial_blocked:
            print("="*70)
            print(f"✅ SUCCESS! {len(final_blocked) - initial_blocked} NEW IPs BLOCKED")
            print("="*70)
            print()
            
            # Show blocked IPs
            print("BLOCKED IP DETAILS:")
            print("-"*70)
            print(f"{'IP Address':<15} {'Anomalies':<12} {'Avg Risk':<12} {'Last Seen':<25}")
            print("-"*70)
            
            for ip_data in final_blocked:
                print(f"{ip_data['ip']:<15} "
                      f"{ip_data['anomaly_count']:<12} "
                      f"{ip_data['avg_risk']:<12.2f} "
                      f"{ip_data.get('last_seen', 'N/A'):<25}")
            
            print()
            
        else:
            print("⚠️  WARNING: No new IPs were blocked")
            print()
            print("Possible reasons:")
            print("   - Duration too short")
            print("   - Random distribution didn't concentrate anomalies")
            print("   - Try running demo again for different random seed")
            print()
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Step 5: Check simulation stats
    print("Step 5: Checking simulation statistics...")
    try:
        response = requests.get(f"{BASE_URL}/simulation/stats")
        stats = response.json()
        
        print(f"   Total Requests: {stats.get('total_requests', 0)}")
        print(f"   Anomalies Detected: {stats.get('anomalies_detected', 0)}")
        print(f"   Windows Processed: {stats.get('windows_processed', 0)}")
        print()
        
    except Exception as e:
        print(f"   ✗ Error getting stats: {e}")
        print()
    
    print("="*70)
    print("TEST COMPLETE")
    print("="*70)
    print()
    print("Next Steps:")
    print("   1. Open http://localhost:3000/admin")
    print("   2. View blocked IPs in the 'Blocked IPs' tab")
    print("   3. Click 'Unblock' to remove IPs from blocklist")
    print()

if __name__ == "__main__":
    test_demo_ip_blocking()
