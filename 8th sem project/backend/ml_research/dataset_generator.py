"""
Research-Grade Dataset Generator for API Anomaly Detection
============================================================
Generates labeled telemetry data with randomized anomaly injection.

Features:
- 10-second metric collection intervals
- Randomized anomaly injection (endpoint, timing, duration, severity)
- Support for 4 anomaly types: traffic_burst, latency_spike, error_spike, timeout
- CSV export with labels

Author: Research Team
Date: February 2026
"""

import csv
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np


class AnomalyInjectionSchedule:
    """Manages randomized anomaly injection schedule"""
    
    ANOMALY_TYPES = ['traffic_burst', 'latency_spike', 'error_spike', 'timeout']
    
    def __init__(self, total_duration_seconds: int, anomaly_probability: float = 0.15):
        """
        Initialize anomaly schedule
        
        Args:
            total_duration_seconds: Total data collection duration
            anomaly_probability: Probability of anomaly occurrence (0.15 = 15%)
        """
        self.total_duration = total_duration_seconds
        self.anomaly_probability = anomaly_probability
        self.schedule = self._generate_schedule()
    
    def _generate_schedule(self) -> List[Dict]:
        """Generate randomized anomaly injection schedule"""
        schedule = []
        current_time = 0
        
        while current_time < self.total_duration:
            # Random gap before next anomaly (avg 200-600 seconds)
            gap = random.randint(200, 600)
            current_time += gap
            
            if current_time >= self.total_duration:
                break
            
            # Randomly decide if anomaly occurs
            if random.random() < self.anomaly_probability:
                anomaly = {
                    'start_time': current_time,
                    'duration': random.randint(30, 180),  # 30-180 seconds
                    'anomaly_type': random.choice(self.ANOMALY_TYPES),
                    'severity_multiplier': random.uniform(3.0, 10.0),  # 3x-10x
                    'endpoint': random.choice([
                        '/api/v1/users',
                        '/api/v1/products',
                        '/api/v1/orders',
                        '/api/v1/payments',
                        '/api/v1/search',
                        '/api/v1/analytics'
                    ])
                }
                schedule.append(anomaly)
                current_time += anomaly['duration']
        
        return schedule
    
    def get_active_anomaly(self, elapsed_time: int) -> Optional[Dict]:
        """Check if anomaly is active at given time"""
        for anomaly in self.schedule:
            if anomaly['start_time'] <= elapsed_time < anomaly['start_time'] + anomaly['duration']:
                return anomaly
        return None


class MetricsGenerator:
    """Generates realistic API metrics with normal and anomalous patterns"""
    
    # Baseline normal metrics
    BASELINE = {
        'avg_response_time': 150,      # ms
        'request_count': 50,           # per 10 seconds
        'error_rate': 0.02,            # 2%
        'five_xx_rate': 0.01,          # 1%
        'four_xx_rate': 0.01,          # 1%
        'payload_avg_size': 2048,      # bytes
        'unique_ip_count': 25,         # unique IPs
        'cpu_usage': 35.0,             # %
        'memory_usage': 45.0           # %
    }
    
    @staticmethod
    def generate_normal_metrics() -> Dict[str, float]:
        """Generate normal baseline metrics with realistic variance"""
        return {
            'avg_response_time': max(10, np.random.normal(
                MetricsGenerator.BASELINE['avg_response_time'], 30
            )),
            'request_count': max(1, int(np.random.normal(
                MetricsGenerator.BASELINE['request_count'], 10
            ))),
            'error_rate': max(0, min(0.1, np.random.normal(
                MetricsGenerator.BASELINE['error_rate'], 0.01
            ))),
            'five_xx_rate': max(0, min(0.05, np.random.normal(
                MetricsGenerator.BASELINE['five_xx_rate'], 0.005
            ))),
            'four_xx_rate': max(0, min(0.05, np.random.normal(
                MetricsGenerator.BASELINE['four_xx_rate'], 0.005
            ))),
            'payload_avg_size': max(100, np.random.normal(
                MetricsGenerator.BASELINE['payload_avg_size'], 500
            )),
            'unique_ip_count': max(1, int(np.random.normal(
                MetricsGenerator.BASELINE['unique_ip_count'], 5
            ))),
            'cpu_usage': max(0, min(100, np.random.normal(
                MetricsGenerator.BASELINE['cpu_usage'], 5
            ))),
            'memory_usage': max(0, min(100, np.random.normal(
                MetricsGenerator.BASELINE['memory_usage'], 8
            )))
        }
    
    @staticmethod
    def inject_anomaly(base_metrics: Dict[str, float], anomaly: Dict) -> Dict[str, float]:
        """Inject anomaly into base metrics"""
        metrics = base_metrics.copy()
        anomaly_type = anomaly['anomaly_type']
        multiplier = anomaly['severity_multiplier']
        
        if anomaly_type == 'traffic_burst':
            # High request count, moderate latency increase
            metrics['request_count'] = int(base_metrics['request_count'] * multiplier)
            metrics['avg_response_time'] *= (1 + multiplier * 0.3)
            metrics['unique_ip_count'] = int(base_metrics['unique_ip_count'] * (multiplier * 0.5))
            metrics['error_rate'] = min(0.4, base_metrics['error_rate'] * 2.5)
            metrics['cpu_usage'] = min(100, base_metrics['cpu_usage'] * 1.8)
            metrics['memory_usage'] = min(100, base_metrics['memory_usage'] * 1.6)
        
        elif anomaly_type == 'latency_spike':
            # High response time, increased errors
            metrics['avg_response_time'] *= multiplier
            metrics['error_rate'] = min(0.5, base_metrics['error_rate'] * 3.0)
            metrics['five_xx_rate'] = min(0.3, base_metrics['five_xx_rate'] * 4.0)
            metrics['cpu_usage'] = min(100, base_metrics['cpu_usage'] * 1.5)
        
        elif anomaly_type == 'error_spike':
            # High error rates, moderate latency
            metrics['error_rate'] = min(0.8, base_metrics['error_rate'] * multiplier * 2)
            metrics['five_xx_rate'] = min(0.6, base_metrics['five_xx_rate'] * multiplier * 2.5)
            metrics['four_xx_rate'] = min(0.3, base_metrics['four_xx_rate'] * multiplier * 1.5)
            metrics['avg_response_time'] *= 1.5
        
        elif anomaly_type == 'timeout':
            # Very high response time, high error rate
            metrics['avg_response_time'] = max(5000, base_metrics['avg_response_time'] * multiplier * 1.5)
            metrics['error_rate'] = min(0.9, 0.6 + random.uniform(0, 0.3))
            metrics['five_xx_rate'] = min(0.7, 0.5 + random.uniform(0, 0.2))
        
        return metrics


class DatasetGenerator:
    """Main dataset generator with CSV export"""
    
    def __init__(self, output_file: str = 'api_telemetry_dataset.csv'):
        """
        Initialize dataset generator
        
        Args:
            output_file: Output CSV filename
        """
        self.output_file = output_file
        self.data_points = []
    
    def generate_dataset(
        self,
        duration_minutes: int = 120,
        interval_seconds: int = 10,
        anomaly_probability: float = 0.15
    ) -> str:
        """
        Generate complete labeled dataset
        
        Args:
            duration_minutes: Total data collection duration
            interval_seconds: Metric collection interval (default 10s)
            anomaly_probability: Probability of anomaly occurrence
        
        Returns:
            Path to generated CSV file
        """
        total_seconds = duration_minutes * 60
        total_samples = total_seconds // interval_seconds
        
        print(f"🔬 Generating Research Dataset")
        print(f"   Duration: {duration_minutes} minutes ({total_seconds} seconds)")
        print(f"   Interval: {interval_seconds} seconds")
        print(f"   Expected samples: {total_samples}")
        print(f"   Anomaly probability: {anomaly_probability * 100}%\n")
        
        # Generate anomaly schedule
        schedule = AnomalyInjectionSchedule(total_seconds, anomaly_probability)
        print(f"   Generated {len(schedule.schedule)} anomaly events\n")
        
        # Print anomaly schedule
        print("📅 Anomaly Schedule:")
        for i, anomaly in enumerate(schedule.schedule, 1):
            start_min = anomaly['start_time'] // 60
            duration_sec = anomaly['duration']
            print(f"   {i}. {anomaly['anomaly_type']:<15} @ {start_min:3d}m, "
                  f"duration={duration_sec:3d}s, "
                  f"severity={anomaly['severity_multiplier']:.2f}x, "
                  f"endpoint={anomaly['endpoint']}")
        
        print(f"\n⏳ Generating {total_samples} data points...\n")
        
        # Generate data points
        for sample_idx in range(total_samples):
            elapsed_time = sample_idx * interval_seconds
            
            # Check if anomaly is active
            active_anomaly = schedule.get_active_anomaly(elapsed_time)
            
            # Generate base metrics
            base_metrics = MetricsGenerator.generate_normal_metrics()
            
            if active_anomaly:
                # Inject anomaly
                metrics = MetricsGenerator.inject_anomaly(base_metrics, active_anomaly)
                label = 1
                anomaly_type = active_anomaly['anomaly_type']
            else:
                # Normal metrics
                metrics = base_metrics
                label = 0
                anomaly_type = 'normal'
            
            # Create data point
            data_point = {
                'timestamp': datetime.now() + timedelta(seconds=elapsed_time),
                'label': label,
                'anomaly_type': anomaly_type,
                **metrics
            }
            
            self.data_points.append(data_point)
            
            # Progress indicator
            if (sample_idx + 1) % 100 == 0 or sample_idx == total_samples - 1:
                progress = ((sample_idx + 1) / total_samples) * 100
                anomaly_count = sum(1 for dp in self.data_points if dp['label'] == 1)
                print(f"   Progress: {progress:5.1f}% | "
                      f"Samples: {sample_idx + 1:4d}/{total_samples} | "
                      f"Anomalies: {anomaly_count:3d}")
        
        # Save to CSV
        self._save_to_csv()
        
        # Print statistics
        self._print_statistics()
        
        return self.output_file
    
    def _save_to_csv(self):
        """Save dataset to CSV file"""
        if not self.data_points:
            raise ValueError("No data points to save")
        
        fieldnames = [
            'timestamp',
            'avg_response_time',
            'request_count',
            'error_rate',
            'five_xx_rate',
            'four_xx_rate',
            'payload_avg_size',
            'unique_ip_count',
            'cpu_usage',
            'memory_usage',
            'label',
            'anomaly_type'
        ]
        
        with open(self.output_file, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for data_point in self.data_points:
                writer.writerow({
                    'timestamp': data_point['timestamp'].isoformat(),
                    'avg_response_time': round(data_point['avg_response_time'], 2),
                    'request_count': data_point['request_count'],
                    'error_rate': round(data_point['error_rate'], 4),
                    'five_xx_rate': round(data_point['five_xx_rate'], 4),
                    'four_xx_rate': round(data_point['four_xx_rate'], 4),
                    'payload_avg_size': round(data_point['payload_avg_size'], 2),
                    'unique_ip_count': data_point['unique_ip_count'],
                    'cpu_usage': round(data_point['cpu_usage'], 2),
                    'memory_usage': round(data_point['memory_usage'], 2),
                    'label': data_point['label'],
                    'anomaly_type': data_point['anomaly_type']
                })
        
        print(f"\n✅ Dataset saved to: {self.output_file}")
    
    def _print_statistics(self):
        """Print dataset statistics"""
        total_samples = len(self.data_points)
        anomaly_samples = sum(1 for dp in self.data_points if dp['label'] == 1)
        normal_samples = total_samples - anomaly_samples
        
        # Count by anomaly type
        anomaly_type_counts = {}
        for dp in self.data_points:
            atype = dp['anomaly_type']
            anomaly_type_counts[atype] = anomaly_type_counts.get(atype, 0) + 1
        
        print("\n" + "="*60)
        print("📊 DATASET STATISTICS")
        print("="*60)
        print(f"Total samples:     {total_samples:5d}")
        print(f"Normal samples:    {normal_samples:5d} ({normal_samples/total_samples*100:5.2f}%)")
        print(f"Anomaly samples:   {anomaly_samples:5d} ({anomaly_samples/total_samples*100:5.2f}%)")
        print(f"\nAnomaly Type Distribution:")
        for atype, count in sorted(anomaly_type_counts.items()):
            if atype != 'normal':
                print(f"  {atype:<20s}: {count:4d} samples ({count/total_samples*100:5.2f}%)")
        print("="*60 + "\n")


def main():
    """Main execution function"""
    # Configuration
    DURATION_MINUTES = 120      # 2 hours of data
    INTERVAL_SECONDS = 10       # Collect metrics every 10 seconds
    ANOMALY_PROBABILITY = 0.15  # 15% chance of anomaly occurrence
    OUTPUT_FILE = 'api_telemetry_dataset.csv'
    
    # Generate dataset
    generator = DatasetGenerator(output_file=OUTPUT_FILE)
    output_path = generator.generate_dataset(
        duration_minutes=DURATION_MINUTES,
        interval_seconds=INTERVAL_SECONDS,
        anomaly_probability=ANOMALY_PROBABILITY
    )
    
    print(f"✨ Dataset generation complete!")
    print(f"📁 File: {output_path}")
    print(f"\nNext steps:")
    print(f"  1. Run preprocessing.py to prepare data")
    print(f"  2. Run train_models.py to train ML models")
    print(f"  3. Run evaluate.py to assess performance")


if __name__ == '__main__':
    main()
