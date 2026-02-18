"""
IP Risk Scoring Engine

Tracks per-IP threat metrics and computes cumulative risk scores:
- Anomaly count (number of flagged requests)
- Frequency (requests per time window)
- Severity (average threat scores)
- Cumulative risk score (0-100)
- Dynamic updates in real-time
- Threshold-based flagging (log only, no blocking)
- Persistent storage in ip_risk_tracker.json

Enables IP-level threat tracking and analysis.
"""

import json
import time
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


class IPRiskEngine:
    """
    Track and score IP-level threat risk over time.
    """
    
    def __init__(
        self,
        tracker_path: str = 'evaluation_results/monitoring/ip_risk_tracker.json',
        high_risk_threshold: int = 70,
        time_window_hours: int = 24,
        decay_rate: float = 0.95
    ):
        """
        Initialize IP risk engine.
        
        Args:
            tracker_path: Path to persistent risk tracker JSON
            high_risk_threshold: Score threshold for flagging IPs (0-100)
            time_window_hours: Time window for risk calculation
            decay_rate: Exponential decay rate for old events (0-1)
        """
        self.tracker_path = Path(tracker_path)
        self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.high_risk_threshold = high_risk_threshold
        self.time_window_hours = time_window_hours
        self.decay_rate = decay_rate
        
        # In-memory IP tracker
        self.ip_data = defaultdict(lambda: {
            'anomaly_count': 0,
            'total_requests': 0,
            'threat_scores': [],
            'timestamps': [],
            'flagged': False,
            'first_seen': None,
            'last_seen': None,
            'risk_score': 0.0
        })
        
        # Load existing tracker
        self.load_tracker()
    
    def load_tracker(self) -> None:
        """Load IP tracker from persistent storage."""
        if self.tracker_path.exists():
            with open(self.tracker_path, 'r') as f:
                data = json.load(f)
                
                # Restore IP data
                for ip, ip_info in data.get('ips', {}).items():
                    self.ip_data[ip] = ip_info
                
                print(f"[OK] Loaded IP tracker: {len(self.ip_data)} IPs tracked")
        else:
            print("[INFO] No existing IP tracker found. Starting fresh.")
    
    def save_tracker(self) -> None:
        """Save IP tracker to persistent storage."""
        data = {
            'ips': dict(self.ip_data),
            'last_updated': datetime.utcnow().isoformat(),
            'total_ips': len(self.ip_data),
            'high_risk_ips': sum(1 for ip_info in self.ip_data.values() if ip_info['risk_score'] >= self.high_risk_threshold)
        }
        
        with open(self.tracker_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _apply_temporal_decay(self, timestamps: List[float], scores: List[float]) -> List[float]:
        """
        Apply exponential decay to older scores.
        
        Args:
            timestamps: List of event timestamps
            scores: List of threat scores
            
        Returns:
            Decayed scores
        """
        if not timestamps or not scores:
            return []
        
        current_time = time.time()
        decayed_scores = []
        
        for ts, score in zip(timestamps, scores):
            age_hours = (current_time - ts) / 3600
            decay_factor = self.decay_rate ** age_hours
            decayed_scores.append(score * decay_factor)
        
        return decayed_scores
    
    def _filter_by_time_window(
        self,
        timestamps: List[float],
        scores: List[float]
    ) -> tuple:
        """
        Filter events within time window.
        
        Args:
            timestamps: List of event timestamps
            scores: List of threat scores
            
        Returns:
            Tuple of (filtered_timestamps, filtered_scores)
        """
        if not timestamps:
            return [], []
        
        current_time = time.time()
        cutoff_time = current_time - (self.time_window_hours * 3600)
        
        filtered_ts = []
        filtered_scores = []
        
        for ts, score in zip(timestamps, scores):
            if ts >= cutoff_time:
                filtered_ts.append(ts)
                filtered_scores.append(score)
        
        return filtered_ts, filtered_scores
    
    def compute_risk_score(
        self,
        ip_address: str
    ) -> float:
        """
        Compute cumulative risk score for an IP (0-100 scale).
        
        Factors:
        - Anomaly frequency
        - Average threat severity
        - Request volume
        - Temporal decay of old events
        
        Args:
            ip_address: IP address to score
            
        Returns:
            Risk score (0-100)
        """
        if ip_address not in self.ip_data:
            return 0.0
        
        ip_info = self.ip_data[ip_address]
        
        # Filter to time window
        timestamps, scores = self._filter_by_time_window(
            ip_info['timestamps'],
            ip_info['threat_scores']
        )
        
        if not timestamps:
            return 0.0
        
        # Apply temporal decay
        decayed_scores = self._apply_temporal_decay(timestamps, scores)
        
        # Component 1: Anomaly frequency (0-40 points)
        anomaly_count = ip_info['anomaly_count']
        frequency_score = min(40, anomaly_count * 4)  # 10 anomalies = max
        
        # Component 2: Average severity (0-40 points)
        avg_severity = np.mean(decayed_scores) if decayed_scores else 0.0
        severity_score = avg_severity * 40  # Already 0-1, scale to 40
        
        # Component 3: Request volume (0-20 points)
        total_requests = ip_info['total_requests']
        volume_score = min(20, (total_requests / 100) * 20)  # 100 requests = max
        
        # Total risk score
        risk_score = frequency_score + severity_score + volume_score
        
        # Clip to [0, 100]
        risk_score = np.clip(risk_score, 0, 100)
        
        return float(risk_score)
    
    def update_ip_risk(
        self,
        ip_address: str,
        threat_score: float,
        is_anomaly: bool = False
    ) -> Dict[str, Any]:
        """
        Update IP risk based on new request.
        
        Args:
            ip_address: IP address
            threat_score: Threat score from ensemble (0-1)
            is_anomaly: Whether request was flagged as anomaly
            
        Returns:
            Updated IP risk information
        """
        current_time = time.time()
        
        ip_info = self.ip_data[ip_address]
        
        # Update counters
        ip_info['total_requests'] += 1
        if is_anomaly:
            ip_info['anomaly_count'] += 1
        
        # Add threat score and timestamp
        ip_info['threat_scores'].append(float(threat_score))
        ip_info['timestamps'].append(current_time)
        
        # Update first/last seen
        if ip_info['first_seen'] is None:
            ip_info['first_seen'] = datetime.utcnow().isoformat()
        ip_info['last_seen'] = datetime.utcnow().isoformat()
        
        # Compute new risk score
        risk_score = self.compute_risk_score(ip_address)
        ip_info['risk_score'] = risk_score
        
        # Check if IP should be flagged
        if risk_score >= self.high_risk_threshold and not ip_info['flagged']:
            ip_info['flagged'] = True
            ip_info['flagged_at'] = datetime.utcnow().isoformat()
            print(f"[ALERT] IP {ip_address} flagged as HIGH RISK (score: {risk_score:.1f})")
        
        return {
            'ip_address': ip_address,
            'risk_score': risk_score,
            'anomaly_count': ip_info['anomaly_count'],
            'total_requests': ip_info['total_requests'],
            'flagged': ip_info['flagged'],
            'anomaly_rate': ip_info['anomaly_count'] / max(1, ip_info['total_requests'])
        }
    
    def get_ip_summary(self, ip_address: str) -> Dict[str, Any]:
        """
        Get summary information for an IP.
        
        Args:
            ip_address: IP address
            
        Returns:
            Dictionary with IP summary
        """
        if ip_address not in self.ip_data:
            return {'error': 'IP not found'}
        
        ip_info = self.ip_data[ip_address]
        
        # Filter to time window
        timestamps, scores = self._filter_by_time_window(
            ip_info['timestamps'],
            ip_info['threat_scores']
        )
        
        summary = {
            'ip_address': ip_address,
            'risk_score': ip_info['risk_score'],
            'anomaly_count': ip_info['anomaly_count'],
            'total_requests': ip_info['total_requests'],
            'anomaly_rate': ip_info['anomaly_count'] / max(1, ip_info['total_requests']),
            'avg_threat_score': np.mean(scores) if scores else 0.0,
            'max_threat_score': np.max(scores) if scores else 0.0,
            'recent_requests_24h': len(timestamps),
            'flagged': ip_info['flagged'],
            'first_seen': ip_info['first_seen'],
            'last_seen': ip_info['last_seen']
        }
        
        return summary
    
    def get_high_risk_ips(self) -> List[Dict[str, Any]]:
        """
        Get list of high-risk IPs.
        
        Returns:
            List of high-risk IP summaries, sorted by risk score
        """
        high_risk = []
        
        for ip in self.ip_data:
            summary = self.get_ip_summary(ip)
            if summary['risk_score'] >= self.high_risk_threshold:
                high_risk.append(summary)
        
        # Sort by risk score (descending)
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return high_risk
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall IP tracking statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_ips = len(self.ip_data)
        
        if total_ips == 0:
            return {'message': 'No IPs tracked yet'}
        
        risk_scores = [ip_info['risk_score'] for ip_info in self.ip_data.values()]
        
        # Risk distribution
        low_risk = sum(1 for score in risk_scores if score < 30)
        medium_risk = sum(1 for score in risk_scores if 30 <= score < 70)
        high_risk = sum(1 for score in risk_scores if score >= 70)
        
        stats = {
            'total_ips': total_ips,
            'risk_distribution': {
                'low': low_risk,
                'medium': medium_risk,
                'high': high_risk
            },
            'risk_score_stats': {
                'mean': np.mean(risk_scores),
                'median': np.median(risk_scores),
                'std': np.std(risk_scores),
                'min': np.min(risk_scores),
                'max': np.max(risk_scores)
            },
            'flagged_ips': sum(1 for ip_info in self.ip_data.values() if ip_info['flagged'])
        }
        
        return stats
    
    def reset_ip(self, ip_address: str) -> None:
        """
        Reset risk tracking for an IP.
        
        Args:
            ip_address: IP to reset
        """
        if ip_address in self.ip_data:
            del self.ip_data[ip_address]
            print(f"[OK] Reset IP: {ip_address}")
        else:
            print(f"[WARN] IP not found: {ip_address}")
    
    def print_report(self) -> None:
        """Print formatted IP risk report."""
        print("\n" + "="*80)
        print("IP RISK TRACKING REPORT")
        print("="*80)
        
        stats = self.get_statistics()
        
        if 'message' in stats:
            print(stats['message'])
            return
        
        print(f"\nTotal IPs tracked: {stats['total_ips']}")
        print(f"Flagged IPs: {stats['flagged_ips']}")
        
        print(f"\nRisk Distribution:")
        print(f"  Low    (0-30):   {stats['risk_distribution']['low']:4d} IPs")
        print(f"  Medium (30-70):  {stats['risk_distribution']['medium']:4d} IPs")
        print(f"  High   (70-100): {stats['risk_distribution']['high']:4d} IPs")
        
        print(f"\nRisk Score Statistics:")
        print(f"  Mean:   {stats['risk_score_stats']['mean']:.2f}")
        print(f"  Median: {stats['risk_score_stats']['median']:.2f}")
        print(f"  Std:    {stats['risk_score_stats']['std']:.2f}")
        print(f"  Range:  {stats['risk_score_stats']['min']:.2f} - {stats['risk_score_stats']['max']:.2f}")
        
        # Show high-risk IPs
        high_risk_ips = self.get_high_risk_ips()
        
        if high_risk_ips:
            print(f"\n" + "="*80)
            print(f"HIGH RISK IPS (Score >= {self.high_risk_threshold})")
            print("="*80)
            print(f"{'IP Address':<20s} {'Risk':>8s} {'Anomalies':>12s} {'Total Req':>12s} {'Rate':>8s}")
            print("-"*80)
            
            for ip_info in high_risk_ips[:10]:  # Top 10
                print(f"{ip_info['ip_address']:<20s} {ip_info['risk_score']:>8.1f} "
                      f"{ip_info['anomaly_count']:>12d} {ip_info['total_requests']:>12d} "
                      f"{ip_info['anomaly_rate']*100:>7.1f}%")
        
        print("="*80)


def demo_ip_risk_engine():
    """
    Demo: IP risk tracking simulation.
    """
    print("="*80)
    print("IP RISK SCORING DEMO")
    print("="*80)
    
    # Initialize engine
    engine = IPRiskEngine(
        high_risk_threshold=70,
        time_window_hours=24
    )
    
    print(f"\nConfiguration:")
    print(f"  High risk threshold: {engine.high_risk_threshold}")
    print(f"  Time window: {engine.time_window_hours} hours")
    print(f"  Decay rate: {engine.decay_rate}")
    
    # Simulate normal traffic
    print("\n=== Simulating Normal Traffic ===")
    
    normal_ips = ['192.168.1.100', '192.168.1.101', '192.168.1.102']
    
    for ip in normal_ips:
        for _ in range(20):
            threat_score = np.random.uniform(0.1, 0.4)  # Low threat
            is_anomaly = threat_score > 0.35
            engine.update_ip_risk(ip, threat_score, is_anomaly)
    
    # Simulate suspicious traffic
    print("\n=== Simulating Suspicious Traffic ===")
    
    suspicious_ips = ['10.0.0.50', '10.0.0.51']
    
    for ip in suspicious_ips:
        for _ in range(30):
            threat_score = np.random.uniform(0.5, 0.8)  # High threat
            is_anomaly = threat_score > 0.6
            engine.update_ip_risk(ip, threat_score, is_anomaly)
    
    # Simulate attack traffic
    print("\n=== Simulating Attack Traffic ===")
    
    attack_ip = '172.16.0.99'
    
    for _ in range(50):
        threat_score = np.random.uniform(0.8, 0.99)  # Very high threat
        is_anomaly = True
        result = engine.update_ip_risk(attack_ip, threat_score, is_anomaly)
    
    print(f"\nAttack IP final score: {result['risk_score']:.1f}")
    
    # Print report
    engine.print_report()
    
    # Show detailed summaries
    print("\n=== IP Detailed Summaries ===")
    
    all_ips = normal_ips + suspicious_ips + [attack_ip]
    
    for ip in all_ips:
        summary = engine.get_ip_summary(ip)
        print(f"\n{ip}:")
        print(f"  Risk Score: {summary['risk_score']:.1f}")
        print(f"  Anomalies: {summary['anomaly_count']}/{summary['total_requests']} ({summary['anomaly_rate']*100:.1f}%)")
        print(f"  Avg Threat: {summary['avg_threat_score']:.3f}")
        print(f"  Flagged: {'YES' if summary['flagged'] else 'NO'}")
    
    # Save tracker
    engine.save_tracker()
    
    print("\n" + "="*80)
    print("IP RISK TRACKING COMPLETE")
    print("="*80)
    print(f"Tracker saved to: {engine.tracker_path}")


if __name__ == "__main__":
    demo_ip_risk_engine()
