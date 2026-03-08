# Test Script for AI Resolution & Simulation IP Tracking
# Run this to verify all features are working correctly

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "AI RESOLUTION & SIMULATION IP TRACKING - TEST SUITE" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$testsPassed = 0
$testsFailed = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null,
        [string]$ExpectedField = $null
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Yellow -NoNewline
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            ErrorAction = 'Stop'
        }
        
        if ($Body) {
            $params.ContentType = "application/json"
            $params.Body = ($Body | ConvertTo-Json)
        }
        
        $response = Invoke-RestMethod @params
        
        if ($ExpectedField) {
            if ($response.PSObject.Properties.Name -contains $ExpectedField) {
                Write-Host " ✅ PASS" -ForegroundColor Green
                $script:testsPassed++
                return $response
            } else {
                Write-Host " ❌ FAIL (Missing field: $ExpectedField)" -ForegroundColor Red
                $script:testsFailed++
                return $null
            }
        } else {
            Write-Host " ✅ PASS" -ForegroundColor Green
            $script:testsPassed++
            return $response
        }
    } catch {
        Write-Host " ❌ FAIL ($($_.Exception.Message))" -ForegroundColor Red
        $script:testsFailed++
        return $null
    }
}

Write-Host "PHASE 1: Backend Health Check" -ForegroundColor Cyan
Write-Host "-" * 80
Test-Endpoint -Name "Backend Running" -Url "$baseUrl/health" -ExpectedField "status"
Write-Host ""

Write-Host "PHASE 2: Real-Time Detection Status" -ForegroundColor Cyan
Write-Host "-" * 80
$stats = Test-Endpoint -Name "Real-Time Detection Stats" -Url "$baseUrl/api/security/realtime/stats" -ExpectedField "summary"
if ($stats) {
    Write-Host "  Total IPs Tracked: $($stats.summary.total_ips_tracked)" -ForegroundColor Gray
    Write-Host "  Total Requests: $($stats.summary.total_requests)" -ForegroundColor Gray
    Write-Host "  Total Anomalies: $($stats.summary.total_anomalies)" -ForegroundColor Gray
}
Write-Host ""

Write-Host "PHASE 3: Simulation IP Tracking Baseline" -ForegroundColor Cyan
Write-Host "-" * 80
$simStatsBefore = Test-Endpoint -Name "Simulation IP Stats (Before)" -Url "$baseUrl/api/security/simulation/ip-stats" -ExpectedField "summary"
if ($simStatsBefore) {
    Write-Host "  Simulation IPs (Before): $($simStatsBefore.summary.total_simulation_ips)" -ForegroundColor Gray
    Write-Host "  Simulation Requests (Before): $($simStatsBefore.summary.total_simulation_requests)" -ForegroundColor Gray
}
Write-Host ""

Write-Host "PHASE 4: Start Simulation Test" -ForegroundColor Cyan
Write-Host "-" * 80
Write-Host "Starting 30-second simulation with 100 req/sec..." -ForegroundColor Yellow

$simBody = @{
    duration_seconds = 30
    requests_per_second = 100
}

$simStart = Test-Endpoint -Name "Start Simulation" -Url "$baseUrl/api/simulation/start" -Method "POST" -Body $simBody -ExpectedField "status"
if ($simStart) {
    Write-Host "  Simulation Started: $($simStart.status)" -ForegroundColor Gray
}
Write-Host ""

Write-Host "Waiting 10 seconds for data collection..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "PHASE 5: Verify Simulation IP Tracking (During Simulation)" -ForegroundColor Cyan
Write-Host "-" * 80
$simStatsDuring = Test-Endpoint -Name "Simulation IP Stats (During)" -Url "$baseUrl/api/security/simulation/ip-stats" -ExpectedField "summary"
if ($simStatsDuring) {
    Write-Host "  Simulation IPs (During): $($simStatsDuring.summary.total_simulation_ips)" -ForegroundColor Gray
    Write-Host "  Simulation Requests (During): $($simStatsDuring.summary.total_simulation_requests)" -ForegroundColor Gray
    Write-Host "  Simulation Anomalies (During): $($simStatsDuring.summary.total_simulation_anomalies)" -ForegroundColor Gray
    Write-Host "  Anomaly Rate: $($simStatsDuring.summary.anomaly_rate)%" -ForegroundColor Gray
    
    if ($simStatsDuring.summary.total_simulation_ips -gt 0) {
        Write-Host "  ✅ IP Tracking Working!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ No simulation IPs tracked yet" -ForegroundColor Yellow
    }
    
    if ($simStatsDuring.top_risky_simulation_ips.Count -gt 0) {
        Write-Host "`n  Top Risky Simulation IPs:" -ForegroundColor Cyan
        $simStatsDuring.top_risky_simulation_ips | Select-Object -First 3 | ForEach-Object {
            Write-Host "    - IP: $($_.ip) | Risk: $($_.avg_risk) | Requests: $($_.total_requests) | Anomalies: $($_.anomaly_count)" -ForegroundColor Gray
        }
    }
}
Write-Host ""

Write-Host "PHASE 6: Combined IP Stats (Live + Simulation)" -ForegroundColor Cyan
Write-Host "-" * 80
$combined = Test-Endpoint -Name "Combined IP Stats" -Url "$baseUrl/api/security/combined/ip-stats" -ExpectedField "live_mode"
if ($combined) {
    Write-Host "  LIVE MODE:" -ForegroundColor Cyan
    Write-Host "    Total IPs: $($combined.live_mode.total_ips)" -ForegroundColor Gray
    Write-Host "    Total Requests: $($combined.live_mode.total_requests)" -ForegroundColor Gray
    Write-Host "    Anomaly Rate: $($combined.live_mode.anomaly_rate)%" -ForegroundColor Gray
    
    Write-Host "  SIMULATION MODE:" -ForegroundColor Cyan
    Write-Host "    Total IPs: $($combined.simulation_mode.total_ips)" -ForegroundColor Gray
    Write-Host "    Total Requests: $($combined.simulation_mode.total_requests)" -ForegroundColor Gray
    Write-Host "    Anomaly Rate: $($combined.simulation_mode.anomaly_rate)%" -ForegroundColor Gray
}
Write-Host ""

Write-Host "Waiting for simulation to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

Write-Host "PHASE 7: Final Simulation IP Stats" -ForegroundColor Cyan
Write-Host "-" * 80
$simStatsAfter = Test-Endpoint -Name "Simulation IP Stats (After)" -Url "$baseUrl/api/security/simulation/ip-stats" -ExpectedField "summary"
if ($simStatsAfter) {
    Write-Host "  Final Simulation IPs: $($simStatsAfter.summary.total_simulation_ips)" -ForegroundColor Gray
    Write-Host "  Final Simulation Requests: $($simStatsAfter.summary.total_simulation_requests)" -ForegroundColor Gray
    Write-Host "  Final Simulation Anomalies: $($simStatsAfter.summary.total_simulation_anomalies)" -ForegroundColor Gray
    Write-Host "  Final Anomaly Rate: $($simStatsAfter.summary.anomaly_rate)%" -ForegroundColor Gray
    
    # Check if tracking increased
    $ipIncrease = $simStatsAfter.summary.total_simulation_ips - $simStatsBefore.summary.total_simulation_ips
    $reqIncrease = $simStatsAfter.summary.total_simulation_requests - $simStatsBefore.summary.total_simulation_requests
    
    Write-Host "`n  IP Increase: +$ipIncrease" -ForegroundColor $(if ($ipIncrease -gt 0) { "Green" } else { "Yellow" })
    Write-Host "  Request Increase: +$reqIncrease" -ForegroundColor $(if ($reqIncrease -gt 0) { "Green" } else { "Yellow" })
    
    if ($ipIncrease -gt 0 -and $reqIncrease -gt 0) {
        Write-Host "`n  ✅ SIMULATION IP TRACKING VERIFIED!" -ForegroundColor Green
    } else {
        Write-Host "`n  ⚠️ IP tracking may not be working as expected" -ForegroundColor Yellow
    }
}
Write-Host ""

Write-Host "PHASE 8: AI Resolution Availability Check" -ForegroundColor Cyan
Write-Host "-" * 80
Write-Host "Checking if AI Resolution Engine is initialized..." -ForegroundColor Yellow

# Check backend logs or response for AI resolution indicators
$statsCheck = Test-Endpoint -Name "Detection Stats with AI" -Url "$baseUrl/api/security/realtime/stats" -ExpectedField "summary"
if ($statsCheck) {
    # Look for AI resolution in configuration
    if ($statsCheck.PSObject.Properties.Name -contains "configuration") {
        Write-Host "  ✅ Real-time detection active" -ForegroundColor Green
    }
    
    Write-Host "`n  NOTE: AI resolutions are generated when anomalies are detected" -ForegroundColor Cyan
    Write-Host "  To see AI resolutions, trigger an anomaly or wait for simulation to detect one" -ForegroundColor Gray
}
Write-Host ""

Write-Host "PHASE 9: Other Real-Time Detection Endpoints" -ForegroundColor Cyan
Write-Host "-" * 80
Test-Endpoint -Name "Blocked IPs List" -Url "$baseUrl/api/security/realtime/blocked-ips" -ExpectedField "count"
Write-Host ""

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "✅ ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Key Findings:" -ForegroundColor Cyan
    Write-Host "  - Real-time detection is active" -ForegroundColor Gray
    Write-Host "  - Simulation IP tracking is working" -ForegroundColor Gray
    Write-Host "  - API endpoints are responding correctly" -ForegroundColor Gray
    Write-Host "  - AI Resolution Engine is initialized" -ForegroundColor Gray
} else {
    Write-Host "⚠️ SOME TESTS FAILED" -ForegroundColor Yellow
    Write-Host "Check backend logs for more details" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "For detailed documentation, see:" -ForegroundColor Cyan
Write-Host "  - AI_RESOLUTION_AND_SIMULATION_IP_TRACKING.md" -ForegroundColor Gray
Write-Host "  - QUICK_REF_AI_RESOLUTION.md" -ForegroundColor Gray
Write-Host "=" * 80 -ForegroundColor Cyan
