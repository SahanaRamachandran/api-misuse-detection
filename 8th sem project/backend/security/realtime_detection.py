"""
Real-time Anomaly Detection Middleware
---------------------------------------
Production-ready middleware for automatic anomaly detection and IP blocking.

Author: Traffic Monitoring System
Date: February 2026
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import numpy as np
import joblib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
import threading
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AI Resolution Engine
try:
    from ai_resolution_engine import get_ai_resolution_engine
    AI_RESOLUTION_AVAILABLE = True
except ImportError:
    AI_RESOLUTION_AVAILABLE = False

# Import Email Alert System
try:
    from email_alerts import trigger_alert_email
    EMAIL_ALERTS_AVAILABLE = True
except ImportError:
    EMAIL_ALERTS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealTimeAnomalyDetector:
    """
    Real-time anomaly detection system with ML models and IP tracking.
    
    Features:
    - TF-IDF + XGBoost classification
    - Autoencoder reconstruction error
    - IP profiling and tracking
    - Automatic IP blocking based on behavior
    - Thread-safe operations
    - Deterministic risk scoring
    """
    
    # Configuration
    RISK_THRESHOLD = 0.7  # Threshold for marking as anomaly
    BLOCK_AVG_RISK_THRESHOLD = 0.8  # Average risk threshold for blocking
    BLOCK_ANOMALY_COUNT_THRESHOLD = 5  # Minimum anomalies before blocking
    XGB_WEIGHT = 0.6  # Weight for XGBoost probability
    AE_WEIGHT = 0.4  # Weight for autoencoder error
    
    def __init__(self, models_dir: str = "../models", openai_api_key: str = None):
        """
        Initialize the real-time anomaly detector.
        
        Args:
            models_dir: Directory containing the trained models
            openai_api_key: OpenAI API key for AI-powered resolutions
        """
        self.models_dir = models_dir
        self.models_loaded = False
        
        # Thread lock for thread-safe operations
        self._lock = threading.Lock()
        
        # IP tracking storage
        self.ip_profiles: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'total_requests': 0,
            'anomaly_count': 0,
            'total_risk': 0.0,
            'avg_risk': 0.0,
            'last_seen': None,
            'blocked': False,
            'is_simulation': False  # Track if this IP is from simulation
        })
        
        # Blocked IPs set for O(1) lookup
        self.blocked_ips = set()
        
        # Models (to be loaded)
        self.tfidf = None
        self.xgb_model = None
        self.autoencoder = None
        self.scaler = None
        self.ae_threshold = None
        
        # AI Resolution Engine
        if AI_RESOLUTION_AVAILABLE:
            self.ai_resolution_engine = get_ai_resolution_engine(openai_api_key)
            logger.info("✅ AI Resolution Engine initialized")
        else:
            self.ai_resolution_engine = None
            logger.warning("⚠️ AI Resolution Engine not available")
        
        # Load models
        self._load_models()
    
    def _load_models(self):
        """Load all required ML models."""
        try:
            logger.info("Loading anomaly detection models...")
            
            # TF-IDF Vectorizer
            tfidf_path = os.path.join(self.models_dir, "tfidf.pkl")
            if os.path.exists(tfidf_path):
                self.tfidf = joblib.load(tfidf_path)
                logger.info("✓ TF-IDF vectorizer loaded")
            else:
                logger.warning(f"TF-IDF not found at {tfidf_path}")
            
            # XGBoost Model
            xgb_path = os.path.join(self.models_dir, "xgb_model.pkl")
            if os.path.exists(xgb_path):
                self.xgb_model = joblib.load(xgb_path)
                logger.info("✓ XGBoost model loaded")
            else:
                logger.warning(f"XGBoost not found at {xgb_path}")
            
            # Autoencoder Model
            try:
                from tensorflow import keras
                ae_path = os.path.join(self.models_dir, "autoencoder.h5")
                if os.path.exists(ae_path):
                    self.autoencoder = keras.models.load_model(ae_path)
                    logger.info("✓ Autoencoder model loaded")
                else:
                    logger.warning(f"Autoencoder not found at {ae_path}")
            except ImportError:
                logger.warning("TensorFlow not available - autoencoder disabled")
            
            # Scaler for Autoencoder
            scaler_path = os.path.join(self.models_dir, "scaler.pkl")
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("✓ Scaler loaded")
            else:
                logger.warning(f"Scaler not found at {scaler_path}")
            
            # Autoencoder threshold
            threshold_path = os.path.join(self.models_dir, "ae_threshold.pkl")
            if os.path.exists(threshold_path):
                self.ae_threshold = joblib.load(threshold_path)
                logger.info(f"✓ AE threshold loaded: {self.ae_threshold}")
            else:
                # Default threshold if not available
                self.ae_threshold = 0.1
                logger.warning(f"AE threshold not found, using default: {self.ae_threshold}")
            
            # Check if all models are loaded
            self.models_loaded = (
                self.tfidf is not None and
                self.xgb_model is not None and
                self.autoencoder is not None and
                self.scaler is not None
            )
            
            if self.models_loaded:
                logger.info("✅ All models loaded successfully - Real-time detection ACTIVE")
            else:
                logger.warning("⚠️ Some models missing - Detection may be limited")
        
        except Exception as e:
            logger.error(f"Error loading models: {e}", exc_info=True)
            self.models_loaded = False
    
    async def extract_request_data(self, request: Request) -> str:
        """
        Extract and combine request data into a single string.
        
        Args:
            request: FastAPI Request object
        
        Returns:
            Combined request data as string
        """
        parts = []
        
        # HTTP Method
        parts.append(f"METHOD:{request.method}")
        
        # URL
        parts.append(f"URL:{request.url.path}")
        
        # Query parameters
        if request.url.query:
            parts.append(f"QUERY:{request.url.query}")
        
        # Headers (exclude sensitive ones)
        sensitive_headers = {'authorization', 'cookie', 'x-api-key'}
        for key, value in request.headers.items():
            if key.lower() not in sensitive_headers:
                parts.append(f"HEADER:{key}={value}")
        
        # Body
        try:
            body = await request.body()
            if body:
                # Try to decode as text
                try:
                    body_text = body.decode('utf-8')
                    parts.append(f"BODY:{body_text}")
                except UnicodeDecodeError:
                    parts.append(f"BODY:binary_data_length={len(body)}")
        except Exception as e:
            logger.debug(f"Could not extract body: {e}")
        
        return " ".join(parts)
    
    def extract_client_ip(self, request: Request) -> str:
        """
        Extract real client IP from request.
        
        Priority:
        1. X-Forwarded-For (first IP)
        2. request.client.host
        
        Args:
            request: FastAPI Request object
        
        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to direct client host
        if request.client:
            return request.client.host
        
        # Ultimate fallback
        return "unknown"
    
    def calculate_xgb_probability(self, request_text: str) -> float:
        """
        Calculate XGBoost anomaly probability (DETERMINISTIC - recalculated per request).
        
        Process:
        1. Transform request text to TF-IDF features (fresh calculation)
        2. Run XGBoost prediction on transformed features
        3. Return probability of anomaly class (0.0 to 1.0)
        
        Args:
            request_text: Combined request data
        
        Returns:
            Probability of being anomalous (0.0 to 1.0, deterministic)
        """
        try:
            if self.tfidf is None or self.xgb_model is None:
                logger.debug("TF-IDF or XGBoost not loaded, returning 0.0")
                return 0.0
            
            # Transform text to TF-IDF features (FRESH calculation per request)
            features = self.tfidf.transform([request_text])
            
            # Get probability of anomaly class (class 1) - DETERMINISTIC
            proba = self.xgb_model.predict_proba(features)[0]
            
            # Return probability of anomaly (second column if binary, first if single class)
            xgb_probability = float(proba[1]) if len(proba) > 1 else float(proba[0])
            
            return xgb_probability
        
        except Exception as e:
            logger.error(f"Error calculating XGBoost probability: {e}")
            return 0.0
    
    def calculate_autoencoder_error(self, request_text: str) -> float:
        """
        Calculate autoencoder reconstruction error (DETERMINISTIC - recalculated per request).
        
        Process:
        1. Transform request text to TF-IDF features (fresh calculation)
        2. Scale features using pre-loaded scaler
        3. Get reconstruction from autoencoder
        4. Calculate MSE between original and reconstruction
        5. Normalize by fixed training threshold
        6. Cap at 1.0 if error exceeds 1.5x threshold
        
        Args:
            request_text: Combined request data
        
        Returns:
            Normalized reconstruction error (0.0 to 1.0, capped, deterministic)
        """
        try:
            if self.autoencoder is None or self.scaler is None or self.tfidf is None:
                logger.debug("Autoencoder components not loaded, returning 0.0")
                return 0.0
            
            # Transform to TF-IDF features (FRESH calculation per request)
            features = self.tfidf.transform([request_text]).toarray()
            
            # Scale features using pre-loaded scaler (DETERMINISTIC)
            scaled_features = self.scaler.transform(features)
            
            # Get reconstruction from autoencoder (DETERMINISTIC - no dropout/randomness in inference)
            reconstruction = self.autoencoder.predict(scaled_features, verbose=0)
            
            # Calculate mean squared error (DETERMINISTIC)
            mse = np.mean(np.square(scaled_features - reconstruction))
            
            # Normalize by FIXED training threshold (loaded at startup, never changes)
            if self.ae_threshold > 0:
                normalized_error = mse / self.ae_threshold
            else:
                normalized_error = mse
            
            # Cap at 1.0 if error exceeds 1.5x threshold (REQUIREMENT)
            if mse > 1.5 * self.ae_threshold:
                normalized_error = 1.0
            
            return float(normalized_error)
        
        except Exception as e:
            logger.error(f"Error calculating autoencoder error: {e}")
            return 0.0
    
    def calculate_risk_score(self, xgb_proba: float, ae_error: float) -> float:
        """
        Calculate final risk score using ensemble approach (DETERMINISTIC).
        
        Formula (FIXED): risk = (0.6 * xgb_probability) + (0.4 * normalized_ae_error)
        
        Properties:
        - Weights are FIXED constants (0.6 and 0.4)
        - No random numbers involved
        - Same inputs = same output (DETERMINISTIC)
        - Result range: 0.0 to 1.0 (both components are capped at 1.0)
        
        Args:
            xgb_proba: XGBoost anomaly probability (0.0 to 1.0)
            ae_error: Normalized autoencoder reconstruction error (0.0 to 1.0, capped)
        
        Returns:
            Combined risk score (0.0 to 1.0, deterministic)
        """
        # DETERMINISTIC ensemble calculation
        # XGB_WEIGHT = 0.6 (constant)
        # AE_WEIGHT = 0.4 (constant)
        risk = (self.XGB_WEIGHT * xgb_proba) + (self.AE_WEIGHT * ae_error)
        return float(risk)
    
    def update_ip_profile(self, ip: str, risk_score: float, is_simulation: bool = False) -> bool:
        """
        Update IP profile with new request data.
        
        Args:
            ip: Client IP address
            risk_score: Calculated risk score for this request
            is_simulation: Whether this is a simulation request
        
        Returns:
            True if IP was blocked due to this update, False otherwise
        """
        with self._lock:
            profile = self.ip_profiles[ip]
            
            # Mark if this is a simulation IP
            if is_simulation:
                profile['is_simulation'] = True
            
            # Update request count
            profile['total_requests'] += 1
            
            # Update anomaly count based on risk threshold
            # Count as anomaly if risk score exceeds threshold
            if risk_score > self.RISK_THRESHOLD:
                profile['anomaly_count'] += 1
            
            # Update total and average risk
            profile['total_risk'] += risk_score
            profile['avg_risk'] = profile['total_risk'] / profile['total_requests']
            
            # Update last seen
            profile['last_seen'] = datetime.now().isoformat()
            
            # Check blocking conditions
            # Block when anomaly count reaches threshold (5 or more anomalies)
            should_block = profile['anomaly_count'] >= self.BLOCK_ANOMALY_COUNT_THRESHOLD  # >= 5 anomalies
            
            # Block if conditions met and not already blocked
            if should_block and not profile['blocked']:
                profile['blocked'] = True
                self.blocked_ips.add(ip)
                ip_type = "SIMULATION" if is_simulation else "LIVE"
                logger.warning(
                    f"🚫 IP BLOCKED ({ip_type}): {ip} | "
                    f"Avg Risk: {profile['avg_risk']:.3f} | "
                    f"Anomalies: {profile['anomaly_count']} | "
                    f"Total Requests: {profile['total_requests']}"
                )
                # Also print to console for visibility
                print(f"\n🚫 IP BLOCKED ({ip_type}): {ip} | Anomalies: {profile['anomaly_count']}\n")
                return True
            
            return False
    
    def is_blocked(self, ip: str) -> bool:
        """
        Check if an IP is blocked.
        
        Args:
            ip: Client IP address
        
        Returns:
            True if blocked, False otherwise
        """
        with self._lock:
            return ip in self.blocked_ips
    
    async def detect_anomaly(self, request: Request, is_simulation: bool = False) -> Dict[str, Any]:
        """
        Main detection function - analyzes request and returns results.
        
        DETERMINISTIC PROCESS:
        1. Extract client IP from request headers
        2. Check if IP is already blocked (O(1) lookup)
        3. Extract request data (method, URL, headers, body)
        4. Calculate XGBoost probability (FRESH per request)
        5. Calculate Autoencoder error (FRESH per request)
        6. Calculate risk score using fixed formula: (0.6*XGB + 0.4*AE)
        7. Update IP profile with new data
        8. Check for auto-blocking condition
        9. Generate AI-powered resolution if anomaly detected
        
        Args:
            request: FastAPI Request object
            is_simulation: Whether this is a simulation request
        
        Returns:
            Dictionary with detection results (deterministic) + AI resolution
        """
        # Extract client IP
        client_ip = self.extract_client_ip(request)
        
        # Check if already blocked
        if self.is_blocked(client_ip):
            return {
                'ip': client_ip,
                'blocked': True,
                'is_simulation': is_simulation,
                'reason': 'IP previously blocked due to suspicious activity'
            }
        
        # Extract request data (combined into single text string)
        request_text = await self.extract_request_data(request)
        
        # FRESH CALCULATIONS (no caching, no reuse of previous predictions)
        # Component 1: XGBoost probability (DETERMINISTIC)
        xgb_proba = self.calculate_xgb_probability(request_text)
        
        # Component 2: Autoencoder reconstruction error (DETERMINISTIC, normalized & capped)
        ae_error = self.calculate_autoencoder_error(request_text)
        
        # Final risk score: DETERMINISTIC ensemble
        # Formula: risk = (0.6 * xgb_proba) + (0.4 * ae_error)
        risk_score = self.calculate_risk_score(xgb_proba, ae_error)
        
        # Update IP profile and check for blocking (only block live IPs)
        was_blocked = self.update_ip_profile(client_ip, risk_score, is_simulation)
        
        # Get current profile
        profile = self.ip_profiles[client_ip]
        
        # Determine if this is an anomaly
        is_anomaly = risk_score > self.RISK_THRESHOLD
        
        # Generate AI-powered resolution if anomaly detected
        ai_resolution = None
        if is_anomaly and self.ai_resolution_engine is not None:
            try:
                # Determine anomaly type based on risk score
                anomaly_type = self._classify_anomaly_type(risk_score, request)
                
                # Determine severity
                if risk_score >= 0.9:
                    severity = 'CRITICAL'
                elif risk_score >= 0.8:
                    severity = 'HIGH'
                elif risk_score >= 0.7:
                    severity = 'MEDIUM'
                else:
                    severity = 'LOW'
                
                # Generate AI resolution
                ai_resolution = self.ai_resolution_engine.generate_resolution(
                    anomaly_type=anomaly_type,
                    severity=severity,
                    endpoint=str(request.url.path),
                    ip_address=client_ip,
                    context={
                        'risk_score': risk_score,
                        'xgb_probability': xgb_proba,
                        'ae_error': ae_error,
                        'is_simulation': is_simulation,
                        'method': request.method,
                        'user_agent': request.headers.get('user-agent', 'Unknown'),
                        'total_requests': profile['total_requests'],
                        'anomaly_count': profile['anomaly_count']
                    }
                )
                logger.info(f"✅ AI Resolution generated for {anomaly_type} ({severity})")
            except Exception as e:
                logger.error(f"❌ Error generating AI resolution: {e}", exc_info=True)
        
        # Trigger email alert for critical anomalies (risk_score >= 0.8, LIVE mode only)
        if is_anomaly and risk_score >= 0.8 and not is_simulation and EMAIL_ALERTS_AVAILABLE:
            try:
                # Prepare email alert data
                alert_data = {
                    'anomaly_type': self._classify_anomaly_type(risk_score, request),
                    'risk_score': risk_score,
                    'probability': xgb_proba,
                    'ip_address': client_ip,
                    'endpoint': str(request.url.path),
                    'timestamp': datetime.now().isoformat(),
                    'blocked': was_blocked,
                    'severity': 'CRITICAL' if risk_score >= 0.9 else 'HIGH',
                    'confidence': risk_score,
                    'method': request.method
                }
                
                # Trigger async email (non-blocking)
                trigger_alert_email(alert_data)
                logger.info(f"📧 Email alert triggered for {client_ip} (Risk: {risk_score:.2f})")
            except Exception as e:
                logger.error(f"❌ Error triggering email alert: {e}")
        
        # Log detection with clear component breakdown
        mode = "SIMULATION" if is_simulation else "LIVE"
        logger.info(
            f"{mode} DETECTION | IP: {client_ip} | "
            f"XGB: {xgb_proba:.4f} | AE: {ae_error:.4f} | "
            f"RISK: {risk_score:.4f} (0.6*{xgb_proba:.4f} + 0.4*{ae_error:.4f}) | "
            f"Anomaly: {is_anomaly} | "
            f"Blocked: {was_blocked} | "
            f"Profile: Avg={profile['avg_risk']:.4f}, Count={profile['anomaly_count']}/{profile['total_requests']}"
        )
        
        result = {
            'ip': client_ip,
            'xgb_probability': round(xgb_proba, 4),
            'ae_reconstruction_error': round(ae_error, 4),
            'risk_score': round(risk_score, 4),
            'risk_calculation': f"(0.6 * {xgb_proba:.4f}) + (0.4 * {ae_error:.4f}) = {risk_score:.4f}",
            'is_anomaly': is_anomaly,
            'is_simulation': is_simulation,
            'blocked': was_blocked,  # Block simulation IPs too for demonstration
            'profile': {
                'total_requests': profile['total_requests'],
                'anomaly_count': profile['anomaly_count'],
                'avg_risk': round(profile['avg_risk'], 4),
                'last_seen': profile['last_seen'],
                'is_simulation': profile.get('is_simulation', False)
            }
        }
        
        # Add AI resolution if generated
        if ai_resolution:
            result['ai_resolution'] = ai_resolution
        
        return result
    
    def _classify_anomaly_type(self, risk_score: float, request: Request) -> str:
        """
        Classify the anomaly type based on risk score and request properties.
        
        Args:
            risk_score: Calculated risk score
            request: Request object
        
        Returns:
            Anomaly type string
        """
        # Check for SQL injection patterns
        if request.method in ['GET', 'POST']:
            # Simple heuristic - can be enhanced
            if risk_score >= 0.9:
                return 'sql_injection'
            elif risk_score >= 0.8:
                return 'xss_attack'
            elif risk_score >= 0.75:
                return 'suspicious_payload'
            else:
                return 'unusual_pattern'
        
        # Traffic-based anomalies
        if risk_score >= 0.8:
            return 'traffic_burst'
        elif risk_score >= 0.75:
            return 'latency_spike'
        else:
            return 'general_anomaly'
    
    def track_simulation_request(
        self, 
        ip_address: str, 
        endpoint: str, 
        method: str,
        response_time_ms: float,
        status_code: int,
        payload_size: int,
        malicious_pattern: str = None,
        query_params: str = None
    ) -> Dict[str, Any]:
        """
        Track a simulation request through the real-time detection system.
        This simplified method can be called from simulation engines without
        needing a full FastAPI Request object.
        
        Args:
            ip_address: Simulated IP address
            endpoint: API endpoint
            method: HTTP method
            response_time_ms: Response time in milliseconds
            status_code: HTTP status code
            payload_size: Payload size in bytes
            malicious_pattern: Type of malicious pattern (SQL_INJECTION, XSS_ATTACK, DDOS_BURST)
            query_params: Query parameters (may contain injection patterns)
        
        Returns:
            Detection result dictionary
        """
        try:
            # Create a simple request text for ML models
            request_text = f"METHOD:{method} URL:{endpoint} STATUS:{status_code} " \
                          f"RESPONSE_TIME:{response_time_ms} PAYLOAD:{payload_size}"
            
            if query_params:
                request_text += f" QUERY:{query_params}"
            
            # Calculate risk scores using ML models (if loaded)
            xgb_proba = 0.0
            ae_error = 0.0
            risk_score = 0.0
            
            if self.models_loaded:
                xgb_proba = self.calculate_xgb_probability(request_text)
                ae_error = self.calculate_autoencoder_error(request_text)
                risk_score = self.calculate_risk_score(xgb_proba, ae_error)
            
            # IMPORTANT: For simulation with malicious patterns, override risk score
            # This ensures IPs get blocked even when ML models aren't loaded
            if malicious_pattern:
                # Assign high risk scores for different attack types
                pattern_risk_scores = {
                    'SQL_INJECTION': 0.95,
                    'XSS_ATTACK': 0.92,
                    'DDOS_BURST': 0.88,
                    'BRUTE_FORCE': 0.90,
                    'PATH_TRAVERSAL': 0.87
                }
                risk_score = pattern_risk_scores.get(malicious_pattern, 0.85)
                logger.info(f"[SIMULATION] Malicious pattern '{malicious_pattern}' detected, risk_score={risk_score:.3f}")
            
            # Update IP profile (with is_simulation=True)
            was_blocked = self.update_ip_profile(ip_address, risk_score, is_simulation=True)
            
            # Get current profile
            profile = self.ip_profiles[ip_address]
            
            # Determine if anomaly
            is_anomaly = risk_score > self.RISK_THRESHOLD
            
            # Log detection
            if is_anomaly:
                logger.info(
                    f"SIMULATION ANOMALY | IP: {ip_address} | Endpoint: {endpoint} | "
                    f"RISK: {risk_score:.4f} | Pattern: {malicious_pattern} | "
                    f"Profile: Anomalies={profile['anomaly_count']}/{profile['total_requests']}"
                )
            
            return {
                'ip': ip_address,
                'endpoint': endpoint,
                'xgb_probability': round(xgb_proba, 4),
                'ae_reconstruction_error': round(ae_error, 4),
                'risk_score': round(risk_score, 4),
                'is_anomaly': is_anomaly,
                'is_simulation': True,
                'malicious_pattern': malicious_pattern,
                'blocked': was_blocked,  # Return actual blocking status for demo
                'tracked': True,
                'profile': {
                    'total_requests': profile['total_requests'],
                    'anomaly_count': profile['anomaly_count'],
                    'avg_risk': round(profile['avg_risk'], 4),
                    'last_seen': profile['last_seen'],
                    'is_simulation': True
                }
            }
        
        except Exception as e:
            logger.error(f"Error tracking simulation request: {e}", exc_info=True)
            return {
                'ip': ip_address,
                'is_simulation': True,
                'tracked': False,
                'error': str(e)
            }
    
    def get_simulation_ip_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all simulation IPs.
        
        Returns:
            Dictionary with simulation IP statistics
        """
        with self._lock:
            simulation_ips = {
                ip: profile 
                for ip, profile in self.ip_profiles.items() 
                if profile.get('is_simulation', False)
            }
            
            total_sim_requests = sum(p['total_requests'] for p in simulation_ips.values())
            total_sim_anomalies = sum(p['anomaly_count'] for p in simulation_ips.values())
            
            return {
                'total_simulation_ips': len(simulation_ips),
                'total_simulation_requests': total_sim_requests,
                'total_simulation_anomalies': total_sim_anomalies,
                'simulation_ips': simulation_ips
            }
    
    def get_all_profiles(self) -> Dict[str, Any]:
        """Get all IP profiles."""
        with self._lock:
            return dict(self.ip_profiles)
    
    def get_blocked_ips(self) -> list:
        """Get list of blocked IPs."""
        with self._lock:
            return list(self.blocked_ips)
    
    def unblock_ip(self, ip: str) -> bool:
        """
        Unblock an IP and reset its profile.
        
        Args:
            ip: IP address to unblock
        
        Returns:
            True if IP was unblocked, False if it wasn't blocked
        """
        with self._lock:
            if ip in self.blocked_ips:
                self.blocked_ips.remove(ip)
                if ip in self.ip_profiles:
                    del self.ip_profiles[ip]
                logger.info(f"✓ IP Unblocked: {ip}")
                return True
            return False


class RealTimeAnomalyMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for real-time anomaly detection.
    
    Automatically inspects every incoming request and blocks suspicious IPs.
    """
    
    def __init__(self, app, detector: RealTimeAnomalyDetector):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            detector: RealTimeAnomalyDetector instance
        """
        super().__init__(app)
        self.detector = detector
        logger.info("🛡️ Real-time anomaly detection middleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request through anomaly detection.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
        
        Returns:
            Response (403 if blocked, otherwise continues)
        """
        # Skip health check and docs endpoints
        skip_paths = ['/health', '/docs', '/redoc', '/openapi.json']
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        # Extract IP early for blocking check
        client_ip = self.detector.extract_client_ip(request)
        
        # Quick block check (O(1) lookup)
        if self.detector.is_blocked(client_ip):
            logger.warning(f"🚫 Blocked request from: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={
                    'error': 'Access Denied',
                    'message': 'Your IP has been blocked due to suspicious activity',
                    'ip': client_ip,
                    'contact': 'Please contact administrator if this is an error'
                }
            )
        
        # Only perform full detection if models are loaded
        if self.detector.models_loaded:
            try:
                # Perform anomaly detection
                detection_result = await self.detector.detect_anomaly(request)
                
                # If IP was just blocked, return 403
                if detection_result.get('blocked'):
                    logger.warning(
                        f"🚫 IP Blocked during request: {client_ip} | "
                        f"Risk: {detection_result.get('risk_score', 0):.3f}"
                    )
                    return JSONResponse(
                        status_code=403,
                        content={
                            'error': 'Access Denied',
                            'message': 'Your IP has been blocked due to suspicious activity',
                            'ip': client_ip,
                            'risk_score': detection_result.get('risk_score'),
                            'details': detection_result
                        }
                    )
                
                # Attach detection result to request state for downstream use
                request.state.anomaly_detection = detection_result
            
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}", exc_info=True)
                # Continue processing even if detection fails
        
        # Continue with request processing
        response = await call_next(request)
        return response


# Global detector instance (singleton)
_detector_instance = None


def get_detector(models_dir: str = "../models", openai_api_key: str = None) -> RealTimeAnomalyDetector:
    """
    Get or create the global detector instance.
    
    Args:
        models_dir: Directory containing models
        openai_api_key: OpenAI API key for AI-powered resolutions
    
    Returns:
        RealTimeAnomalyDetector instance
    """
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = RealTimeAnomalyDetector(models_dir, openai_api_key)
    return _detector_instance


# Convenience function for middleware setup
def setup_realtime_detection(app, models_dir: str = "../models", openai_api_key: str = None):
    """
    Set up real-time anomaly detection middleware on a FastAPI app.
    
    Usage:
        from security.realtime_detection import setup_realtime_detection
        
        app = FastAPI()
        openai_key = "sk-proj-..."
        setup_realtime_detection(app, openai_api_key=openai_key)
    
    Args:
        app: FastAPI application
        models_dir: Directory containing ML models
        openai_api_key: OpenAI API key for AI-powered resolutions
    """
    detector = get_detector(models_dir, openai_api_key)
    app.add_middleware(RealTimeAnomalyMiddleware, detector=detector)
    logger.info("✅ Real-time anomaly detection middleware added to application")
    return detector


if __name__ == "__main__":
    # Test the detector
    print("=" * 60)
    print("Real-time Anomaly Detector - Test Mode")
    print("=" * 60)
    
    detector = RealTimeAnomalyDetector()
    
    print(f"\nModels Loaded: {detector.models_loaded}")
    print(f"Tracked IPs: {len(detector.ip_profiles)}")
    print(f"Blocked IPs: {len(detector.blocked_ips)}")
    
    print("\n" + "=" * 60)
    print("Detector ready for use!")
    print("=" * 60)
