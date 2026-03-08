"""
Quick test to verify realtime detector tracking
"""
import requests

# Direct test of realtime detector
url = "http://localhost:8000/api/security/realtime/status"
response = requests.get(url)
data = response.json()

print("Realtime Detector Status:")
print(f"  Total IPs tracked: {data['total_ips']}")
print(f"  Total requests: {data['total_requests']}")
print(f"  Total anomalies: {data['total_anomalies']}")
print(f"  Blocked IPs: {data['blocked_ips_count']}")
print()

# Check simulation stats
sim_url = "http://localhost:8000/simulation/stats"
sim_response = requests.get(sim_url)
sim_data = sim_response.json()

print("Simulation Stats:")
print(f"  Total requests: {sim_data['total_requests']}")
print(f"  Anomalies detected: {sim_data['anomalies_detected']}")
print(f"  Windows processed: {sim_data['windows_processed']}")
print()

# Check if IPs tracked
if data['total_ips'] == 0 and sim_data['total_requests'] > 0:
    print("❌ PROBLEM: Simulation generated {} requests but detector tracked 0!".format(sim_data['total_requests']))
    print()
    print("Possible causes:")
    print("  1. track_simulation_request() is not being called")
    print("  2. Exception in tracking code (silently caught)")
    print("  3. Detector not initialized properly")
else:
    print("✅ Tracking is working!")
