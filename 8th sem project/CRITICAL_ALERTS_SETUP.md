# 🚨 Critical Alerts System

## Overview
Email alerts are **automatically sent** when critical anomalies are detected during simulation mode.

---

## ⚡ Alert Triggers

Alerts are sent when **ANY** of these conditions are met:
- ✅ **Risk Score ≥ 80%** (High confidence detection)
- ✅ **Severity = CRITICAL** (Critical threat level)

**Alert Mode:** Simulation Mode only (where actual attacks are injected)

---

## 📧 Quick Setup (Gmail)

### 1. Install Email Package
```powershell
cd "8th sem project\backend"
..\..\..venv\Scripts\Activate.ps1
pip install aiosmtplib
```

### 2. Create `.env` File
Create file: `8th sem project\backend\.env`

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
ADMIN_EMAIL=sahanaramachandran2003@gmail.com
```

### 3. Get Gmail App Password
1. **Enable 2FA**: https://myaccount.google.com/security
2. **Generate App Password**: https://myaccount.google.com/apppasswords
   - App: Mail
   - Device: Other (Custom) → "Traffic Monitor"
   - Copy 16-character password (remove spaces)
3. **Add to .env**: `SMTP_PASSWORD=abcdabcdabcdabcd`

### 4. Test Email System
```powershell
cd "8th sem project\backend"
python email_alerts.py
```

Expected output:
```
✅ Test email sent successfully!
```

Check **sahanaramachandran2003@gmail.com** inbox.

---

## 🎯 Testing Critical Alerts

### Run Simulation to Trigger Alerts

1. **Start Backend:**
   ```powershell
   cd "8th sem project\backend"
   python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start Frontend:**
   ```powershell
   cd "8th sem project\frontend"
   npm run dev
   ```

3. **Trigger Simulation:**
   - Open dashboard: http://localhost:5173
   - Go to **Admin Panel**
   - Click **Start Enhanced Simulation**
   - Select attack patterns (SQL Injection, XSS, DDoS)

4. **Check Email:**
   - Within 1-2 minutes, critical alerts will be sent
   - Check **sahanaramachandran2003@gmail.com**
   - Email subject: `🚨 SECURITY ALERT [CRITICAL] - SQL INJECTION DETECTED`

---

## 📋 Email Alert Contents

### Subject Line
```
🚨 SECURITY ALERT [CRITICAL] - SQL INJECTION DETECTED
```

### Email Body Includes:
1. **Threat Metrics**
   - Risk Score: 92%
   - Confidence: 88%
   - Severity: CRITICAL

2. **Attack Details**
   - Attack Type (SQL Injection, XSS, DDoS, etc.)
   - Source IP Address
   - Target Endpoint
   - HTTP Method
   - Timestamp

3. **Recommended Actions**
   - Review logs
   - Verify attack pattern
   - Check firewall rules
   - Monitor IP activity

---

## 🔧 Configuration Options

### Change Alert Threshold
Edit `backend/email_alerts.py` line 25:
```python
ALERT_THRESHOLD = 0.8  # Change to 0.7 for 70% threshold
```

### Change Admin Email
Edit `.env` file:
```env
ADMIN_EMAIL=your-admin@company.com
```

### Multiple Recipients
Edit `backend/email_alerts.py` line 76:
```python
message['To'] = "admin1@company.com, admin2@company.com"
```

---

## ✅ Verify Email Alerts Are Working

### Check Console Output During Simulation
Look for:
```
🚨 ANOMALY DETECTED: SQL Injection
   Endpoint: /api/payment
   Severity: CRITICAL
   Risk Score: 92.00/100 (Confidence: 0.920)
   📧 CRITICAL ALERT EMAIL SENT (Risk: 92.00)
```

### Check Email Logs
```
[INFO] ✅ Alert email sent to sahanaramachandran2003@gmail.com for SQL Injection (Risk: 0.92)
```

---

## 🚫 Troubleshooting

### "Email alerts not available"
**Solution:** Install aiosmtplib
```powershell
pip install aiosmtplib
```

### "SMTP credentials not configured"
**Solution:** Create `.env` file with SMTP settings (see Step 2)

### "Failed to send alert email: Authentication failed"
**Solutions:**
1. Verify 2FA is enabled on Gmail
2. Use App Password (not regular password)
3. Remove spaces from app password
4. Check SMTP_USER matches your Gmail address

### No emails received
**Solutions:**
1. Check spam folder
2. Verify ADMIN_EMAIL is correct
3. Run `python email_alerts.py` to test
4. Check backend console for error messages

---

## 📊 Alert Statistics

View alert activity in backend console:
- Total alerts sent
- Risk scores
- Attack types detected
- Timestamps

---

## 🔐 Security Notes

- ✅ Never commit `.env` file to git
- ✅ Use App Passwords (not regular passwords)
- ✅ Emails sent asynchronously (non-blocking)
- ✅ Only critical threats trigger alerts (reduces noise)
- ✅ Professional SOC-style formatting for security teams

---

## 📚 Related Documentation

- Full setup guide: `EMAIL_ALERTS_SETUP.md`
- Testing guide: `QUICK_START_TESTING_GUIDE.md`
- Simulation guide: `HOW_TO_TEST_LIVE_MODE.md`

---

**Status:** ✅ Email alerts integrated and ready to use!
