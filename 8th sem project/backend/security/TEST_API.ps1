# ========================================
# IP Risk Engine - PowerShell Test Script
# ========================================
# Quick API testing without Python dependencies
# ========================================

$BASE_URL = "http://localhost:8000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  IP Risk Engine - API Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to print section headers
function Print-Section {
    param($Title)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "  $Title" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
}

# Function to pretty print JSON
function Print-Response {
    param($Response)
    Write-Host "Status Code: $($Response.StatusCode)" -ForegroundColor Green
    Write-Host ($Response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10)
}

# Test 1: Health Check
Print-Section "Test 1: Health Check"
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/health" -Method GET
    Print-Response $response
    Write-Host "✓ Health check passed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the server is running:" -ForegroundColor Yellow
    Write-Host "  START_RISK_ENGINE.bat" -ForegroundColor Yellow
    exit 1
}

# Test 2: Risk Analysis Endpoint
Print-Section "Test 2: Risk Analysis (Normal IP)"
Write-Host "Sending 5 requests from IP 192.168.1.100..." -ForegroundColor Cyan

for ($i = 1; $i -le 5; $i++) {
    Write-Host "`nRequest $i of 5:" -ForegroundColor Cyan
    
    $headers = @{
        "X-Forwarded-For" = "192.168.1.100"
    }
    
    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api" -Method POST -Headers $headers
        $data = $response.Content | ConvertFrom-Json
        
        Write-Host "  IP: $($data.ip)"
        Write-Host "  Risk Score: $($data.risk_score)"
        Write-Host "  Blocked: $($data.blocked_status)"
        Write-Host "  Request Count: $($data.request_count)"
        Write-Host "  Average Risk: $($data.average_risk)"
        
        Start-Sleep -Milliseconds 300
    }
    catch {
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n✓ Normal traffic test completed" -ForegroundColor Green

# Test 3: High Risk IP
Print-Section "Test 3: High Risk IP (May Get Blocked)"
Write-Host "Sending requests from IP 10.0.0.50..." -ForegroundColor Cyan
Write-Host "(Risk scores are random - may need multiple runs to trigger block)" -ForegroundColor Gray

$blocked = $false
for ($i = 1; $i -le 10; $i++) {
    Write-Host "`nRequest $i of 10:" -ForegroundColor Cyan
    
    $headers = @{
        "X-Forwarded-For" = "10.0.0.50"
    }
    
    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api" -Method POST -Headers $headers
        $data = $response.Content | ConvertFrom-Json
        
        Write-Host "  Risk Score: $($data.risk_score)"
        Write-Host "  Average Risk: $($data.average_risk)"
        Write-Host "  Blocked: $($data.blocked_status)" -ForegroundColor $(if ($data.blocked_status) { "Red" } else { "Green" })
        
        if ($data.blocked_status) {
            Write-Host "`n⚠️  IP WAS BLOCKED!" -ForegroundColor Red
            $blocked = $true
            break
        }
        
        Start-Sleep -Milliseconds 300
    }
    catch {
        $errorData = $_.ErrorDetails.Message | ConvertFrom-Json
        if ($errorData.error -eq "IP blocked") {
            Write-Host "`n⚠️  IP IS BLOCKED!" -ForegroundColor Red
            Write-Host "  Error: $($errorData.error)"
            Write-Host "  Message: $($errorData.message)"
            $blocked = $true
            break
        }
        else {
            Write-Host "  Error: $_" -ForegroundColor Red
        }
    }
}

if (-not $blocked) {
    Write-Host "`n⚠️  IP was not blocked (risk scores were too low)" -ForegroundColor Yellow
    Write-Host "   This is expected due to random risk simulation" -ForegroundColor Gray
}

# Test 4: Suspicious IPs Tracking
Print-Section "Test 4: Suspicious IPs Tracking"

try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/suspicious-ips" -Method GET
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "Total IPs Tracked: $($data.total_ips_tracked)" -ForegroundColor Cyan
    Write-Host "Blocked IPs: $($data.blocked_ips_count)" -ForegroundColor $(if ($data.blocked_ips_count -gt 0) { "Red" } else { "Green" })
    
    Write-Host "`nTracking Details:" -ForegroundColor Yellow
    $data.tracking_data.PSObject.Properties | ForEach-Object {
        $ip = $_.Name
        $stats = $_.Value
        
        Write-Host "`n  IP: $ip"
        Write-Host "    Requests: $($stats.request_count)"
        Write-Host "    Average Risk: $([math]::Round($stats.average_risk, 4))"
        Write-Host "    Blocked: $($stats.blocked)" -ForegroundColor $(if ($stats.blocked) { "Red" } else { "Green" })
        Write-Host "    Last Seen: $($stats.last_seen)"
    }
    
    Write-Host "`n✓ Successfully retrieved tracking data" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Test 5: X-Forwarded-For Header Support
Print-Section "Test 5: X-Forwarded-For Header Support"

$testIPs = @("203.0.113.1", "198.51.100.2", "192.0.2.3")

foreach ($ip in $testIPs) {
    Write-Host "`nTesting with IP: $ip" -ForegroundColor Cyan
    
    $headers = @{
        "X-Forwarded-For" = $ip
    }
    
    try {
        $response = Invoke-WebRequest -Uri "$BASE_URL/api" -Method POST -Headers $headers
        $data = $response.Content | ConvertFrom-Json
        
        if ($data.ip -eq $ip) {
            Write-Host "  ✓ IP correctly extracted: $($data.ip)" -ForegroundColor Green
        }
        else {
            Write-Host "  ❌ IP mismatch: Expected $ip, got $($data.ip)" -ForegroundColor Red
        }
        
        Start-Sleep -Milliseconds 300
    }
    catch {
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

# Test 6: Admin Endpoints
Print-Section "Test 6: Admin Endpoints"

Write-Host "Getting blocked IPs list..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$BASE_URL/admin/blocked-ips" -Method GET
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "Blocked IPs Count: $($data.count)"
    
    if ($data.count -gt 0) {
        Write-Host "Blocked IPs:"
        $data.blocked_ips | ForEach-Object {
            Write-Host "  - $_" -ForegroundColor Red
        }
        
        # Try to unblock the first one
        $ipToUnblock = $data.blocked_ips[0]
        Write-Host "`nAttempting to unblock: $ipToUnblock" -ForegroundColor Cyan
        
        try {
            $response = Invoke-WebRequest -Uri "$BASE_URL/admin/unblock/$ipToUnblock" -Method POST
            $unblockData = $response.Content | ConvertFrom-Json
            Write-Host "✓ $($unblockData.message)" -ForegroundColor Green
        }
        catch {
            Write-Host "  Error: $_" -ForegroundColor Red
        }
    }
    else {
        Write-Host "⚠️  No blocked IPs to test unblocking" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Final Summary
Print-Section "Test Summary"
Write-Host ""
Write-Host "✓ All tests completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. View interactive docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  2. Integrate ML models (XGBoost, TF-IDF, Autoencoder)" -ForegroundColor White
Write-Host "  3. Replace random.uniform() with actual risk prediction" -ForegroundColor White
Write-Host "  4. Add authentication to admin endpoints" -ForegroundColor White
Write-Host "  5. Configure CORS for production" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
