"""
Integration Example: Using ML Models in Production API
========================================================
Demonstrates how to integrate the trained models into your existing
API monitoring system.

Author: Research Team
Date: February 2026
"""

from realtime_predictor import RealtimeAnomalyPredictor
import time
from datetime import datetime


class APIMonitoringIntegration:
    """Example integration with existing API monitoring"""
    
    def __init__(self):
        # Initialize predictor with trained models
        self.predictor = RealtimeAnomalyPredictor(
            models_dir='models',
            use_random_forest=True,
            use_isolation_forest=True
        )
        self.alert_threshold = 0.7  # Confidence threshold for alerts
    
    def collect_metrics(self) -> dict:
        """
        Collect real-time metrics from your API
        Replace this with your actual metric collection logic
        """
        # Example: This would come from your monitoring system
        # (Prometheus, Grafana, custom metrics collector, etc.)
        
        return {
            'avg_response_time': 150.5,
            'request_count': 45,
            'error_rate': 0.02,
            'five_xx_rate': 0.01,
            'four_xx_rate': 0.01,
            'payload_avg_size': 2048.0,
            'unique_ip_count': 25,
            'cpu_usage': 35.0,
            'memory_usage': 45.0
        }
    
    def send_alert(self, prediction: dict, metrics: dict):
        """
        Send alert when anomaly detected
        Replace with your alerting system (email, Slack, PagerDuty, etc.)
        """
        print("\n" + "="*70)
        print("⚠️  ANOMALY ALERT")
        print("="*70)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Prediction: {prediction['prediction_label']}")
        print(f"Confidence: {prediction['confidence']:.2%}")
        print(f"Anomaly Score: {prediction['anomaly_score']:.4f}")
        print(f"\nMetrics:")
        for key, value in metrics.items():
            print(f"  {key:<20s}: {value}")
        print("="*70 + "\n")
    
    def monitor_loop(self, interval_seconds: int = 10):
        """
        Main monitoring loop - collects metrics and detects anomalies
        
        Args:
            interval_seconds: How often to check (default 10s)
        """
        print(f"🔍 Starting API Monitoring (checking every {interval_seconds}s)")
        print(f"   Alert threshold: {self.alert_threshold:.0%} confidence\n")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                
                # Collect current metrics
                metrics = self.collect_metrics()
                
                # Run prediction
                result = self.predictor.predict(metrics)
                primary = result['primary_prediction']
                
                # Log status
                status = "🔴 ANOMALY" if primary['prediction'] == 1 else "🟢 NORMAL"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"Check #{iteration:3d} | {status} | "
                      f"Confidence: {primary['confidence']:.2%} | "
                      f"Score: {primary['anomaly_score']:.4f}")
                
                # Send alert if anomaly detected with high confidence
                if (primary['prediction'] == 1 and 
                    primary['confidence'] >= self.alert_threshold):
                    self.send_alert(primary, metrics)
                
                # Wait before next check
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring stopped by user")
            print(f"Total checks performed: {iteration}")


def example_batch_prediction():
    """Example: Batch prediction for historical data analysis"""
    print("="*70)
    print("📊 BATCH PREDICTION EXAMPLE")
    print("="*70)
    
    predictor = RealtimeAnomalyPredictor(models_dir='models')
    
    # Simulate batch of historical metrics
    historical_metrics = [
        {
            'avg_response_time': 150.0,
            'request_count': 50,
            'error_rate': 0.02,
            'five_xx_rate': 0.01,
            'four_xx_rate': 0.01,
            'payload_avg_size': 2000.0,
            'unique_ip_count': 25,
            'cpu_usage': 35.0,
            'memory_usage': 45.0
        },
        {
            'avg_response_time': 4500.0,  # Anomaly: High latency
            'request_count': 450,
            'error_rate': 0.65,
            'five_xx_rate': 0.50,
            'four_xx_rate': 0.15,
            'payload_avg_size': 15000.0,
            'unique_ip_count': 150,
            'cpu_usage': 85.0,
            'memory_usage': 92.0
        },
        {
            'avg_response_time': 180.0,
            'request_count': 48,
            'error_rate': 0.03,
            'five_xx_rate': 0.01,
            'four_xx_rate': 0.02,
            'payload_avg_size': 2100.0,
            'unique_ip_count': 27,
            'cpu_usage': 38.0,
            'memory_usage': 47.0
        }
    ]
    
    # Batch prediction
    results = predictor.predict_batch(historical_metrics)
    
    print(f"\nProcessed {len(results)} historical records:\n")
    for i, result in enumerate(results, 1):
        pred = result['primary_prediction']
        print(f"{i}. {pred['prediction_label']:<10s} "
              f"(confidence: {pred['confidence']:.2%}, "
              f"score: {pred['anomaly_score']:.4f})")
    
    print("\n" + "="*70 + "\n")


def example_rest_api_endpoint():
    """Example: Flask REST API endpoint for predictions"""
    
    example_code = '''
from flask import Flask, request, jsonify
from realtime_predictor import RealtimeAnomalyPredictor

app = Flask(__name__)
predictor = RealtimeAnomalyPredictor(models_dir='models')

@app.route('/predict', methods=['POST'])
def predict_anomaly():
    """API endpoint for anomaly prediction"""
    try:
        # Get metrics from request
        metrics = request.json
        
        # Validate required fields
        required_fields = [
            'avg_response_time', 'request_count', 'error_rate',
            'five_xx_rate', 'four_xx_rate', 'payload_avg_size',
            'unique_ip_count', 'cpu_usage', 'memory_usage'
        ]
        
        for field in required_fields:
            if field not in metrics:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Run prediction
        result = predictor.predict(metrics)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
'''
    
    print("="*70)
    print("🌐 REST API ENDPOINT EXAMPLE")
    print("="*70)
    print("\nSave this code as 'prediction_api.py':\n")
    print(example_code)
    print("\nThen run:")
    print("  python prediction_api.py")
    print("\nTest with curl:")
    print('''  curl -X POST http://localhost:5000/predict \\
    -H "Content-Type: application/json" \\
    -d '{
      "avg_response_time": 150.5,
      "request_count": 45,
      "error_rate": 0.02,
      "five_xx_rate": 0.01,
      "four_xx_rate": 0.01,
      "payload_avg_size": 2048.0,
      "unique_ip_count": 25,
      "cpu_usage": 35.0,
      "memory_usage": 45.0
    }'
''')
    print("="*70 + "\n")


def main():
    """Run integration examples"""
    print("\n" + "="*70)
    print("  PRODUCTION INTEGRATION EXAMPLES")
    print("="*70 + "\n")
    
    print("Choose an example to run:")
    print("  1. Real-time monitoring loop")
    print("  2. Batch prediction (historical data)")
    print("  3. REST API endpoint code")
    print("  4. All examples (code only)")
    print()
    
    choice = input("Enter choice (1-4): ").strip()
    
    if choice == '1':
        monitor = APIMonitoringIntegration()
        monitor.monitor_loop(interval_seconds=10)
    elif choice == '2':
        example_batch_prediction()
    elif choice == '3':
        example_rest_api_endpoint()
    elif choice == '4':
        example_batch_prediction()
        example_rest_api_endpoint()
        print("\n💡 To run real-time monitoring, choose option 1")
    else:
        print("Invalid choice")


if __name__ == '__main__':
    main()
