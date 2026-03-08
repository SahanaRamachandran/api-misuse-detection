"""
AI-Powered Resolution Engine
Uses OpenAI GPT-4 to generate comprehensive, technical mitigation strategies
for detected anomalies with extreme detail and accuracy.
"""
import openai
import os
import logging
from typing import Dict, Any, List
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIResolutionEngine:
    """
    Generates extremely detailed, technically accurate mitigation strategies
    using OpenAI GPT-4 for each anomaly type.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize AI Resolution Engine with OpenAI API key.
        
        Args:
            api_key: OpenAI API key (if not provided, uses environment variable)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
            logger.info("✅ AI Resolution Engine initialized with OpenAI API")
        else:
            logger.warning("⚠️ OpenAI API key not provided - AI resolution disabled")
    
    def generate_resolution(
        self,
        anomaly_type: str,
        severity: str,
        endpoint: str,
        ip_address: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive, technical resolution strategy using AI.
        
        Provides:
        1. Immediate Containment Steps
        2. Network-Level Mitigation
        3. Application-Level Mitigation
        4. Logging & Forensic Analysis Queries
        5. Detection Improvement Strategy
        6. Risk Explanation (technical reasoning)
        7. IP Blocking Recommendation (permanent vs rate-limited)
        8. Firewall / Nginx / UFW Rules
        9. API-Level Hardening Suggestions
        
        Args:
            anomaly_type: Type of anomaly (e.g., 'latency_spike', 'sql_injection')
            severity: Severity level ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
            endpoint: Affected API endpoint
            ip_address: Source IP address
            context: Additional context (e.g., request details, patterns)
        
        Returns:
            Dictionary with comprehensive resolution strategies
        """
        if not self.api_key:
            return self._generate_fallback_resolution(anomaly_type, severity)
        
        try:
            # Build detailed prompt for AI
            prompt = self._build_resolution_prompt(
                anomaly_type, severity, endpoint, ip_address, context
            )
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent, technical responses
                max_tokens=3000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            # Parse AI response
            ai_content = response.choices[0].message.content
            
            # Structure the response
            resolution = self._parse_ai_response(ai_content, anomaly_type, severity)
            
            logger.info(f"✅ AI Resolution generated for {anomaly_type} ({severity})")
            
            return resolution
        
        except Exception as e:
            logger.error(f"❌ Error generating AI resolution: {e}")
            return self._generate_fallback_resolution(anomaly_type, severity)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI assistant."""
        return """You are a senior security engineer and DevOps expert specializing in API security, 
network defense, and incident response. You provide extremely detailed, technically accurate, 
production-ready mitigation strategies for API anomalies and security threats.

Your responses must be:
- Technically precise with specific commands, configurations, and code
- Actionable with step-by-step instructions
- Production-ready with real-world examples
- Security-focused with defense-in-depth approach
- Comprehensive covering all aspects of mitigation

Always provide specific examples of:
- Exact firewall rules (iptables, UFW, Nginx)
- Specific log queries (grep, awk, SQL)
- Concrete configuration changes
- Real code snippets for fixes
- Precise thresholds and limits"""

    def _build_resolution_prompt(
        self,
        anomaly_type: str,
        severity: str,
        endpoint: str,
        ip_address: str,
        context: Dict[str, Any]
    ) -> str:
        """Build detailed prompt for AI."""
        
        context_str = json.dumps(context, indent=2) if context else "No additional context"
        
        prompt = f"""
API Anomaly Detection Alert - Mitigation Required

ANOMALY DETAILS:
- Type: {anomaly_type}
- Severity: {severity}
- Endpoint: {endpoint}
- Source IP: {ip_address}
- Additional Context: {context_str}

REQUIRED RESPONSE FORMAT:

Provide an extremely detailed, technically accurate mitigation strategy with the following 9 sections:

1. IMMEDIATE CONTAINMENT STEPS
   - What to do RIGHT NOW to stop the threat
   - Exact commands to execute
   - Time-critical actions

2. NETWORK-LEVEL MITIGATION
   - Firewall rules (iptables, UFW specific commands)
   - Load balancer configuration
   - DDoS protection measures
   - Network segmentation recommendations

3. APPLICATION-LEVEL MITIGATION
   - Code fixes (with exact code snippets)
   - Configuration changes (specific values)
   - Input validation improvements
   - Rate limiting implementation

4. LOGGING & FORENSIC ANALYSIS
   - Exact log queries to run (grep, awk, SQL)
   - What to look for in logs
   - Log retention recommendations
   - SIEM integration suggestions

5. DETECTION IMPROVEMENT STRATEGY
   - How to detect this faster next time
   - New monitoring rules to add
   - Alert threshold tuning
   - ML model improvements

6. TECHNICAL RISK EXPLANATION
   - Why this is dangerous (technical details)
   - Attack vectors explained
   - Potential impact analysis
   - Business risk assessment

7. IP BLOCKING RECOMMENDATION
   - Should this IP be permanently blocked?
   - Or rate-limited? (with specific limits)
   - Whitelist considerations
   - Geo-blocking recommendations

8. INFRASTRUCTURE HARDENING RULES
   - NGINX configuration (exact nginx.conf snippets)
   - UFW firewall rules (exact commands)
   - iptables rules (exact syntax)
   - CloudFlare / WAF rules
   - Fail2ban configuration

9. API-LEVEL HARDENING
   - Input sanitization code
   - Request validation schemas
   - Authentication improvements
   - Authorization checks
   - API versioning recommendations

Be extremely specific. Provide EXACT commands, configurations, and code that can be copy-pasted into production.
Use real-world production-grade examples.
"""
        return prompt
    
    def _parse_ai_response(self, ai_content: str, anomaly_type: str, severity: str) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        
        # Try to extract sections from AI response
        sections = {
            'immediate_containment': self._extract_section(ai_content, '1. IMMEDIATE CONTAINMENT'),
            'network_mitigation': self._extract_section(ai_content, '2. NETWORK-LEVEL MITIGATION'),
            'application_mitigation': self._extract_section(ai_content, '3. APPLICATION-LEVEL MITIGATION'),
            'forensic_analysis': self._extract_section(ai_content, '4. LOGGING & FORENSIC ANALYSIS'),
            'detection_improvement': self._extract_section(ai_content, '5. DETECTION IMPROVEMENT'),
            'risk_explanation': self._extract_section(ai_content, '6. TECHNICAL RISK EXPLANATION'),
            'ip_blocking_recommendation': self._extract_section(ai_content, '7. IP BLOCKING RECOMMENDATION'),
            'infrastructure_rules': self._extract_section(ai_content, '8. INFRASTRUCTURE HARDENING'),
            'api_hardening': self._extract_section(ai_content, '9. API-LEVEL HARDENING')
        }
        
        return {
            'anomaly_type': anomaly_type,
            'severity': severity,
            'generated_by': 'OpenAI GPT-4',
            'timestamp': datetime.now().isoformat(),
            'resolution_strategy': sections,
            'full_response': ai_content
        }
    
    def _extract_section(self, content: str, section_marker: str) -> str:
        """Extract a specific section from AI response."""
        try:
            # Find section start
            start_idx = content.find(section_marker)
            if start_idx == -1:
                return "Section not found in AI response"
            
            # Find next section (numbered section)
            next_sections = [
                '\n2. ', '\n3. ', '\n4. ', '\n5. ', '\n6. ', '\n7. ', '\n8. ', '\n9. '
            ]
            
            end_idx = len(content)
            for next_marker in next_sections:
                idx = content.find(next_marker, start_idx + len(section_marker))
                if idx != -1 and idx < end_idx:
                    end_idx = idx
            
            section_content = content[start_idx:end_idx].strip()
            return section_content
        
        except Exception as e:
            logger.error(f"Error extracting section {section_marker}: {e}")
            return "Error extracting section"
    
    def _generate_fallback_resolution(self, anomaly_type: str, severity: str) -> Dict[str, Any]:
        """Generate basic fallback resolution when AI is unavailable."""
        
        fallback_resolutions = {
            'latency_spike': {
                'immediate_containment': """
**IMMEDIATE CONTAINMENT STEPS:**
1. Enable auto-scaling: `aws autoscaling set-desired-capacity --auto-scaling-group-name api-group --desired-capacity 5`
2. Activate CDN caching for static assets
3. Enable connection pooling in application config
""",
                'network_mitigation': """
**NETWORK-LEVEL MITIGATION:**
```bash
# Enable rate limiting at load balancer
sudo ufw limit 80/tcp
sudo ufw limit 443/tcp
```
""",
                'application_mitigation': """
**APPLICATION-LEVEL MITIGATION:**
- Add caching layer (Redis)
- Optimize database queries
- Enable gzip compression
""",
                'ip_blocking_recommendation': "Rate-limit to 100 req/min - likely legitimate traffic spike",
                'risk_explanation': "Latency spikes can lead to timeouts, poor user experience, and potential service degradation if left unaddressed."
            }
        }
        
        default_resolution = fallback_resolutions.get(anomaly_type, {
            'immediate_containment': f"Investigate {anomaly_type} immediately",
            'network_mitigation': "Apply standard network security controls",
            'application_mitigation': "Review application logs and metrics",
            'ip_blocking_recommendation': "Monitor IP for suspicious patterns",
            'risk_explanation': f"{severity} severity {anomaly_type} detected"
        })
        
        return {
            'anomaly_type': anomaly_type,
            'severity': severity,
            'generated_by': 'Fallback System',
            'timestamp': datetime.now().isoformat(),
            'resolution_strategy': default_resolution,
            'note': 'AI resolution unavailable - using fallback'
        }


# Global AI resolution engine instance
_ai_resolution_engine = None


def get_ai_resolution_engine(api_key: str = None) -> AIResolutionEngine:
    """Get or create AI resolution engine instance."""
    global _ai_resolution_engine
    if _ai_resolution_engine is None:
        _ai_resolution_engine = AIResolutionEngine(api_key)
    return _ai_resolution_engine


if __name__ == "__main__":
    # Test the engine
    print("=" * 60)
    print("AI Resolution Engine - Test Mode")
    print("=" * 60)
    
    # Test with a sample anomaly
    engine = AIResolutionEngine()
    
    if engine.api_key:
        print("\n✅ Testing AI resolution generation...")
        
        resolution = engine.generate_resolution(
            anomaly_type='sql_injection',
            severity='CRITICAL',
            endpoint='/api/search',
            ip_address='192.168.1.100',
            context={
                'payload': "' OR '1'='1",
                'user_agent': 'sqlmap/1.0',
                'request_count': 50
            }
        )
        
        print("\n" + "=" * 60)
        print("RESOLUTION GENERATED:")
        print("=" * 60)
        print(json.dumps(resolution, indent=2))
    else:
        print("\n⚠️ No API key - using fallback resolution")
        resolution = engine._generate_fallback_resolution('sql_injection', 'CRITICAL')
        print(json.dumps(resolution, indent=2))
