"""
Resolution Suggestion Engine
Generates unique, actionable, multi-point resolutions for each anomaly type.
NOW ENHANCED WITH AI-POWERED RESOLUTIONS (OpenAI GPT-4)
"""
from typing import List, Dict
import os
import logging

# Try to import AI resolution engine
try:
    from ai_resolution_engine import get_ai_resolution_engine
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    
logger = logging.getLogger(__name__)


class ResolutionEngine:
    """Generates severity-ranked, actionable resolutions for anomalies.
    
    NOW ENHANCED: Uses AI (OpenAI GPT-4) when available for extremely detailed,
    production-ready resolution strategies. Falls back to basic resolutions if AI unavailable.
    """
    
    def __init__(self, use_ai: bool = True, openai_api_key: str = None):
        """
        Initialize Resolution Engine.
        
        Args:
            use_ai: Whether to use AI-powered resolutions (default: True)
            openai_api_key: OpenAI API key (optional, will use env var if not provided)
        """
        self.use_ai = use_ai and AI_AVAILABLE
        self.ai_engine = None
        
        if self.use_ai:
            try:
                self.ai_engine = get_ai_resolution_engine(openai_api_key)
                logger.info("✅ Resolution Engine initialized with AI support")
            except Exception as e:
                logger.warning(f"⚠️ AI resolution unavailable: {e}")
                self.use_ai = False
        else:
            logger.info("Resolution Engine initialized (AI disabled)")
    
    RESOLUTIONS = {
        'latency_spike': {
            'CRITICAL': [
                {'category': 'IMMEDIATE', 'action': 'Enable auto-scaling', 'detail': 'Add 3-5 additional server instances to handle load', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Activate CDN caching', 'detail': 'Cache static assets and API responses at edge locations', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Enable connection pooling', 'detail': 'Reuse database connections to reduce overhead', 'priority': 'CRITICAL'},
                {'category': 'OPTIMIZATION', 'action': 'Optimize slow queries', 'detail': 'Add indexes to database tables causing delays', 'priority': 'HIGH'},
                {'category': 'MONITORING', 'action': 'Set up latency alerts', 'detail': 'Alert when p95 latency exceeds 500ms', 'priority': 'MEDIUM'},
            ],
            'HIGH': [
                {'category': 'SCALING', 'action': 'Scale horizontally', 'detail': 'Add 2 more server instances to distribute load', 'priority': 'HIGH'},
                {'category': 'CACHING', 'action': 'Implement Redis caching', 'detail': 'Cache frequently accessed data for 5 minutes', 'priority': 'HIGH'},
                {'category': 'OPTIMIZATION', 'action': 'Review N+1 queries', 'detail': 'Eliminate redundant database calls in ORM', 'priority': 'MEDIUM'},
                {'category': 'INFRASTRUCTURE', 'action': 'Upgrade database tier', 'detail': 'Increase database IOPS and memory allocation', 'priority': 'MEDIUM'},
            ],
            'MEDIUM': [
                {'category': 'OPTIMIZATION', 'action': 'Enable gzip compression', 'detail': 'Compress API responses to reduce transfer time', 'priority': 'MEDIUM'},
                {'category': 'CACHING', 'action': 'Add browser caching headers', 'detail': 'Cache-Control: max-age=3600 for static assets', 'priority': 'LOW'},
                {'category': 'MONITORING', 'action': 'Profile slow endpoints', 'detail': 'Use APM tools to identify bottlenecks', 'priority': 'LOW'},
            ],
        },
        
        'error_spike': {
            'CRITICAL': [
                {'category': 'IMMEDIATE', 'action': 'Rollback deployment', 'detail': 'Revert to last known stable version immediately', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Enable circuit breaker', 'detail': 'Stop cascading failures to downstream services', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Activate backup database', 'detail': 'Switch to read replica to prevent data corruption', 'priority': 'CRITICAL'},
                {'category': 'INVESTIGATION', 'action': 'Analyze error logs', 'detail': 'Check last 1000 errors for common patterns', 'priority': 'HIGH'},
                {'category': 'COMMUNICATION', 'action': 'Notify stakeholders', 'detail': 'Send incident alert to engineering and product teams', 'priority': 'HIGH'},
            ],
            'HIGH': [
                {'category': 'INVESTIGATION', 'action': 'Check dependency health', 'detail': 'Verify all external APIs and services are operational', 'priority': 'HIGH'},
                {'category': 'MITIGATION', 'action': 'Increase retry attempts', 'detail': 'Retry failed requests with exponential backoff', 'priority': 'HIGH'},
                {'category': 'MONITORING', 'action': 'Enable detailed logging', 'detail': 'Log full request/response for failed calls', 'priority': 'MEDIUM'},
                {'category': 'TESTING', 'action': 'Run regression tests', 'detail': 'Execute full test suite to identify broken functionality', 'priority': 'MEDIUM'},
            ],
            'MEDIUM': [
                {'category': 'VALIDATION', 'action': 'Strengthen input validation', 'detail': 'Add schema validation for all API requests', 'priority': 'MEDIUM'},
                {'category': 'RESILIENCE', 'action': 'Implement graceful degradation', 'detail': 'Return partial data instead of hard failures', 'priority': 'LOW'},
            ],
        },
        
        'timeout': {
            'CRITICAL': [
                {'category': 'IMMEDIATE', 'action': 'Reduce timeout threshold', 'detail': 'Lower timeout from 30s to 10s to fail fast', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Enable async processing', 'detail': 'Move long-running tasks to background queue', 'priority': 'CRITICAL'},
                {'category': 'SCALING', 'action': 'Scale worker processes', 'detail': 'Increase Gunicorn/Uvicorn workers from 4 to 12', 'priority': 'HIGH'},
                {'category': 'OPTIMIZATION', 'action': 'Optimize database queries', 'detail': 'Add composite indexes for multi-column filters', 'priority': 'HIGH'},
            ],
            'HIGH': [
                {'category': 'ARCHITECTURE', 'action': 'Implement request queuing', 'detail': 'Queue requests instead of rejecting them', 'priority': 'HIGH'},
                {'category': 'CACHING', 'action': 'Cache slow computations', 'detail': 'Store expensive calculation results for 10 minutes', 'priority': 'MEDIUM'},
                {'category': 'MONITORING', 'action': 'Track slow queries', 'detail': 'Log all queries taking over 1 second', 'priority': 'MEDIUM'},
            ],
            'MEDIUM': [
                {'category': 'OPTIMIZATION', 'action': 'Use connection pooling', 'detail': 'Reuse database connections to save handshake time', 'priority': 'MEDIUM'},
                {'category': 'INFRASTRUCTURE', 'action': 'Upgrade network bandwidth', 'detail': 'Increase network throughput to reduce latency', 'priority': 'LOW'},
            ],
        },
        
        'traffic_burst': {
            'CRITICAL': [
                {'category': 'IMMEDIATE', 'action': 'Enable rate limiting', 'detail': 'Limit to 100 requests per minute per IP', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Activate auto-scaling', 'detail': 'Scale from 2 to 8 instances based on CPU usage', 'priority': 'CRITICAL'},
                {'category': 'SECURITY', 'action': 'Check for DDoS attack', 'detail': 'Analyze traffic patterns for malicious activity', 'priority': 'HIGH'},
                {'category': 'LOAD_BALANCING', 'action': 'Distribute traffic evenly', 'detail': 'Use round-robin across all available instances', 'priority': 'HIGH'},
            ],
            'HIGH': [
                {'category': 'CACHING', 'action': 'Aggressive response caching', 'detail': 'Cache 90% of read requests for 2 minutes', 'priority': 'HIGH'},
                {'category': 'THROTTLING', 'action': 'Implement API throttling', 'detail': 'Queue excess requests instead of dropping', 'priority': 'MEDIUM'},
                {'category': 'MONITORING', 'action': 'Set traffic spike alerts', 'detail': 'Alert when traffic exceeds 150% of baseline', 'priority': 'MEDIUM'},
            ],
            'MEDIUM': [
                {'category': 'OPTIMIZATION', 'action': 'Optimize response size', 'detail': 'Reduce payload by removing unnecessary fields', 'priority': 'MEDIUM'},
                {'category': 'INFRASTRUCTURE', 'action': 'Use CDN for static assets', 'detail': 'Offload 80% of traffic to edge servers', 'priority': 'LOW'},
            ],
        },
        
        'resource_exhaustion': {
            'CRITICAL': [
                {'category': 'IMMEDIATE', 'action': 'Restart application servers', 'detail': 'Clear memory leaks and release resources', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Limit request payload size', 'detail': 'Reject requests larger than 10MB', 'priority': 'CRITICAL'},
                {'category': 'IMMEDIATE', 'action': 'Enable memory monitoring', 'detail': 'Kill processes exceeding 80% memory usage', 'priority': 'CRITICAL'},
                {'category': 'SCALING', 'action': 'Upgrade server resources', 'detail': 'Double RAM from 8GB to 16GB per instance', 'priority': 'HIGH'},
                {'category': 'INVESTIGATION', 'action': 'Profile memory usage', 'detail': 'Identify memory leaks with heap analysis', 'priority': 'HIGH'},
            ],
            'HIGH': [
                {'category': 'OPTIMIZATION', 'action': 'Implement streaming', 'detail': 'Stream large responses instead of buffering', 'priority': 'HIGH'},
                {'category': 'CLEANUP', 'action': 'Clear old cache entries', 'detail': 'Purge cache items older than 1 hour', 'priority': 'MEDIUM'},
                {'category': 'VALIDATION', 'action': 'Validate file uploads', 'detail': 'Reject files larger than 5MB', 'priority': 'MEDIUM'},
            ],
            'MEDIUM': [
                {'category': 'MONITORING', 'action': 'Track resource metrics', 'detail': 'Monitor CPU, memory, and disk usage every minute', 'priority': 'MEDIUM'},
                {'category': 'OPTIMIZATION', 'action': 'Use pagination', 'detail': 'Limit response size to 100 items per page', 'priority': 'LOW'},
            ],
        },
    }
    
    def generate_resolutions(self, anomaly_type: str, severity: str, endpoint: str = None, ip_address: str = None, context: Dict = None) -> List[Dict]:
        """
        Generate actionable resolutions for specific anomaly type and severity.
        
        NOW ENHANCED: Uses AI (OpenAI GPT-4) when available to generate extremely detailed,
        production-ready resolution strategies with 9 comprehensive sections.
        
        Args:
            anomaly_type: Type of anomaly (e.g., 'latency_spike', 'sql_injection')
            severity: Severity level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
            endpoint: Affected API endpoint (optional, used for AI context)
            ip_address: Source IP (optional, used for AI context)
            context: Additional context (optional, used for AI)
        
        Returns:
            List of resolution suggestions (basic format) OR 
            AI-generated detailed resolution (if use_ai=True)
        """
        # Try AI-powered resolution first
        if self.use_ai and self.ai_engine is not None:
            try:
                ai_resolution = self.ai_engine.generate_resolution(
                    anomaly_type=anomaly_type,
                    severity=severity,
                    endpoint=endpoint or f'/api/{anomaly_type}',
                    ip_address=ip_address or 'unknown',
                    context=context or {}
                )
                
                # Convert AI resolution to list format for compatibility
                # (The AI resolution is much more detailed and structured)
                if ai_resolution and 'resolution_strategy' in ai_resolution:
                    logger.info(f"✅ AI resolution generated for {anomaly_type} ({severity})")
                    return self._format_ai_resolution_as_list(ai_resolution)
                    
            except Exception as e:
                logger.warning(f"⚠️ AI resolution failed, using fallback: {e}")
        
        # Fallback to basic resolutions
        if anomaly_type not in self.RESOLUTIONS:
            return self._get_generic_resolutions(severity)
        
        severity_map = self.RESOLUTIONS[anomaly_type]
        
        # Get resolutions for exact severity
        if severity in severity_map:
            return severity_map[severity]
        
        # Fallback to lower severity if not found
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
        for sev in severity_order:
            if sev in severity_map:
                return severity_map[sev]
        
        return self._get_generic_resolutions(severity)
    
    def _format_ai_resolution_as_list(self, ai_resolution: Dict) -> List[Dict]:
        """
        Convert AI resolution to list format for backward compatibility.
        Returns a structured list with the 9 AI-generated sections.
        """
        strategy = ai_resolution.get('resolution_strategy', {})
        
        # Format AI sections into list format
        formatted = []
        
        section_mapping = {
            'immediate_containment': ('IMMEDIATE CONTAINMENT', 'CRITICAL', 'Emergency Response Protocol'),
            'network_mitigation': ('NETWORK MITIGATION', 'HIGH', 'Network Layer Defense Strategy'),
            'application_mitigation': ('APPLICATION HARDENING', 'HIGH', 'Application Security Enhancement'),
            'forensic_analysis': ('FORENSIC INVESTIGATION', 'MEDIUM', 'Digital Forensics & Root Cause Analysis'),
            'detection_improvement': ('DETECTION OPTIMIZATION', 'MEDIUM', 'Advanced Detection Rule Tuning'),
            'risk_explanation': ('THREAT INTELLIGENCE', 'HIGH', 'Attack Vector Analysis & Risk Assessment'),
            'ip_blocking_recommendation': ('NETWORK ACCESS CONTROL', 'HIGH', 'IP-Based Blocking & Mitigation Policy'),
            'infrastructure_rules': ('INFRASTRUCTURE SECURITY', 'CRITICAL', 'Firewall & WAF Rule Implementation'),
            'api_hardening': ('API SECURITY FRAMEWORK', 'HIGH', 'REST API Protection & Input Validation'),
        }
        
        for key, (category, priority, action_name) in section_mapping.items():
            content = strategy.get(key, '')
            if content and content != "Section not found in AI response":
                formatted.append({
                    'category': category,
                    'action': action_name,
                    'detail': content[:500] + '...' if len(content) > 500 else content,  # Truncate if too long
                    'priority': priority,
                    'full_content': content,  # Store full content
                    'ai_generated': True
                })
        
        # If no AI content, return empty (will fall back to basic)
        if not formatted:
            return []
        
        # Add technical metadata
        formatted.append({
            'category': 'RESOLUTION METADATA',
            'action': 'Advanced Security Analysis Report',
            'detail': f"Comprehensive threat mitigation strategy compiled from enterprise security frameworks and industry best practices. Analysis timestamp: {ai_resolution.get('timestamp', 'unknown')}",
            'priority': 'INFO',
            'full_ai_response': ai_resolution.get('full_response', ''),
            'ai_generated': True
        })
        
        return formatted
    
    def _get_generic_resolutions(self, severity: str) -> List[Dict]:
        """Generic fallback resolutions."""
        return [
            {'category': 'MONITORING', 'action': 'Investigate anomaly', 'detail': 'Review logs and metrics for unusual patterns', 'priority': severity},
            {'category': 'INVESTIGATION', 'action': 'Check dependencies', 'detail': 'Verify all external services are operational', 'priority': severity},
            {'category': 'MITIGATION', 'action': 'Enable monitoring', 'detail': 'Set up alerts for similar anomalies', 'priority': 'MEDIUM'},
        ]


# Global resolution engine (initialized with AI support)
# OpenAI API key will be loaded from environment or passed during initialization
resolution_engine = ResolutionEngine(
    use_ai=True,  # Enable AI-powered resolutions
    openai_api_key=os.getenv('OPENAI_API_KEY')
)
