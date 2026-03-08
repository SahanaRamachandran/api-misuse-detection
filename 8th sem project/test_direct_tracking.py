"""
Direct test of realtime_detector.track_simulation_request
"""
import sys
sys.path.append('backend')

from security.realtime_detection import setup_realtime_detection

# Initialize detector
print("Initializing realtime detector...")
detector = setup_realtime_detection(
    openai_api_key="test",
    risk_threshold=0.7,
    block_avg_risk_threshold=0.8,
    block_anomaly_count_threshold=5
)

print(f"Detector initialized: {detector is not None}")
print(f"Models loaded: {detector.models_loaded if detector else False}")
print()

# Track some simulation requests
print("Tracking simulation requests...")
for i in range(10):
    ip = f"SIM-{(i % 3) + 1}"  # Use only 3 IPs to concentrate anomalies
    
    result = detector.track_simulation_request(
        ip_address=ip,
        endpoint="/sim/login",
        method="POST",
        response_time_ms=300 + (i * 10),
        status_code=200 if i % 3 == 0 else 403,
        payload_size=1500
    )
    
    print(f"Request {i+1}: IP={ip}, Risk={result['risk_score']:.4f}, "
          f"Anomaly={result['is_anomaly']}, Blocked={result.get('blocked', False)}")
    print(f"  Profile: Requests={result['profile']['total_requests']}, "
          f"Anomalies={result['profile']['anomaly_count']}, "
          f"Avg Risk={result['profile']['avg_risk']:.4f}")
    print()

# Check blocked IPs
print("=" * 70)
blocked = detector.get_blocked_ips()
print(f"Blocked IPs: {len(blocked)}")
for ip in blocked:
    print(f"  - {ip}")
print()

# Get all profiles
profiles = detector.get_all_profiles()
print(f"All IP Profiles: {len(profiles)}")
for ip, profile in profiles.items():
    print(f"  {ip}: Requests={profile['total_requests']}, "
          f"Anomalies={profile['anomaly_count']}, "
          f"Avg Risk={profile['avg_risk']:.4f}, "
          f"Blocked={profile.get('blocked', False)}")
