# Test Prometheus Alert Rules for SentimentAnalyzer
# TwisterLab v3.2.0 - Phase 3.3
# 
# This script triggers various alert conditions to verify Prometheus alerting works correctly

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("HighErrorRate", "HighLatency", "LowConfidence", "NoKeywords", "All")]
    [string]$TestType = "All",
    
    [Parameter(Mandatory=$false)]
    [string]$ApiUrl = "http://192.168.0.30:30000",
    
    [Parameter(Mandatory=$false)]
    [string]$PrometheusUrl = "http://192.168.0.30:30090"
)

$ErrorActionPreference = "Continue"

function Write-TestHeader {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-TestStep {
    param([string]$Message)
    Write-Host "  → $Message" -ForegroundColor Yellow
}

function Write-TestSuccess {
    param([string]$Message)
    Write-Host "  ✓ $Message" -ForegroundColor Green
}

function Write-TestError {
    param([string]$Message)
    Write-Host "  ✗ $Message" -ForegroundColor Red
}

function Wait-ForAlert {
    param(
        [string]$AlertName,
        [int]$TimeoutMinutes = 6
    )
    
    Write-TestStep "Waiting for alert '$AlertName' to fire (max $TimeoutMinutes min)..."
    $startTime = Get-Date
    $fired = $false
    
    while ((Get-Date) -lt $startTime.AddMinutes($TimeoutMinutes)) {
        try {
            $response = Invoke-WebRequest -Uri "$PrometheusUrl/api/v1/alerts" -UseBasicParsing
            $alerts = ($response.Content | ConvertFrom-Json).data.alerts
            
            $targetAlert = $alerts | Where-Object { $_.labels.alertname -eq $AlertName }
            
            if ($targetAlert -and $targetAlert.state -eq "firing") {
                Write-TestSuccess "Alert '$AlertName' is FIRING!"
                Write-Host "    Value: $($targetAlert.value)" -ForegroundColor White
                Write-Host "    Summary: $($targetAlert.annotations.summary)" -ForegroundColor White
                $fired = $true
                break
            } elseif ($targetAlert -and $targetAlert.state -eq "pending") {
                Write-Host "    Alert pending... (elapsed: $([math]::Round(((Get-Date) - $startTime).TotalSeconds))s)" -ForegroundColor DarkYellow
            } else {
                Write-Host "    Waiting for alert... (elapsed: $([math]::Round(((Get-Date) - $startTime).TotalSeconds))s)" -ForegroundColor DarkGray
            }
        } catch {
            Write-TestError "Error checking alerts: $($_.Exception.Message)"
        }
        
        Start-Sleep -Seconds 15
    }
    
    if (-not $fired) {
        Write-TestError "Alert '$AlertName' did not fire within $TimeoutMinutes minutes"
        return $false
    }
    
    return $true
}

function Test-HighErrorRate {
    Write-TestHeader "TEST 1: High Error Rate Alert (SentimentAnalyzerHighErrorRate)"
    
    Write-TestStep "Generating 50 error requests (empty text)..."
    $errorCount = 0
    for ($i = 1; $i -le 50; $i++) {
        try {
            $body = @{text=""; detailed=$false} | ConvertTo-Json
            $response = Invoke-WebRequest `
                -Uri "$ApiUrl/api/v1/mcp/analyze_sentiment" `
                -Method POST `
                -ContentType "application/json" `
                -Body $body `
                -UseBasicParsing
            
            if ($response.StatusCode -ne 200) {
                $errorCount++
            }
        } catch {
            $errorCount++
        }
        
        if ($i % 10 -eq 0) {
            Write-Host "    Sent $i/50 error requests..." -ForegroundColor DarkGray
        }
    }
    
    Write-TestSuccess "Sent 50 error requests (expected $errorCount errors)"
    
    # Wait for alert to fire (threshold: >10% error rate over 5 min)
    Wait-ForAlert -AlertName "SentimentAnalyzerHighErrorRate"
}

function Test-LowConfidence {
    Write-TestHeader "TEST 2: Low Confidence Alert (SentimentAnalyzerLowConfidence)"
    
    Write-TestStep "Generating 30 ambiguous/neutral texts (low confidence expected)..."
    
    $ambiguousTexts = @(
        "It's okay",
        "Not bad",
        "Could be better",
        "It works",
        "Average",
        "Meh",
        "Fine I guess",
        "So-so",
        "Acceptable",
        "Nothing special"
    )
    
    $lowConfidenceCount = 0
    for ($i = 1; $i -le 30; $i++) {
        $text = $ambiguousTexts[$i % $ambiguousTexts.Length]
        
        try {
            $body = @{text=$text; detailed=$true} | ConvertTo-Json
            $response = Invoke-WebRequest `
                -Uri "$ApiUrl/api/v1/mcp/analyze_sentiment" `
                -Method POST `
                -ContentType "application/json" `
                -Body $body `
                -UseBasicParsing
            
            $result = ($response.Content | ConvertFrom-Json).content[0].text | ConvertFrom-Json
            
            if ($result.confidence -lt 0.5) {
                $lowConfidenceCount++
            }
            
            if ($i % 10 -eq 0) {
                Write-Host "    Sent $i/30 ambiguous texts..." -ForegroundColor DarkGray
            }
        } catch {
            Write-TestError "Request failed: $($_.Exception.Message)"
        }
    }
    
    $lowConfidencePct = [math]::Round(($lowConfidenceCount / 30) * 100, 1)
    Write-TestSuccess "Sent 30 requests, $lowConfidenceCount had confidence <0.5 ($lowConfidencePct%)"
    
    if ($lowConfidencePct -gt 20) {
        Write-Host "    Expected to trigger alert (threshold: >20%)" -ForegroundColor Yellow
        Wait-ForAlert -AlertName "SentimentAnalyzerLowConfidence" -TimeoutMinutes 12
    } else {
        Write-Host "    Low confidence rate too low to trigger alert ($lowConfidencePct% < 20%)" -ForegroundColor DarkYellow
    }
}

function Test-NoKeywordMatches {
    Write-TestHeader "TEST 3: No Keyword Matches Alert (SentimentAnalyzerNoKeywordMatches)"
    
    Write-TestStep "Generating 30 texts with no sentiment keywords..."
    
    $noKeywordTexts = @(
        "12345",
        "xyz abc def",
        "Lorem ipsum dolor",
        "Test test test",
        "1 2 3 4 5",
        "AAAA BBBB CCCC",
        "qwerty uiop",
        "Random words here",
        "Some text",
        "More text"
    )
    
    $zeroKeywordCount = 0
    for ($i = 1; $i -le 30; $i++) {
        $text = $noKeywordTexts[$i % $noKeywordTexts.Length]
        
        try {
            $body = @{text=$text; detailed=$true} | ConvertTo-Json
            $response = Invoke-WebRequest `
                -Uri "$ApiUrl/api/v1/mcp/analyze_sentiment" `
                -Method POST `
                -ContentType "application/json" `
                -Body $body `
                -UseBasicParsing
            
            $result = ($response.Content | ConvertFrom-Json).content[0].text | ConvertFrom-Json
            
            if ($result.PSObject.Properties['keywords'] -and $result.keywords.Count -eq 0) {
                $zeroKeywordCount++
            }
            
            if ($i % 10 -eq 0) {
                Write-Host "    Sent $i/30 non-keyword texts..." -ForegroundColor DarkGray
            }
        } catch {
            Write-TestError "Request failed: $($_.Exception.Message)"
        }
    }
    
    $zeroKeywordPct = [math]::Round(($zeroKeywordCount / 30) * 100, 1)
    Write-TestSuccess "Sent 30 requests, $zeroKeywordCount had 0 keywords ($zeroKeywordPct%)"
    
    if ($zeroKeywordPct -gt 50) {
        Write-Host "    Expected to trigger alert (threshold: >50%)" -ForegroundColor Yellow
        Wait-ForAlert -AlertName "SentimentAnalyzerNoKeywordMatches" -TimeoutMinutes 12
    } else {
        Write-Host "    Zero keyword rate too low to trigger alert ($zeroKeywordPct% < 50%)" -ForegroundColor DarkYellow
    }
}

function Test-AllAlerts {
    Write-TestHeader "RUNNING ALL ALERT TESTS"
    
    Test-HighErrorRate
    Start-Sleep -Seconds 30  # Brief pause between tests
    
    Test-LowConfidence
    Start-Sleep -Seconds 30
    
    Test-NoKeywordMatches
    
    Write-TestHeader "ALL TESTS COMPLETE"
    Write-Host "Check Prometheus UI for active alerts:" -ForegroundColor Cyan
    Write-Host "  $PrometheusUrl/alerts" -ForegroundColor White
}

function Show-CurrentAlerts {
    Write-TestHeader "CURRENT ACTIVE ALERTS"
    
    try {
        $response = Invoke-WebRequest -Uri "$PrometheusUrl/api/v1/alerts" -UseBasicParsing
        $alerts = ($response.Content | ConvertFrom-Json).data.alerts
        
        if ($alerts.Count -eq 0) {
            Write-Host "  No active alerts" -ForegroundColor Green
            return
        }
        
        foreach ($alert in $alerts) {
            $color = switch ($alert.labels.severity) {
                "critical" { "Red" }
                "warning" { "Yellow" }
                "info" { "Cyan" }
                default { "White" }
            }
            
            Write-Host "`n  Alert: $($alert.labels.alertname)" -ForegroundColor $color
            Write-Host "    State: $($alert.state)" -ForegroundColor $color
            Write-Host "    Severity: $($alert.labels.severity)" -ForegroundColor $color
            Write-Host "    Value: $($alert.value)" -ForegroundColor White
            Write-Host "    Summary: $($alert.annotations.summary)" -ForegroundColor White
        }
    } catch {
        Write-TestError "Failed to fetch alerts: $($_.Exception.Message)"
    }
}

# Main execution
Write-Host @"

╔═══════════════════════════════════════════════════════════╗
║  TwisterLab - Prometheus Alert Testing                   ║
║  Version: v3.2.0 | Phase: 3.3                            ║
╚═══════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

Write-Host "Configuration:" -ForegroundColor White
Write-Host "  API URL: $ApiUrl" -ForegroundColor Gray
Write-Host "  Prometheus URL: $PrometheusUrl" -ForegroundColor Gray
Write-Host "  Test Type: $TestType`n" -ForegroundColor Gray

# Verify connectivity
Write-TestStep "Verifying API connectivity..."
try {
    $health = Invoke-WebRequest -Uri "$ApiUrl/health" -UseBasicParsing -TimeoutSec 5
    Write-TestSuccess "API is reachable (Status: $($health.StatusCode))"
} catch {
    Write-TestError "Cannot reach API at $ApiUrl"
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-TestStep "Verifying Prometheus connectivity..."
try {
    $prom = Invoke-WebRequest -Uri "$PrometheusUrl/-/ready" -UseBasicParsing -TimeoutSec 5
    Write-TestSuccess "Prometheus is reachable (Status: $($prom.StatusCode))"
} catch {
    Write-TestError "Cannot reach Prometheus at $PrometheusUrl"
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Show current alerts before testing
Show-CurrentAlerts

# Run selected test
switch ($TestType) {
    "HighErrorRate" { Test-HighErrorRate }
    "LowConfidence" { Test-LowConfidence }
    "NoKeywords" { Test-NoKeywordMatches }
    "All" { Test-AllAlerts }
}

# Show final alert state
Start-Sleep -Seconds 5
Show-CurrentAlerts

Write-Host "`n✓ Testing complete!`n" -ForegroundColor Green
