"""
Async Email Alert System for Anomaly Detection
Sends professional SOC-style alerts to administrators when critical anomalies detected.
"""
import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import asyncio
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Email Configuration (from environment variables)
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'sahanaramachandran2003@gmail.com')

# Alert threshold
ALERT_THRESHOLD = 0.8


async def send_alert_email(anomaly_data: Dict[str, Any]) -> bool:
    """
    Send async email alert for critical anomaly detection.
    
    Email is sent asynchronously and does not block the main request processing.
    Only sends when risk_score >= 0.8 (ALERT_THRESHOLD).
    
    Args:
        anomaly_data: Dictionary containing anomaly details:
            - anomaly_type: Type of attack/anomaly
            - risk_score: Risk score (0.0 to 1.0)
            - probability: Detection probability
            - ip_address: Source IP address
            - endpoint: Affected API endpoint
            - timestamp: Detection timestamp
            - blocked: Whether IP was blocked
            - (optional) severity, confidence, method, etc.
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Extract data with defaults
        anomaly_type = anomaly_data.get('anomaly_type', 'Unknown Anomaly')
        risk_score = float(anomaly_data.get('risk_score', 0.0))
        probability = float(anomaly_data.get('probability', 0.0))
        ip_address = anomaly_data.get('ip_address', 'Unknown IP')
        endpoint = anomaly_data.get('endpoint', 'Unknown Endpoint')
        timestamp = anomaly_data.get('timestamp', datetime.utcnow().isoformat())
        blocked = anomaly_data.get('blocked', False)
        severity = anomaly_data.get('severity', 'HIGH')
        confidence = anomaly_data.get('confidence', probability)
        method = anomaly_data.get('method', 'Unknown')
        
        # Only send alert if risk score meets threshold
        if risk_score < ALERT_THRESHOLD:
            logger.debug(f"Risk score {risk_score:.2f} below threshold {ALERT_THRESHOLD}, skipping email")
            return False
        
        # Check if SMTP is configured
        if not SMTP_USER or not SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured, skipping email alert")
            return False
        
        # Create email message
        message = MIMEMultipart('alternative')
        message['Subject'] = f"🚨 SECURITY ALERT [{severity}] - {anomaly_type.upper()} DETECTED"
        message['From'] = SMTP_USER
        message['To'] = ADMIN_EMAIL
        
        # Create professional SOC-style email body
        html_body = _create_soc_alert_html(
            anomaly_type=anomaly_type,
            risk_score=risk_score,
            probability=probability,
            ip_address=ip_address,
            endpoint=endpoint,
            timestamp=timestamp,
            blocked=blocked,
            severity=severity,
            confidence=confidence,
            method=method
        )
        
        # Plain text fallback
        text_body = _create_soc_alert_text(
            anomaly_type=anomaly_type,
            risk_score=risk_score,
            probability=probability,
            ip_address=ip_address,
            endpoint=endpoint,
            timestamp=timestamp,
            blocked=blocked,
            severity=severity,
            confidence=confidence,
            method=method
        )
        
        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        message.attach(part1)
        message.attach(part2)
        
        # Send email asynchronously
        async with aiosmtplib.SMTP(hostname=SMTP_HOST, port=SMTP_PORT) as smtp:
            await smtp.starttls()
            await smtp.login(SMTP_USER, SMTP_PASSWORD)
            await smtp.send_message(message)
        
        logger.info(f"✅ Alert email sent to {ADMIN_EMAIL} for {anomaly_type} (Risk: {risk_score:.2f})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send alert email: {e}", exc_info=True)
        return False


def _create_soc_alert_html(
    anomaly_type: str,
    risk_score: float,
    probability: float,
    ip_address: str,
    endpoint: str,
    timestamp: str,
    blocked: bool,
    severity: str,
    confidence: float,
    method: str
) -> str:
    """Create professional HTML-formatted SOC alert email."""
    
    # Determine severity color
    severity_colors = {
        'CRITICAL': '#D32F2F',
        'HIGH': '#F57C00',
        'MEDIUM': '#FFA000',
        'LOW': '#FBC02D'
    }
    severity_color = severity_colors.get(severity, '#757575')
    
    # Status badge
    status_badge = f'<span style="background: #D32F2F; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">🚫 IP BLOCKED</span>' if blocked else f'<span style="background: #FFA000; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold;">⚠️ MONITORING</span>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 700px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); overflow: hidden; }}
            .header {{ background: {severity_color}; color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header .subtitle {{ margin-top: 8px; opacity: 0.9; font-size: 14px; }}
            .content {{ padding: 30px; }}
            .alert-box {{ background: #FFF3E0; border-left: 4px solid #FF9800; padding: 16px; margin: 20px 0; border-radius: 4px; }}
            .info-grid {{ display: grid; gap: 16px; margin: 20px 0; }}
            .info-row {{ display: flex; border-bottom: 1px solid #e0e0e0; padding: 12px 0; }}
            .info-label {{ font-weight: 600; color: #424242; width: 180px; }}
            .info-value {{ color: #616161; flex: 1; }}
            .metric {{ display: inline-block; background: #E3F2FD; padding: 8px 16px; border-radius: 4px; margin: 4px; }}
            .metric-label {{ font-size: 12px; color: #1976D2; text-transform: uppercase; }}
            .metric-value {{ font-size: 20px; font-weight: bold; color: #0D47A1; }}
            .footer {{ background: #FAFAFA; padding: 20px 30px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #757575; }}
            .action-required {{ background: #FFEBEE; border: 2px solid #F44336; padding: 16px; border-radius: 4px; margin: 20px 0; }}
            .action-required h3 {{ margin: 0 0 12px 0; color: #D32F2F; }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <h1>🚨 SECURITY OPERATIONS CENTER ALERT</h1>
                <div class="subtitle">Anomaly Detection System - Immediate Action Required</div>
                <div style="margin-top: 16px;">{status_badge}</div>
            </div>
            
            <!-- Content -->
            <div class="content">
                <div class="alert-box">
                    <strong>⚠️ THREAT DETECTED:</strong> {anomaly_type.upper()}<br>
                    <strong>Detection Time:</strong> {timestamp}
                </div>
                
                <!-- Metrics -->
                <div style="text-align: center; margin: 24px 0;">
                    <div class="metric">
                        <div class="metric-label">Risk Score</div>
                        <div class="metric-value" style="color: #D32F2F;">{risk_score:.2%}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value">{confidence:.2%}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Severity</div>
                        <div class="metric-value" style="color: {severity_color};">{severity}</div>
                    </div>
                </div>
                
                <!-- Threat Details -->
                <h3 style="color: #424242; border-bottom: 2px solid #E0E0E0; padding-bottom: 8px;">Threat Intelligence</h3>
                <div class="info-grid">
                    <div class="info-row">
                        <div class="info-label">Attack Type:</div>
                        <div class="info-value"><strong>{anomaly_type}</strong></div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Source IP Address:</div>
                        <div class="info-value"><code style="background: #FFEBEE; padding: 4px 8px; border-radius: 3px; color: #D32F2F;">{ip_address}</code></div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Target Endpoint:</div>
                        <div class="info-value"><code>{endpoint}</code></div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">HTTP Method:</div>
                        <div class="info-value">{method}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Detection Model:</div>
                        <div class="info-value">XGBoost + Autoencoder Ensemble</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Detection Probability:</div>
                        <div class="info-value">{probability:.2%}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">IP Status:</div>
                        <div class="info-value">{'<strong style="color: #D32F2F;">BLOCKED ✓</strong>' if blocked else '<strong style="color: #FF9800;">MONITORING</strong>'}</div>
                    </div>
                </div>
                
                <!-- Action Required -->
                <div class="action-required">
                    <h3>⚡ IMMEDIATE ACTION REQUIRED</h3>
                    <ol style="margin: 8px 0; padding-left: 20px; color: #424242;">
                        <li>Review detailed logs for IP: <strong>{ip_address}</strong></li>
                        <li>Verify if attack is ongoing or isolated incident</li>
                        <li>Check for similar patterns from other IPs</li>
                        <li>{'Confirm IP block is effective' if blocked else 'Consider blocking IP address permanently'}</li>
                        <li>Update firewall rules if necessary</li>
                        <li>Document incident for security audit</li>
                    </ol>
                </div>
                
                <!-- System Info -->
                <div style="margin-top: 24px; padding: 16px; background: #E8F5E9; border-radius: 4px;">
                    <strong>✓ System Response:</strong><br>
                    Real-time detection middleware has {'automatically blocked this IP address from all endpoints' if blocked else 'flagged this IP for monitoring. Manual review recommended.'}<br>
                    <strong>Dashboard:</strong> <a href="http://localhost:3000">http://localhost:3000</a>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <strong>Traffic Monitoring & Anomaly Detection System</strong><br>
                This is an automated security alert. Do not reply to this email.<br>
                For assistance, contact your system administrator.<br>
                <br>
                <em>Alert ID: {timestamp.replace(':', '-')[:19]} | System: Production API Gateway</em>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def _create_soc_alert_text(
    anomaly_type: str,
    risk_score: float,
    probability: float,
    ip_address: str,
    endpoint: str,
    timestamp: str,
    blocked: bool,
    severity: str,
    confidence: float,
    method: str
) -> str:
    """Create plain text SOC alert email."""
    
    status = "BLOCKED" if blocked else "MONITORING"
    
    text = f"""
================================================================================
🚨 SECURITY OPERATIONS CENTER ALERT - {severity}
================================================================================

THREAT DETECTED: {anomaly_type.upper()}
Detection Time: {timestamp}
Status: {status}

--------------------------------------------------------------------------------
THREAT METRICS
--------------------------------------------------------------------------------
Risk Score:          {risk_score:.2%}
Confidence:          {confidence:.2%}
Severity Level:      {severity}
Detection Model:     XGBoost + Autoencoder Ensemble

--------------------------------------------------------------------------------
THREAT DETAILS
--------------------------------------------------------------------------------
Attack Type:         {anomaly_type}
Source IP:           {ip_address}
Target Endpoint:     {endpoint}
HTTP Method:         {method}
Detection Probability: {probability:.2%}
IP Status:           {'BLOCKED ✓' if blocked else 'MONITORING'}

--------------------------------------------------------------------------------
IMMEDIATE ACTIONS REQUIRED
--------------------------------------------------------------------------------
1. Review detailed logs for IP: {ip_address}
2. Verify if attack is ongoing or isolated incident
3. Check for similar patterns from other IPs
4. {'Confirm IP block is effective' if blocked else 'Consider blocking IP address permanently'}
5. Update firewall rules if necessary
6. Document incident for security audit

--------------------------------------------------------------------------------
SYSTEM RESPONSE
--------------------------------------------------------------------------------
Real-time detection middleware has {'automatically blocked this IP address from all endpoints' if blocked else 'flagged this IP for monitoring. Manual review recommended.'}.

Dashboard: http://localhost:3000

================================================================================
Traffic Monitoring & Anomaly Detection System
This is an automated security alert. Do not reply to this email.
Alert ID: {timestamp.replace(':', '-')[:19]}
================================================================================
    """
    return text.strip()


def trigger_alert_email(anomaly_data: Dict[str, Any]) -> None:
    """
    Trigger email alert asynchronously without blocking.
    
    This function creates an async task to send the email,
    ensuring it does not block the main API request processing.
    
    Args:
        anomaly_data: Anomaly detection data dictionary
    """
    try:
        # Create async task to send email without blocking
        asyncio.create_task(send_alert_email(anomaly_data))
        logger.info(f"📧 Email alert task created for {anomaly_data.get('anomaly_type', 'unknown')} (non-blocking)")
    except Exception as e:
        logger.error(f"❌ Failed to create email alert task: {e}")


# For testing the email system
if __name__ == "__main__":
    import asyncio
    
    # Test email configuration
    print("=" * 60)
    print("EMAIL ALERT SYSTEM - TEST MODE")
    print("=" * 60)
    print(f"SMTP Host: {SMTP_HOST}")
    print(f"SMTP Port: {SMTP_PORT}")
    print(f"SMTP User: {SMTP_USER[:10]}..." if SMTP_USER else "SMTP User: Not configured")
    print(f"Admin Email: {ADMIN_EMAIL}")
    print("")
    
    # Test data
    test_anomaly = {
        'anomaly_type': 'SQL Injection',
        'risk_score': 0.92,
        'probability': 0.88,
        'ip_address': '192.168.1.100',
        'endpoint': '/api/login',
        'timestamp': datetime.utcnow().isoformat(),
        'blocked': True,
        'severity': 'CRITICAL',
        'confidence': 0.88,
        'method': 'POST'
    }
    
    print("Sending test email alert...")
    result = asyncio.run(send_alert_email(test_anomaly))
    
    if result:
        print("\n✅ Test email sent successfully!")
    else:
        print("\n❌ Failed to send test email. Check configuration.")
