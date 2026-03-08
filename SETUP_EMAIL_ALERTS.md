# 📧 Email Alerts - Quick Setup Guide

## ✅ What's Already Done
- ✅ Email alert code implemented in `backend/email_alerts.py`
- ✅ `aiosmtplib` package installed
- ✅ `.env` configuration file created
- ✅ Integration with anomaly detection system

---

## 🔧 Configuration Required (2 minutes)

### Step 1: Get Gmail App Password

1. **Enable 2-Factor Authentication** on your Gmail account:
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Select app: **Mail**
   - Select device: **Other (Custom name)** → Type "Traffic Monitor"
   - Click **Generate**
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 2: Configure Email Settings

Edit the file: `8th sem project\backend\.env`

Replace these lines:
```env
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

With your actual credentials:
```env
SMTP_USER=youremail@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
```

**IMPORTANT**: 
- Remove all spaces from the app password
- Use the **App Password**, NOT your regular Gmail password
- Admin email is already set to: `sahanaramachandran2003@gmail.com`

---

## 🧪 Test Email System

Run this command to send a test email:

```powershell
cd "8th sem project\backend"
& "..\..\..venv\Scripts\Activate.ps1"
python email_alerts.py
```

**Expected Output:**
```
============================================================
EMAIL ALERT SYSTEM - TEST MODE
============================================================
SMTP Host: smtp.gmail.com
SMTP Port: 587
SMTP User: youremail@...
Admin Email: sahanaramachandran2003@gmail.com

Sending test email alert...

✅ Test email sent successfully!
```

**Check Email:**
- Go to: sahanaramachandran2003@gmail.com inbox
- Look for: `🚨 SECURITY ALERT [CRITICAL] - SQL INJECTION DETECTED`

---

## 🎯 How Email Alerts Work

### Alert Triggers
Emails are automatically sent when:
- **Risk Score ≥ 80%** (High confidence threat)
- **Severity = CRITICAL**

### What's in the Alert Email

**Subject:**
```
🚨 SECURITY ALERT [CRITICAL] - SQL INJECTION DETECTED
```

**Email Contains:**
1. **Threat Metrics**
   - Risk Score (e.g., 92%)
   - Confidence Level
   - Severity Rating

2. **Attack Details**
   - Attack Type (SQL Injection, XSS, DDoS, etc.)
   - Source IP Address
   - Target Endpoint
   - HTTP Method
   - Detection Timestamp

3. **System Response**
   - IP Block Status
   - Detection Model Used

4. **Recommended Actions**
   - Review activity logs
   - Verify attack pattern
   - Check firewall rules
   - Document incident

---

## 🚀 Live Testing

### Start the System
```powershell
# Terminal 1 - Backend
cd "8th sem project\backend"
& "..\..\..venv\Scripts\Activate.ps1"
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd "8th sem project\frontend"
npm run dev
```

### Trigger Real Alerts

1. **Open Dashboard**: http://localhost:5173
2. **Go to Admin Panel**
3. **Start Enhanced Simulation**
4. **Select Attack Types**: SQL Injection, XSS, DDoS
5. **Wait 30-60 seconds**
6. **Check Email**: sahanaramachandran2003@gmail.com

You'll receive professional SOC-style alerts for each critical threat detected!

---

## ⚙️ Configuration Options

### Change Alert Threshold

Edit `backend/email_alerts.py`, line 26:
```python
ALERT_THRESHOLD = 0.8  # 80% minimum
# Change to 0.7 for 70% threshold (more alerts)
# Change to 0.9 for 90% threshold (fewer, critical only)
```

### Add Multiple Recipients

Edit `backend/.env`:
```env
ADMIN_EMAIL=admin1@company.com,admin2@company.com,admin3@company.com
```

### Use Different Email Provider

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

---

## 🚫 Troubleshooting

### "SMTP credentials not configured"
**Solution:** Edit `.env` file and add SMTP_USER and SMTP_PASSWORD

### "Failed to send alert email: Authentication failed"
**Solutions:**
1. Verify 2FA is enabled on Gmail
2. Use **App Password**, not regular password
3. Remove all spaces from app password
4. Verify SMTP_USER matches your Gmail address

### "No emails received"
**Solutions:**
1. Check spam/junk folder
2. Verify ADMIN_EMAIL is correct
3. Run test: `python email_alerts.py`
4. Check backend console for errors

### "Email alerts not available"
**Solution:** 
```powershell
pip install aiosmtplib
```

---

## 📊 Email Alert Flow

```
1. Anomaly Detected (Risk ≥ 80%)
        ↓
2. Email Alert Triggered (Async)
        ↓
3. Professional HTML Email Created
        ↓
4. Sent via SMTP (Gmail)
        ↓
5. Admin Receives Alert
        ↓
6. Admin Takes Action
```

---

## 🔐 Security Best Practices

✅ **DO:**
- Use App Passwords for Gmail
- Enable 2-Factor Authentication
- Keep `.env` file secure (not in git)
- Use HTTPS for email providers
- Monitor alert frequency

❌ **DON'T:**
- Share SMTP passwords
- Commit `.env` to version control
- Use regular Gmail password
- Send unnecessary alerts (spam)

---

## 📁 Related Files

- **Email System**: `backend/email_alerts.py`
- **Configuration**: `backend/.env`
- **Config Template**: `backend/.env.example`
- **Integration**: `backend/security/realtime_detection.py`
- **Setup Script**: `backend/INSTALL_EMAIL_ALERTS.ps1`

---

## ✅ Quick Checklist

- [ ] 2FA enabled on Gmail
- [ ] App Password generated
- [ ] `.env` file configured
- [ ] Test email sent successfully (`python email_alerts.py`)
- [ ] Test email received at ADMIN_EMAIL
- [ ] Backend shows "📧 Email alert triggered" during simulation
- [ ] Alerts received for critical threats (Risk ≥ 80%)

---

## 📞 Support

**Status**: ✅ Email alerts fully implemented and ready to use

**Admin Email**: sahanaramachandran2003@gmail.com

**Documentation**:
- Full setup: `EMAIL_ALERTS_SETUP.md`
- Critical alerts: `CRITICAL_ALERTS_SETUP.md`
- Testing guide: `QUICK_START_TESTING_GUIDE.md`

---

**Last Updated**: February 24, 2026  
**Version**: 1.0.0  
**Status**: Production Ready 🚀
