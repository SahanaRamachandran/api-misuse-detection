# 📧 Email Alert System - Setup Guide

## Overview
The system sends **professional SOC-style email alerts** when critical anomalies are detected (risk score >= 80%).

---

## 🚀 Quick Setup

### Step 1: Install Required Package
```powershell
cd backend
.venv\Scripts\Activate.ps1
pip install aiosmtplib
```

### Step 2: Configure Email Settings

Create a `.env` file in the `backend` folder:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ADMIN_EMAIL=sahanaramachandran2003@gmail.com
```

### Step 3: Get Gmail App Password

1. **Enable 2-Factor Authentication**:
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other (Custom name)"
   - Name it: "Traffic Monitoring System"
   - Click "Generate"
   - Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

3. **Add to .env file**:
   ```env
   SMTP_PASSWORD=your16characterapppassword
   ```
   (Remove all spaces from the app password)

### Step 4: Test Email System
```powershell
cd backend
python email_alerts.py
```

You should see:
```
EMAIL ALERT SYSTEM - TEST MODE
Sending test email alert...
✅ Test email sent successfully!
```

Check **sahanaramachandran2003@gmail.com** for the test email.

---

## 📋 Email Alert Triggers

Emails are sent automatically when:
- ✅ **Risk Score >= 0.8** (80% or higher)
- ✅ **Live Mode Only** (not sent for simulation traffic)
- ✅ **Real-time detection** finds an anomaly
- ✅ **Background detector** finds an anomaly

---

## 📧 What's Included in Alerts

### Email Subject
```
🚨 SECURITY ALERT [HIGH/CRITICAL] - SQL INJECTION DETECTED
```

### Email Content (Professional SOC Format)

1. **Threat Metrics**:
   - Risk Score: 92%
   - Confidence: 88%
   - Severity: CRITICAL/HIGH

2. **Threat Details**:
   - Attack Type (e.g., SQL Injection, XSS, DDoS)
   - Source IP Address
   - Target Endpoint
   - HTTP Method
   - Detection Model Used
   - IP Block Status

3. **Immediate Actions Required**:
   - Review logs for the IP
   - Verify if attack is ongoing
   - Check for similar patterns
   - Confirm IP block effectiveness
   - Update firewall rules
   - Document incident

4. **System Response**:
   - Whether IP was auto-blocked
   - Link to dashboard for details

### Email Format
- **HTML Version**: Beautiful, color-coded, professional SOC alert
- **Plain Text Version**: Fallback for email clients without HTML support

---

## 🔧 Configuration Options

### Change Admin Email
Edit `.env`:
```env
ADMIN_EMAIL=your-email@example.com
```

### Use Different SMTP Provider

#### Outlook/Office 365
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

#### Yahoo Mail
```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

#### Custom SMTP Server
```env
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USER=alerts@yourdomain.com
SMTP_PASSWORD=your-password
```

### Adjust Alert Threshold

Edit `backend/email_alerts.py`:
```python
ALERT_THRESHOLD = 0.8  # Change to 0.9 for CRITICAL only, 0.7 for more alerts
```

---

## 🧪 Testing

### Test 1: Send Test Email
```powershell
cd backend
python email_alerts.py
```

### Test 2: Trigger Real Anomaly
```powershell
# Trigger SQL injection detection (should send email)
curl http://localhost:8000/login `
  -X POST `
  -H "Content-Type: application/json" `
  -H "X-Forwarded-For: 192.168.1.100" `
  -d '{"username": "admin'' OR ''1''=''1", "password": "test"}'
```

Wait for detection (might take a few seconds), then check email.

### Test 3: Start Simulation (No Emails)
```powershell
# Simulation traffic does NOT trigger emails (by design)
curl -X POST http://localhost:8000/api/simulation/start `
  -H "Content-Type: application/json" `
  -d '{"duration_seconds": 30, "requests_per_second": 100}'
```

This should NOT send emails (simulation traffic is excluded).

---

## 📊 Email Sending Behavior

### Non-Blocking (Async)
- Email sending **does NOT block** API requests
- Uses `asyncio.create_task()` for background sending
- API responds immediately, email sends in background

### Error Handling
- If email fails, error is logged but API continues working
- Fallback: System continues detecting even if email is down

### Rate Limiting
- No built-in rate limiting currently
- Each anomaly triggers one email
- Consider adding rate limiting if you get too many emails

---

## 🔍 Troubleshooting

### Problem: "SMTP credentials not configured"

**Solution**: Create `.env` file with SMTP settings:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Problem: "Authentication failed"

**Solutions**:
1. **Gmail**: Use App Password, not regular password
2. **2FA**: Make sure 2-factor auth is enabled
3. **Less Secure Apps**: Gmail no longer supports this - use App Passwords

### Problem: "Connection refused"

**Solutions**:
1. Check SMTP_HOST and SMTP_PORT are correct
2. Try port 465 (SSL) instead of 587 (TLS)
3. Check firewall/antivirus blocking port 587

### Problem: No emails received

**Solutions**:
1. **Check Spam Folder**: Emails might be marked as spam
2. **Check Risk Score**: Only risk_score >= 0.8 triggers emails
3. **Check Mode**: Simulation traffic doesn't send emails
4. **Check Logs**: Look for "📧 Email alert triggered" in backend logs

### Problem: Emails sent but not received

**Solutions**:
1. Verify ADMIN_EMAIL is correct in `.env`
2. Check your spam/junk folder
3. Check email provider's blocked senders list
4. Try sending to different email address

---

## 📁 Files

### Created Files
- **`backend/email_alerts.py`** - Email alert system (370 lines)
- **`backend/.env.example`** - Configuration template

### Modified Files
- **`backend/security/realtime_detection.py`** - Added email triggers
- **`backend/app.py`** - Added email triggers for live anomalies

---

## 🔐 Security Best Practices

1. **Never commit `.env` file** to Git (it contains passwords)
2. Use **App Passwords**, not your main email password
3. Enable **2-Factor Authentication** on your email account
4. Use a **dedicated email account** for system alerts (optional)
5. **Rotate passwords** regularly

---

## ⚙️ Advanced Configuration

### Add Multiple Recipients

Edit `email_alerts.py`:
```python
ADMIN_EMAIL = "admin1@example.com,admin2@example.com,admin3@example.com"
```

### Customize Email Template

Edit `_create_soc_alert_html()` in `email_alerts.py` to customize:
- Colors
- Layout
- Additional information
- Branding/logo

### Add Attachments (e.g., logs)

```python
from email.mime.application import MIMEApplication

# In send_alert_email():
with open('logs/anomaly.log', 'rb') as f:
    attachment = MIMEApplication(f.read(), _subtype='txt')
    attachment.add_header('Content-Disposition', 'attachment', filename='anomaly.log')
    message.attach(attachment)
```

---

## 🎯 Email Alert Workflow

```
Anomaly Detected (risk >= 0.8)
    ↓
Extract Anomaly Data
    ↓
Create Alert Email (HTML + Plain Text)
    ↓
asyncio.create_task(send_alert_email())  ← Non-blocking!
    ↓
API Request Completes ← User gets response immediately
    ↓
(Background) Email Sends via SMTP
    ↓
Admin Receives Alert Email
```

---

## 📞 Support

### Common Issues
- **Gmail**: App passwords required (not regular password)
- **Office 365**: Use smtp.office365.com
- **Yahoo**: App passwords may be required
- **Custom SMTP**: Check with your email provider

### Logs
Check backend console for:
- `✅ Alert email sent to ...`
- `❌ Failed to send alert email: ...`
- `📧 Email alert triggered for ...`

---

## ✅ Verification Checklist

- [ ] `pip install aiosmtplib` completed
- [ ] `.env` file created with SMTP settings
- [ ] Gmail App Password generated (if using Gmail)
- [ ] Test email script runs successfully
- [ ] Test email received at ADMIN_EMAIL
- [ ] Backend shows "📧 Email alert triggered" in logs
- [ ] Email NOT sent for simulation traffic (correct behavior)
- [ ] Email sent for live anomalies with risk >= 0.8

---

**Last Updated**: February 2024  
**Status**: ✅ Production Ready  
**Admin Email**: sahanaramachandran2003@gmail.com
