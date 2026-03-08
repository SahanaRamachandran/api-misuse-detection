import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import SessionLocal, APILog
from scipy.stats import entropy


def extract_features_from_logs(time_window_minutes=1, is_simulation=False, specific_endpoint=None):
    """
    Extract features from API logs using a sliding time window.
    
    STRICT SEPARATION: Only analyzes live OR simulation data, never mixed.
    
    Args:
        time_window_minutes: Time window size for feature extraction
        is_simulation: If True, extract from simulation logs only. If False, extract from live logs only.
        specific_endpoint: If provided, only extract features for this endpoint
    
    Features extracted per window:
    - req_count: Total number of requests
    - error_rate: Proportion of 4xx and 5xx status codes
    - avg_response_time: Average response time in ms
    - max_response_time: Maximum response time in ms
    - payload_mean: Average payload size
    - unique_endpoints: Number of distinct endpoints accessed
    - repeat_rate: Proportion of repeated endpoints
    - status_entropy: Shannon entropy of status code distribution
    """
    db = SessionLocal()
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # CRITICAL: Filter by mode to prevent contamination
        if is_simulation:
            query = db.query(APILog).filter(
                APILog.timestamp >= start_time,
                APILog.timestamp <= end_time,
                APILog.is_simulation == True
            )
            if specific_endpoint:
                query = query.filter(APILog.endpoint == specific_endpoint)
            logs = query.all()
        else:
            # Live mode: only real endpoint traffic
            query = db.query(APILog).filter(
                APILog.timestamp >= start_time,
                APILog.timestamp <= end_time,
                (APILog.is_simulation == False) | (APILog.is_simulation == None)
            )
            if specific_endpoint:
                query = query.filter(APILog.endpoint == specific_endpoint)
            logs = query.all()
        
        if not logs:
            return None
        
        df = pd.DataFrame([{
            'timestamp': log.timestamp,
            'endpoint': log.endpoint,
            'method': log.method,
            'response_time_ms': log.response_time_ms,
            'status_code': log.status_code,
            'payload_size': log.payload_size,
            'ip_address': log.ip_address,
            'user_id': log.user_id,
            'malicious_pattern': getattr(log, 'malicious_pattern', None),
            'query_params': getattr(log, 'query_params', ''),
            'request_count': getattr(log, 'request_count', 1)
        } for log in logs])
        
        req_count = len(df)
        
        error_count = len(df[df['status_code'] >= 400])
        error_rate = error_count / req_count if req_count > 0 else 0.0
        
        avg_response_time = df['response_time_ms'].mean()
        max_response_time = df['response_time_ms'].max()
        
        payload_mean = df['payload_size'].mean()
        
        unique_endpoints = df['endpoint'].nunique()
        
        endpoint_counts = df['endpoint'].value_counts()
        repeated_endpoints = (endpoint_counts > 1).sum()
        repeat_rate = repeated_endpoints / unique_endpoints if unique_endpoints > 0 else 0.0
        
        status_counts = df['status_code'].value_counts()
        status_probs = status_counts / status_counts.sum()
        status_entropy = entropy(status_probs)
        
        most_common_endpoint = df['endpoint'].mode()[0] if len(df) > 0 else "/unknown"
        most_common_method = df['method'].mode()[0] if len(df) > 0 else "GET"
        
        # Check for malicious patterns
        malicious_pattern = None
        if 'malicious_pattern' in df.columns:
            pattern_counts = df['malicious_pattern'].dropna()
            if len(pattern_counts) > 0:
                malicious_pattern = pattern_counts.mode()[0] if len(pattern_counts) > 0 else None
        
        # Count SQL injection indicators
        sql_keywords = 0
        xss_keywords = 0
        if 'query_params' in df.columns:
            query_str = ' '.join(df['query_params'].fillna('').astype(str))
            sql_patterns = ["'", "OR", "AND", "SELECT", "DROP", "UNION", "--", "admin"]
            xss_patterns = ["<script>", "<img", "javascript:", "<iframe", "onerror=", "onload="]
            sql_keywords = sum(1 for pattern in sql_patterns if pattern.lower() in query_str.lower())
            xss_keywords = sum(1 for pattern in xss_patterns if pattern.lower() in query_str.lower())
        
        # Calculate request rate for DDoS detection
        request_count = df['request_count'].sum() if 'request_count' in df.columns else req_count
        unique_ips = df['ip_address'].nunique()
        
        features = {
            'req_count': req_count,
            'error_rate': error_rate,
            'avg_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'payload_mean': payload_mean,
            'unique_endpoints': unique_endpoints,
            'repeat_rate': repeat_rate,
            'status_entropy': status_entropy,
            'endpoint': most_common_endpoint,
            'method': most_common_method,
            'ip_addresses': df['ip_address'].unique().tolist(),  # All unique IPs in this window
            'malicious_pattern': malicious_pattern,
            'sql_keywords_count': sql_keywords,
            'xss_keywords_count': xss_keywords,
            'request_count': request_count,
            'unique_ips': unique_ips
        }
        
        return features
        
    finally:
        db.close()


def prepare_training_data(hours_back=24):
    """
    Prepare training dataset by extracting features from historical logs.
    Creates multiple time windows to generate training samples.
    """
    db = SessionLocal()
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours_back)
        
        logs = db.query(APILog).filter(
            APILog.timestamp >= start_time,
            APILog.timestamp <= end_time
        ).order_by(APILog.timestamp).all()
        
        if not logs:
            return generate_synthetic_training_data()
        
        df = pd.DataFrame([{
            'timestamp': log.timestamp,
            'endpoint': log.endpoint,
            'method': log.method,
            'response_time_ms': log.response_time_ms,
            'status_code': log.status_code,
            'payload_size': log.payload_size,
            'ip_address': log.ip_address,
            'user_id': log.user_id
        } for log in logs])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        window_size = pd.Timedelta(minutes=1)
        step_size = pd.Timedelta(seconds=30)
        
        features_list = []
        
        current_start = df['timestamp'].min()
        max_time = df['timestamp'].max()
        
        while current_start + window_size <= max_time:
            current_end = current_start + window_size
            
            window_df = df[(df['timestamp'] >= current_start) & (df['timestamp'] < current_end)]
            
            if len(window_df) > 0:
                req_count = len(window_df)
                error_count = len(window_df[window_df['status_code'] >= 400])
                error_rate = error_count / req_count
                
                avg_response_time = window_df['response_time_ms'].mean()
                max_response_time = window_df['response_time_ms'].max()
                payload_mean = window_df['payload_size'].mean()
                unique_endpoints = window_df['endpoint'].nunique()
                
                endpoint_counts = window_df['endpoint'].value_counts()
                repeated_endpoints = (endpoint_counts > 1).sum()
                repeat_rate = repeated_endpoints / unique_endpoints if unique_endpoints > 0 else 0.0
                
                status_counts = window_df['status_code'].value_counts()
                status_probs = status_counts / status_counts.sum()
                status_entropy = entropy(status_probs)
                
                most_common_endpoint = window_df['endpoint'].mode()[0]
                most_common_method = window_df['method'].mode()[0]
                
                features_list.append({
                    'req_count': req_count,
                    'error_rate': error_rate,
                    'avg_response_time': avg_response_time,
                    'max_response_time': max_response_time,
                    'payload_mean': payload_mean,
                    'unique_endpoints': unique_endpoints,
                    'repeat_rate': repeat_rate,
                    'status_entropy': status_entropy,
                    'endpoint': most_common_endpoint,
                    'method': most_common_method
                })
            
            current_start += step_size
        
        if len(features_list) < 50:
            return generate_synthetic_training_data()
        
        return pd.DataFrame(features_list)
        
    finally:
        db.close()


def generate_synthetic_training_data(n_samples=500):
    """
    Generate synthetic training data for initial model training.
    This ensures the system can run even without historical data.
    """
    np.random.seed(42)
    
    normal_samples = int(n_samples * 0.70)
    heavy_samples = int(n_samples * 0.20)
    bot_samples = n_samples - normal_samples - heavy_samples
    
    data = []
    
    for i in range(normal_samples):
        data.append({
            'req_count': np.random.randint(5, 30),
            'error_rate': np.random.uniform(0.0, 0.15),
            'avg_response_time': np.random.uniform(50, 300),
            'max_response_time': np.random.uniform(100, 500),
            'payload_mean': np.random.uniform(100, 2000),
            'unique_endpoints': np.random.randint(2, 6),
            'repeat_rate': np.random.uniform(0.1, 0.5),
            'status_entropy': np.random.uniform(0.3, 1.2),
            'endpoint': np.random.choice(['/login', '/search', '/payment', '/health']),
            'method': np.random.choice(['GET', 'POST'])
        })
    
    for i in range(heavy_samples):
        data.append({
            'req_count': np.random.randint(30, 80),
            'error_rate': np.random.uniform(0.15, 0.35),
            'avg_response_time': np.random.uniform(300, 700),
            'max_response_time': np.random.uniform(500, 1200),
            'payload_mean': np.random.uniform(1500, 5000),
            'unique_endpoints': np.random.randint(3, 8),
            'repeat_rate': np.random.uniform(0.4, 0.7),
            'status_entropy': np.random.uniform(1.0, 2.0),
            'endpoint': np.random.choice(['/login', '/search', '/payment', '/health']),
            'method': np.random.choice(['GET', 'POST'])
        })
    
    for i in range(bot_samples):
        data.append({
            'req_count': np.random.randint(80, 200),
            'error_rate': np.random.uniform(0.30, 0.70),
            'avg_response_time': np.random.uniform(700, 1500),
            'max_response_time': np.random.uniform(1200, 3000),
            'payload_mean': np.random.uniform(50, 500),
            'unique_endpoints': np.random.randint(1, 3),
            'repeat_rate': np.random.uniform(0.7, 0.95),
            'status_entropy': np.random.uniform(0.1, 0.8),
            'endpoint': np.random.choice(['/login', '/search', '/payment', '/health']),
            'method': np.random.choice(['GET', 'POST'])
        })
    
    return pd.DataFrame(data)
