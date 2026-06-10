# TwisterLab Alert Testing Script
# This script helps test and validate your Prometheus alerting rules

$ErrorActionPreference = "Stop"

Write-Host "🧪 TwisterLab Alert Testing Suite" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

function Test-PrometheusConnection {
    Write-Host "Testing Prometheus connection..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Prometheus is healthy" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "✗ Cannot connect to Prometheus" -ForegroundColor Red
        Write-Host "  Run: kubectl port-forward -n monitoring svc/prometheus 9090:9090" -ForegroundColor Yellow
        return $false
    }
}

function Get-LoadedRules {
    Write-Host "`nChecking loaded alert rules..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/rules" -ErrorAction Stop
        
        $twisterlabGroups = $response.data.groups | Where-Object { $_.name -like "twisterlab_*" }
        
        if ($twisterlabGroups) {
            Write-Host "✓ Found TwisterLab rule groups:" -ForegroundColor Green
            foreach ($group in $twisterlabGroups) {
                Write-Host "  - $($group.name): $($group.rules.Count) rules" -ForegroundColor Cyan
            }
            return $true
        } else {
            Write-Host "✗ No TwisterLab rule groups found" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Failed to fetch rules: $_" -ForegroundColor Red
        return $false
    }
}

function Get-ActiveAlerts {
    Write-Host "`nChecking active alerts..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/alerts" -ErrorAction Stop
        
        $firingAlerts = $response.data.alerts | Where-Object { $_.state -eq "firing" }
        
        if ($firingAlerts.Count -gt 0) {
            Write-Host "⚠ $($firingAlerts.Count) alert(s) currently firing:" -ForegroundColor Yellow
            foreach ($alert in $firingAlerts) {
                Write-Host "  - $($alert.labels.alertname) [$($alert.labels.severity)]" -ForegroundColor Red
                Write-Host "    $($alert.annotations.summary)" -ForegroundColor Gray
            }
        } else {
            Write-Host "✓ No alerts currently firing" -ForegroundColor Green
        }
        
        return $true
    } catch {
        Write-Host "✗ Failed to fetch alerts: $_" -ForegroundColor Red
        return $false
    }
}

function Test-MetricAvailability {
    Write-Host "`nChecking metric availability..." -ForegroundColor Yellow
    
    $metrics = @(
        "twisterlab_registry_agents_online",
        "twisterlab_agent_resolution_total",
        "twisterlab_agent_errors_total",
        "twisterlab_agent_call_duration_seconds_bucket"
    )
    
    $available = 0
    foreach ($metric in $metrics) {
        try {
            $query = "up{job=`"twisterlab-api`"}"
            if ($metric -ne $metrics[0]) {
                $query = $metric
            }
            
            $response = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/query?query=$query" -ErrorAction Stop
            
            if ($response.data.result.Count -gt 0) {
                Write-Host "  ✓ $metric" -ForegroundColor Green
                $available++
            } else {
                Write-Host "  ✗ $metric (no data)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ✗ $metric (error)" -ForegroundColor Red
        }
    }
    
    if ($available -eq $metrics.Count) {
        Write-Host "`n✓ All metrics available" -ForegroundColor Green
        return $true
    } else {
        Write-Host "`n⚠ Only $available/$($metrics.Count) metrics available" -ForegroundColor Yellow
        return $false
    }
}

function Test-AgentDropoutAlert {
    Write-Host "`n🔬 Test: Agent Dropout Alert" -ForegroundColor Cyan
    Write-Host "This test will scale down agents to trigger the alert" -ForegroundColor Gray
    
    $confirm = Read-Host "Continue? (y/n)"
    if ($confirm -ne "y") {
        Write-Host "Skipped" -ForegroundColor Yellow
        return
    }
    
    Write-Host "`nStep 1: Getting current agent count..." -ForegroundColor Yellow
    $originalReplicas = kubectl get deployment twisterlab-agents -n twisterlab -o jsonpath='{.spec.replicas}'
    Write-Host "Current replicas: $originalReplicas"
    
    Write-Host "`nStep 2: Scaling down to 2 replicas..." -ForegroundColor Yellow
    kubectl scale deployment/twisterlab-agents --replicas=2 -n twisterlab
    Write-Host "✓ Scaled down" -ForegroundColor Green
    
    Write-Host "`nStep 3: Waiting 2 minutes for alert to fire..." -ForegroundColor Yellow
    for ($i = 120; $i -gt 0; $i -= 10) {
        Write-Host "  $i seconds remaining..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
    }
    
    Write-Host "`nStep 4: Checking if alert fired..." -ForegroundColor Yellow
    $response = Invoke-RestMethod -Uri "http://localhost:9090/api/v1/alerts"
    $dropoutAlert = $response.data.alerts | Where-Object { $_.labels.alertname -eq "CriticalAgentDropout" -and $_.state -eq "firing" }
    
    if ($dropoutAlert) {
        Write-Host "✓ Alert successfully fired!" -ForegroundColor Green
    } else {
        Write-Host "✗ Alert did not fire (check configuration)" -ForegroundColor Red
    }
    
    Write-Host "`nStep 5: Restoring original replica count..." -ForegroundColor Yellow
    kubectl scale deployment/twisterlab-agents --replicas=$originalReplicas -n twisterlab
    Write-Host "✓ Restored to $originalReplicas replicas" -ForegroundColor Green
}

# Main execution
Write-Host "Starting validation..." -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

if (-not (Test-PrometheusConnection)) { $allPassed = $false }
if (-not (Get-LoadedRules)) { $allPassed = $false }
if (-not (Get-ActiveAlerts)) { $allPassed = $false }
if (-not (Test-MetricAvailability)) { $allPassed = $false }

Write-Host "`n===================================" -ForegroundColor Cyan

if ($allPassed) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    Write-Host "`nOptional: Run live alert test" -ForegroundColor Cyan
    Test-AgentDropoutAlert
} else {
    Write-Host "⚠ Some checks failed" -ForegroundColor Yellow
    Write-Host "Review the output above for details" -ForegroundColor Gray
}

Write-Host "`n📖 For more information, see:" -ForegroundColor Cyan
Write-Host "   docs/prometheus-alerting-setup.md" -ForegroundColor Gray
Write-Host ""
