"""
FastAPI Integration Example

Demonstrates how to integrate all ML features into a FastAPI application.

Endpoints:
- POST /api/request - Process a request through the ML pipeline
- GET /api/health - System health check
- GET /api/ips/high-risk - Get high-risk IPs
- GET /api/ips/{ip} - Get specific IP summary
- POST /api/drift/check - Check for concept drift
- GET /api/explain/{request_id} - Get SHAP explanation

Usage:
    python fastapi_integration_example.py
    
Then visit: http://localhost:8001/docs
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import time
import numpy as np
import pandas as pd

# Import ML modules
from explainability import SHAPExplainer
from drift_detection import ConceptDriftDetector
from realtime_inference import RealTimeInferenceEngine, RealTimeInferenceMiddleware
from ensemble_scoring import EnsembleThreatScorer
from ip_risk_engine import IPRiskEngine


# === Pydantic Models ===

class RequestData(BaseModel):
    """Incoming request data."""
    ip_address: str
    endpoint: str
    method: str
    payload_size: int
    response_time: float
    status_code: int


class DriftCheckRequest(BaseModel):
    """Drift check request."""
    current_data_path: str


class ThreatResponse(BaseModel):
    """Threat analysis response."""
    ip_address: str
    endpoint: str
    is_anomaly: bool
    threat_score: float
    risk_level: str
    ip_risk_score: float
    ip_flagged: bool
    processing_time_ms: float
    explanation: Optional[Dict[str, Any]] = None


# === Initialize FastAPI App ===

app = FastAPI(
    title="ML-Enhanced API Threat Detection",
    description="Advanced threat detection with SHAP explainability, drift detection, and IP risk tracking",
    version="1.0.0"
)


# === Global State ===

class MLComponents:
    """Container for ML components."""
    
    def __init__(self):
        self.explainer: Optional[SHAPExplainer] = None
        self.drift_detector: Optional[ConceptDriftDetector] = None
        self.inference_engine: Optional[RealTimeInferenceEngine] = None
        self.ensemble_scorer: Optional[EnsembleThreatScorer] = None
        self.ip_risk_engine: Optional[IPRiskEngine] = None
        self.initialized = False


ml_components = MLComponents()


# === Startup/Shutdown ===

@app.on_event("startup")
async def startup_event():
    """Initialize ML components on startup."""
    print("Initializing ML components...")
    
    try:
        # 1. SHAP Explainability
        ml_components.explainer = SHAPExplainer(
            models_dir='models',
            output_dir='evaluation_results/explainability'
        )
        ml_components.explainer.load_model('robust_random_forest')
        ml_components.explainer.create_explainer('robust_random_forest')
        
        # 2. Drift Detection
        ml_components.drift_detector = ConceptDriftDetector(
            reference_data_path='evaluation_results/training/kfold_test_features.csv'
        )
        
        # 3. Real-Time Inference
        ml_components.inference_engine = RealTimeInferenceEngine(
            model_path='models/robust_random_forest.pkl'
        )
        
        # 4. Ensemble Scoring
        ml_components.ensemble_scorer = EnsembleThreatScorer(
            models_dir='models',
            rf_model_name='robust_random_forest',
            iso_model_name='robust_isolation_forest'
        )
        
        # 5. IP Risk Tracking
        ml_components.ip_risk_engine = IPRiskEngine(
            high_risk_threshold=70
        )
        
        ml_components.initialized = True
        
        print("[OK] ML components initialized successfully")
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize ML components: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Save state on shutdown."""
    if ml_components.ip_risk_engine:
        ml_components.ip_risk_engine.save_tracker()
        print("[OK] IP tracker saved")


# === Helper Functions ===

def check_initialized():
    """Check if ML components are initialized."""
    if not ml_components.initialized:
        raise HTTPException(
            status_code=503,
            detail="ML components not initialized"
        )


# === API Endpoints ===

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ML-Enhanced API Threat Detection",
        "version": "1.0.0",
        "components": {
            "explainability": ml_components.explainer is not None,
            "drift_detection": ml_components.drift_detector is not None,
            "inference": ml_components.inference_engine is not None,
            "ensemble": ml_components.ensemble_scorer is not None,
            "ip_risk": ml_components.ip_risk_engine is not None
        }
    }


@app.post("/api/request", response_model=ThreatResponse)
async def analyze_request(request_data: RequestData):
    """
    Analyze a request through the complete ML pipeline.
    
    Returns threat analysis with SHAP explanation if anomaly detected.
    """
    check_initialized()
    
    start_time = time.time()
    
    try:
        # Stage 1: Real-time inference
        request_metadata = {
            'endpoint': request_data.endpoint,
            'method': request_data.method,
            'payload_size': request_data.payload_size,
            'response_time': request_data.response_time,
            'status_code': request_data.status_code,
            'timestamp': time.time()
        }
        prediction = ml_components.inference_engine.predict_anomaly(
            ip_address=request_data.ip_address,
            request_metadata=request_metadata
        )
        
        # Stage 2: Ensemble threat scoring
        # Convert features dict to properly ordered array
        feature_names = [
            'request_rate', 'unique_endpoint_count', 'method_ratio',
            'avg_payload_size', 'error_rate', 'repeated_parameter_ratio',
            'user_agent_entropy', 'avg_response_time', 'max_response_time'
        ]
        features_values = [prediction['features'][fname] for fname in feature_names]
        features = np.array([features_values])
        ensemble_scores = ml_components.ensemble_scorer.compute_ensemble_score(features)
        threat_score = float(ensemble_scores[0])
        risk_level = ml_components.ensemble_scorer.classify_risk_level(threat_score)
        
        # Stage 3: SHAP explanation (if anomaly)
        explanation = None
        if prediction['is_anomaly']:
            # Convert features array to DataFrame
            features_df = pd.DataFrame(features, columns=[
                'request_rate', 'unique_endpoint_count', 'method_ratio',
                'avg_payload_size', 'error_rate', 'repeated_parameter_ratio',
                'user_agent_entropy', 'avg_response_time', 'max_response_time'
            ])
            explanation = ml_components.explainer.explain_sample(
                model_name='robust_random_forest',
                X_sample=features_df,
                sample_idx=0,
                top_k=5
            )
        
        # Stage 4: Update IP risk
        ip_update = ml_components.ip_risk_engine.update_ip_risk(
            ip_address=request_data.ip_address,
            threat_score=threat_score,
            is_anomaly=prediction['is_anomaly']
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        return ThreatResponse(
            ip_address=request_data.ip_address,
            endpoint=request_data.endpoint,
            is_anomaly=prediction['is_anomaly'],
            threat_score=float(threat_score),
            risk_level=risk_level,
            ip_risk_score=float(ip_update['risk_score']),
            ip_flagged=ip_update['flagged'],
            processing_time_ms=processing_time,
            explanation=explanation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Get system health metrics."""
    check_initialized()
    
    try:
        inference_stats = ml_components.inference_engine.get_performance_stats()
        ip_stats = ml_components.ip_risk_engine.get_statistics()
        
        health = {
            'status': 'healthy',
            'inference_performance': inference_stats,
            'ip_tracking': ip_stats,
            'high_risk_ips': len(ml_components.ip_risk_engine.get_high_risk_ips())
        }
        
        # Check for degraded performance
        if 'mean_inference_time_ms' in inference_stats:
            if inference_stats['mean_inference_time_ms'] > 20:
                health['status'] = 'degraded'
                health['warning'] = 'High inference latency'
        
        return health
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ips/high-risk")
async def get_high_risk_ips():
    """Get list of high-risk IPs."""
    check_initialized()
    
    try:
        high_risk_ips = ml_components.ip_risk_engine.get_high_risk_ips()
        return {
            'count': len(high_risk_ips),
            'ips': high_risk_ips
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ips/{ip_address}")
async def get_ip_summary(ip_address: str):
    """Get summary for a specific IP."""
    check_initialized()
    
    try:
        summary = ml_components.ip_risk_engine.get_ip_summary(ip_address)
        
        if 'error' in summary:
            raise HTTPException(status_code=404, detail=f"IP not found: {ip_address}")
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/drift/check")
async def check_drift(request: DriftCheckRequest):
    """Check for concept drift."""
    check_initialized()
    
    try:
        drift_results = ml_components.drift_detector.detect_drift(
            request.current_data_path
        )
        
        return drift_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_statistics():
    """Get overall system statistics."""
    check_initialized()
    
    try:
        ip_stats = ml_components.ip_risk_engine.get_statistics()
        inference_stats = ml_components.inference_engine.get_performance_stats()
        
        return {
            'ip_tracking': ip_stats,
            'inference_performance': inference_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Middleware Integration Example ===

# Uncomment to add real-time inference middleware to ALL requests
# (This would automatically analyze every incoming request)

# from realtime_inference import RealTimeInferenceMiddleware
# app.add_middleware(RealTimeInferenceMiddleware)


# === Run Server ===

if __name__ == "__main__":
    print("="*80)
    print("Starting ML-Enhanced API Threat Detection Server")
    print("="*80)
    print("\nEndpoints:")
    print("  - POST /api/request - Analyze a request")
    print("  - GET /api/health - System health")
    print("  - GET /api/ips/high-risk - High-risk IPs")
    print("  - GET /api/ips/{ip} - IP summary")
    print("  - POST /api/drift/check - Check drift")
    print("  - GET /api/stats - Statistics")
    print("\nAPI Documentation: http://localhost:8001/docs")
    print("="*80)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
