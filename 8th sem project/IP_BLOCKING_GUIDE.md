# IP Blocking & Admin Panel Guide

## ✅ Implementation Complete

Your IP tracking and blocking system is now fully implemented and working!

## 🎯 Features

### Automatic IP Tracking
- ✓ All incoming requests are automatically tracked by IP address
- ✓ Each IP has a profile with:
  - Total requests count
  - Anomaly count (requests flagged as suspicious)
  - Average risk score (0.0 to 1.0)
  - Last seen timestamp
  - Blocked status

### Automatic Blocking
- ✓ **When an IP exceeds 5 anomalies, it gets automatically blocked**
- ✓ Blocked IPs receive a 403 Forbidden response on all future requests
- ✓ Blocking is immediate and prevents further access
- ✓ Simulation IPs are tracked separately and never auto-blocked

### Admin Panel
- ✓ View all blocked IPs with details
- ✓ View all tracked IPs (both blocked and active)
- ✓ Manually unblock IPs with one click
- ✓ Real-time statistics (auto-refreshes every 5 seconds)
- ✓ Color-coded risk levels:
  - 🔴 Red: Critical (80%+ risk)
  - 🟠 Orange: High (60%+ risk)
  - 🟡 Yellow: Medium (40%+ risk)
  - 🟢 Green: Low (<40% risk)

## 📍 How to Access

1. **Start your backend** (if not running):
   ```powershell
   cd "8th sem project"
   .\.venv\Scripts\Activate.ps1
   cd backend
   python app.py
   ```

2. **Start your frontend** (if not running):
   ```powershell
   cd "8th sem project\frontend"
   npm run dev
   ```

3. **Navigate to Admin Panel**:
   - Open your browser to: `http://localhost:5173`
   - Click on **⚙️ Admin Panel** in the navigation bar
   - Or go directly to: `http://localhost:5173/admin`

## 🔍 What You'll See

### Statistics Dashboard
- **Blocked IPs** - Total number of currently blocked IPs
- **Tracked IPs** - Total IPs being monitored
- **At Risk (4+ anomalies)** - IPs close to being blocked
- **Clean IPs** - IPs with zero anomalies

### Tabs

#### 1. 🚫 Blocked IPs Tab
Shows all currently blocked IP addresses with:
- IP address (monospace font for clarity)
- Number of anomalies that triggered the block
- Total requests from that IP
- Average risk score (color-coded)
- Last seen timestamp
- **✅ Unblock** button to manually restore access

#### 2. 📊 All Tracked IPs Tab
Shows every IP the system has seen with:
- IP address and simulation badge (if applicable)
- Status: Blocked / At Risk / Active
- Anomaly count vs total requests
- Average risk score
- Last activity timestamp
- Unblock button (for blocked IPs only)

## 🧪 How to Test

### Test 1: View Current Status
1. Go to Admin Panel
2. Check the statistics - should show current IP tracking
3. Toggle auto-refresh on/off to control updates

### Test 2: Simulate Traffic and Blocking
1. Go to the main Dashboard
2. Run a simulation with anomalies:
   - Click "Start Simulation"
   - Select an endpoint
   - Choose "Mixed" anomaly mode
   - Run for 30-60 seconds
3. Go back to Admin Panel
4. You should see tracked IPs with anomaly counts increasing
5. Note: Simulation IPs won't be auto-blocked (marked with "SIM" badge)

### Test 3: Manual Blocking (Live Traffic)
To test real blocking with live traffic:
1. Make 6+ requests to your API that trigger anomalies
2. The IP will automatically be blocked after the 5th anomaly
3. Check Admin Panel to see the blocked IP
4. Try making another request - you'll get a 403 Forbidden
5. Click "Unblock" in Admin Panel
6. The IP can now access the API again

### Test 4: Unblock Functionality
1. In the Admin Panel, find a blocked IP
2. Click the **✅ Unblock** button
3. You'll see a success toast notification
4. The IP disappears from the Blocked IPs tab
5. The IP's profile is reset and can access the API again

## 🔧 Backend Endpoints

The following API endpoints power the admin panel:

### Get System Status
```
GET /api/security/realtime/status
```
Returns all IP profiles and configuration

### Get Blocked IPs
```
GET /api/security/realtime/blocked-ips
```
Returns list of blocked IPs with details

### Get Specific IP Profile
```
GET /api/security/realtime/ip/{ip_address}
```
Returns detailed profile for a specific IP

### Unblock IP
```
POST /api/security/realtime/unblock/{ip_address}
```
Manually unblock an IP address

### Reset System
```
DELETE /api/security/realtime/reset
```
⚠️ Clears all tracking data (use with caution)

## 📊 Configuration

The blocking system uses these thresholds (defined in backend):

- **Risk Threshold**: 0.7 (70%) - Marks request as anomaly
- **Block Avg Risk**: 0.8 (80%) - Minimum average risk for blocking
- **Block Anomaly Count**: 5 - Anomalies needed to trigger block
- **XGBoost Weight**: 0.6 (60%)
- **Autoencoder Weight**: 0.4 (40%)

## 🎨 UI Features

- **Auto-Refresh Toggle** - Control whether data updates automatically
- **Tab Navigation** - Switch between blocked and all IPs
- **Color-Coded Risk** - Visual risk levels at a glance
- **Responsive Design** - Works on different screen sizes
- **Toast Notifications** - Success/error feedback
- **Loading States** - Smooth UX during data fetches
- **Monospace IPs** - Easy to read IP addresses
- **Simulation Badges** - Clearly marks simulation traffic

## 🚀 Next Steps

Your IP blocking system is production-ready! You can now:

1. **Monitor** - Watch IPs in real-time via the admin panel
2. **Manage** - Unblock false positives with one click
3. **Analyze** - Review anomaly patterns across IPs
4. **Demonstrate** - Show the automatic blocking in action
5. **Customize** - Adjust thresholds in `backend/security/realtime_detection.py`

## 💡 Tips

- Keep auto-refresh ON for live monitoring
- Check "At Risk" count to see IPs approaching the threshold
- Use the simulation mode to safely test the system
- Unblock IPs immediately if you notice false positives
- Monitor the average risk scores to tune thresholds

---

**Your IP blocking and admin panel are now fully functional!** 🎉
