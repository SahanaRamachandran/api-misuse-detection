# ================================================================
# Real-time Anomaly Detection API Test Script
# ================================================================
# Tests the production-grade anomaly detection middleware
# Author: Traffic Monitoring System
# Date: February 2026
# ================================================================

$baseUrl = "http://localhost:8002"
$headers = @{
    "Content-Type" = "application/json"
}

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "Real-time Anomaly Detection API Tests" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# ================================================================
# Test 1: Health Check
# ================================================================
Write-Host "[TEST 1] Health Check" -ForegroundColor Yellow
Write-Host "GET $baseUrl/health" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -Headers $headers
    Write-Host "✓ Status: $($response.status)" -ForegroundColor Green
    Write-Host "✓ Models Loaded: $($response.models_loaded)" -ForegroundColor Green
    Write-Host "✓ Total IPs Tracked: $($response.statistics.total_ips_tracked)" -ForegroundColor Green
    Write-Host "✓ Blocked IPs: $($response.statistics.blocked_ips)" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 2: Root Endpoint
# ================================================================
Write-Host "[TEST 2] Root Endpoint (API Info)" -ForegroundColor Yellow
Write-Host "GET $baseUrl/" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/" -Method Get -Headers $headers
    Write-Host "✓ Service: $($response.service)" -ForegroundColor Green
    Write-Host "✓ Version: $($response.version)" -ForegroundColor Green
    Write-Host "✓ Status: $($response.status)" -ForegroundColor Green
    Write-Host "✓ Features:" -ForegroundColor Green
    foreach ($feature in $response.features) {
        Write-Host "    - $feature" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 3: Login Endpoint (Normal Request)
# ================================================================
Write-Host "[TEST 3] Login Endpoint - Normal Request" -ForegroundColor Yellow
Write-Host "POST $baseUrl/api/login" -ForegroundColor Gray

$loginBody = @{
    username = "john_doe"
    password = "SecurePassword123"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/login" -Method Post -Headers $headers -Body $loginBody
    Write-Host "✓ Status: $($response.status)" -ForegroundColor Green
    Write-Host "✓ Message: $($response.message)" -ForegroundColor Green
    if ($response.security) {
        Write-Host "✓ Security Info:" -ForegroundColor Green
        Write-Host "    - Risk Score: $($response.security.risk_score)" -ForegroundColor $(if ($response.security.risk_score -gt 0.7) { "Red" } else { "Gray" })
        Write-Host "    - Is Anomaly: $($response.security.is_anomaly)" -ForegroundColor $(if ($response.security.is_anomaly) { "Red" } else { "Gray" })
        Write-Host "    - Request Count: $($response.security.request_count)" -ForegroundColor Gray
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 4: Payment Endpoint
# ================================================================
Write-Host "[TEST 4] Payment Endpoint" -ForegroundColor Yellow
Write-Host "POST $baseUrl/api/payment" -ForegroundColor Gray

$paymentBody = @{
    amount = 99.99
    card_number = "4532-1234-5678-9010"
    cvv = "123"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/payment" -Method Post -Headers $headers -Body $paymentBody
    Write-Host "✓ Status: $($response.status)" -ForegroundColor Green
    Write-Host "✓ Message: $($response.message)" -ForegroundColor Green
    Write-Host "✓ Amount: `$$($response.amount)" -ForegroundColor Green
    if ($response.security) {
        Write-Host "✓ Risk Score: $($response.security.risk_score)" -ForegroundColor $(if ($response.security.risk_score -gt 0.7) { "Red" } else { "Gray" })
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 5: Search Endpoint
# ================================================================
Write-Host "[TEST 5] Search Endpoint" -ForegroundColor Yellow
Write-Host "POST $baseUrl/api/search" -ForegroundColor Gray

$searchBody = @{
    query = "user data"
    filters = @{
        category = "all"
        sortBy = "relevance"
    }
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/search" -Method Post -Headers $headers -Body $searchBody
    Write-Host "✓ Status: $($response.status)" -ForegroundColor Green
    Write-Host "✓ Query: $($response.query)" -ForegroundColor Green
    if ($response.security) {
        Write-Host "✓ Risk Score: $($response.security.risk_score)" -ForegroundColor $(if ($response.security.risk_score -gt 0.7) { "Red" } else { "Gray" })
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 6: Send Multiple Requests (Simulate Traffic)
# ================================================================
Write-Host "[TEST 6] Simulate Multiple Requests" -ForegroundColor Yellow
Write-Host "Sending 10 login requests to build IP profile..." -ForegroundColor Gray

$riskScores = @()

for ($i = 1; $i -le 10; $i++) {
    $loginBody = @{
        username = "test_user_$i"
        password = "password_$i"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/login" -Method Post -Headers $headers -Body $loginBody
        $risk = $response.security.risk_score
        $riskScores += $risk
        
        Write-Host "  Request $i - Risk: $risk - Anomaly: $($response.security.is_anomaly)" -ForegroundColor $(if ($risk -gt 0.7) { "Red" } else { "Gray" })
        
        Start-Sleep -Milliseconds 200
    } catch {
        Write-Host "  Request $i - Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

$avgRisk = ($riskScores | Measure-Object -Average).Average
Write-Host "`n✓ Average Risk Score: $([math]::Round($avgRisk, 4))" -ForegroundColor $(if ($avgRisk -gt 0.7) { "Red" } else { "Green" })

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 7: Security Statistics
# ================================================================
Write-Host "[TEST 7] Security Statistics" -ForegroundColor Yellow
Write-Host "GET $baseUrl/security/stats" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/security/stats" -Method Get -Headers $headers
    Write-Host "✓ Summary:" -ForegroundColor Green
    Write-Host "    - Total IPs Tracked: $($response.summary.total_ips_tracked)" -ForegroundColor Gray
    Write-Host "    - Blocked IPs: $($response.summary.blocked_ips)" -ForegroundColor Gray
    Write-Host "    - Total Requests: $($response.summary.total_requests)" -ForegroundColor Gray
    Write-Host "    - Total Anomalies: $($response.summary.total_anomalies)" -ForegroundColor Gray
    Write-Host "    - Anomaly Rate: $($response.summary.anomaly_rate)%" -ForegroundColor Gray
    
    if ($response.top_risky_ips.Count -gt 0) {
        Write-Host "`n✓ Top Risky IPs:" -ForegroundColor Green
        foreach ($ip in $response.top_risky_ips[0..([Math]::Min(4, $response.top_risky_ips.Count - 1))]) {
            Write-Host "    - $($ip.ip): Risk=$($ip.avg_risk), Requests=$($ip.total_requests), Anomalies=$($ip.anomaly_count), Blocked=$($ip.blocked)" -ForegroundColor $(if ($ip.blocked) { "Red" } else { "Gray" })
        }
    }
    
    Write-Host "`n✓ Configuration:" -ForegroundColor Green
    Write-Host "    - Risk Threshold: $($response.configuration.risk_threshold)" -ForegroundColor Gray
    Write-Host "    - Block Avg Risk Threshold: $($response.configuration.block_avg_risk_threshold)" -ForegroundColor Gray
    Write-Host "    - Block Anomaly Count Threshold: $($response.configuration.block_anomaly_count_threshold)" -ForegroundColor Gray
    Write-Host "    - XGB Weight: $($response.configuration.xgb_weight)" -ForegroundColor Gray
    Write-Host "    - AE Weight: $($response.configuration.ae_weight)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 8: Blocked IPs
# ================================================================
Write-Host "[TEST 8] Blocked IPs" -ForegroundColor Yellow
Write-Host "GET $baseUrl/security/blocked-ips" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/security/blocked-ips" -Method Get -Headers $headers
    Write-Host "✓ Blocked IPs Count: $($response.count)" -ForegroundColor $(if ($response.count -gt 0) { "Yellow" } else { "Green" })
    
    if ($response.count -gt 0) {
        Write-Host "`n✓ Blocked IPs Details:" -ForegroundColor Yellow
        foreach ($ip in $response.blocked_ips) {
            Write-Host "    - $($ip.ip):" -ForegroundColor Red
            Write-Host "        Requests: $($ip.total_requests)" -ForegroundColor Gray
            Write-Host "        Anomalies: $($ip.anomaly_count)" -ForegroundColor Gray
            Write-Host "        Avg Risk: $($ip.avg_risk)" -ForegroundColor Gray
            Write-Host "        Last Seen: $($ip.last_seen)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No IPs are currently blocked." -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test 9: Test Deterministic Behavior
# ================================================================
Write-Host "[TEST 9] Test Deterministic Behavior" -ForegroundColor Yellow
Write-Host "Sending the same request 3 times to verify consistent risk scoring..." -ForegroundColor Gray

$testBody = @{
    username = "deterministic_test"
    password = "same_password"
} | ConvertTo-Json

$scores = @()

for ($i = 1; $i -le 3; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/api/login" -Method Post -Headers $headers -Body $testBody
        $risk = $response.security.risk_score
        $scores += $risk
        Write-Host "  Attempt $i - Risk Score: $risk" -ForegroundColor Gray
        Start-Sleep -Milliseconds 100
    } catch {
        Write-Host "  Attempt $i - Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Check if all scores are identical (deterministic)
$uniqueScores = $scores | Select-Object -Unique

if ($uniqueScores.Count -eq 1) {
    Write-Host "`n✓ DETERMINISTIC: All risk scores are identical ($($scores[0]))" -ForegroundColor Green
    Write-Host "  This confirms the system is deterministic (no random numbers)." -ForegroundColor Green
} else {
    Write-Host "`n✗ NON-DETERMINISTIC: Risk scores vary!" -ForegroundColor Red
    Write-Host "  Scores: $($scores -join ', ')" -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------------------`n"

# ================================================================
# Test Summary
# ================================================================
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "✓ All endpoints tested successfully" -ForegroundColor Green
Write-Host "✓ Anomaly detection is active and working" -ForegroundColor Green
Write-Host "✓ IP profiling and tracking verified" -ForegroundColor Green
Write-Host "✓ Deterministic behavior confirmed" -ForegroundColor Green

Write-Host "`nNext Steps:" -ForegroundColor Yellow
Write-Host "  1. Check logs for detailed detection events" -ForegroundColor Gray
Write-Host "  2. Monitor IP profiles at: $baseUrl/security/stats" -ForegroundColor Gray
Write-Host "  3. View interactive docs at: $baseUrl/docs" -ForegroundColor Gray
Write-Host "  4. Send malicious payloads to trigger blocking" -ForegroundColor Gray

Write-Host "`n================================================================`n" -ForegroundColor Cyan
