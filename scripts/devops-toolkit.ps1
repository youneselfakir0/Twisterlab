#!/usr/bin/env pwsh
<#
.SYNOPSIS
    TwisterLab DevOps Automation Script
.DESCRIPTION
    Comprehensive automation script for common DevOps tasks including:
    - Deployment management
    - Health checks and diagnostics
    - Backup and recovery
    - Resource scaling
    - Log analysis
.PARAMETER Action
    The action to perform (deploy, health, backup, scale, logs, debug)
.PARAMETER Environment
    Target environment (dev, staging, production)
.EXAMPLE
    .\devops-toolkit.ps1 -Action health -Environment production
.EXAMPLE
    .\devops-toolkit.ps1 -Action deploy -Environment staging
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("deploy", "health", "backup", "scale", "logs", "debug", "rollback", "security")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "staging", "production")]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [int]$Replicas,
    
    [Parameter(Mandatory=$false)]
    [string]$Component,
    
    [Parameter(Mandatory=$false)]
    [int]$TailLines = 100
)

# Configuration
$NAMESPACE = "twisterlab"
$API_DEPLOYMENT = "twisterlab-api"
$MCP_DEPLOYMENT = "mcp-unified"
$POSTGRES_DEPLOYMENT = "postgres"

# Color output functions
function Write-Success { param($Message) Write-Host "✓ $Message" -ForegroundColor Green }
function Write-Info { param($Message) Write-Host "ℹ $Message" -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host "⚠ $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "✗ $Message" -ForegroundColor Red }

# Health Check Function
function Invoke-HealthCheck {
    Write-Info "Running comprehensive health checks..."
    
    # Check namespace exists
    $namespaceExists = kubectl get namespace $NAMESPACE 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Namespace '$NAMESPACE' does not exist!"
        return $false
    }
    Write-Success "Namespace '$NAMESPACE' exists"
    
    # Check pod status
    Write-Info "Checking pod status..."
    $pods = kubectl get pods -n $NAMESPACE -o json | ConvertFrom-Json
    $healthyPods = 0
    $totalPods = $pods.items.Count
    
    foreach ($pod in $pods.items) {
        $podName = $pod.metadata.name
        $podStatus = $pod.status.phase
        
        if ($podStatus -eq "Running") {
            $containerStatuses = $pod.status.containerStatuses
            $allReady = $true
            foreach ($container in $containerStatuses) {
                if (-not $container.ready) {
                    $allReady = $false
                    Write-Warning "Pod $podName - Container $($container.name) not ready"
                }
            }
            if ($allReady) {
                $healthyPods++
                Write-Success "Pod $podName is healthy"
            }
        } else {
            Write-Error "Pod $podName is in $podStatus state"
        }
    }
    
    Write-Info "Pod Health: $healthyPods/$totalPods healthy"
    
    # Check API endpoint
    Write-Info "Testing API endpoint..."
    $apiUrl = "http://edgeserver.twisterlab.local:30001/health"
    try {
        $response = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 10
        if ($response.status -eq "healthy") {
            Write-Success "API endpoint is healthy"
        } else {
            Write-Warning "API endpoint returned status: $($response.status)"
        }
    } catch {
        Write-Error "API endpoint unreachable: $_"
    }
    
    # Check database connectivity
    Write-Info "Testing database connectivity..."
    $dbTest = kubectl exec deployment/$POSTGRES_DEPLOYMENT -n $NAMESPACE -- pg_isready -U twisterlab 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database is accepting connections"
    } else {
        Write-Error "Database connectivity failed: $dbTest"
    }
    
    # Check resource usage
    Write-Info "Checking resource usage..."
    kubectl top pods -n $NAMESPACE 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Resource metrics available"
    } else {
        Write-Warning "Metrics server not available or not responding"
    }
    
    return ($healthyPods -eq $totalPods)
}

# Deploy Function
function Invoke-Deploy {
    Write-Info "Starting deployment to $Environment environment..."
    
    # Pre-deployment checks
    Write-Info "Running pre-deployment checks..."
    $healthStatus = Invoke-HealthCheck
    
    if (-not $healthStatus -and $Environment -eq "production") {
        Write-Warning "System is not fully healthy. Continue? (Y/N)"
        $response = Read-Host
        if ($response -ne "Y") {
            Write-Info "Deployment cancelled"
            return
        }
    }
    
    # Create backup before deployment
    Write-Info "Creating pre-deployment backup..."
    Invoke-Backup
    
    # Apply manifests
    Write-Info "Applying Kubernetes manifests..."
    kubectl apply -f k8s/base/ -n $NAMESPACE
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply base manifests"
        return
    }
    Write-Success "Base manifests applied"
    
    kubectl apply -f k8s/deployments/ -n $NAMESPACE
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to apply deployment manifests"
        return
    }
    Write-Success "Deployment manifests applied"
    
    # Wait for rollout
    Write-Info "Waiting for rollout to complete..."
    kubectl rollout status deployment/$API_DEPLOYMENT -n $NAMESPACE --timeout=5m
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Rollout failed or timed out"
        Write-Warning "Consider rolling back with: .\devops-toolkit.ps1 -Action rollback"
        return
    }
    Write-Success "Rollout completed successfully"
    
    # Post-deployment health check
    Write-Info "Running post-deployment health checks..."
    Start-Sleep -Seconds 10
    $postHealthStatus = Invoke-HealthCheck
    
    if ($postHealthStatus) {
        Write-Success "Deployment completed successfully!"
    } else {
        Write-Error "Post-deployment health check failed!"
        Write-Warning "Check logs with: .\devops-toolkit.ps1 -Action logs -Component api"
    }
}

# Backup Function
function Invoke-Backup {
    Write-Info "Creating database backup..."
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backup_${Environment}_${timestamp}.sql"
    
    # Create backup directory if not exists
    $backupDir = "backups"
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir | Out-Null
    }
    
    # Execute pg_dump
    Write-Info "Dumping database to $backupFile..."
    kubectl exec deployment/$POSTGRES_DEPLOYMENT -n $NAMESPACE -- pg_dump -U twisterlab twisterlab > "$backupDir\$backupFile"
    
    if ($LASTEXITCODE -eq 0) {
        $fileSize = (Get-Item "$backupDir\$backupFile").Length / 1MB
        Write-Success "Backup created successfully: $backupFile ($([math]::Round($fileSize, 2)) MB)"
        
        # Compress backup
        Write-Info "Compressing backup..."
        Compress-Archive -Path "$backupDir\$backupFile" -DestinationPath "$backupDir\$backupFile.zip" -Force
        Remove-Item "$backupDir\$backupFile"
        Write-Success "Backup compressed: $backupFile.zip"
        
        # Clean old backups (keep last 7 days)
        Write-Info "Cleaning old backups..."
        Get-ChildItem $backupDir -Filter "*.zip" | 
            Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | 
            Remove-Item -Force
        Write-Success "Old backups cleaned"
    } else {
        Write-Error "Backup failed!"
    }
}

# Scale Function
function Invoke-Scale {
    if (-not $Replicas) {
        Write-Error "Replicas parameter is required for scaling"
        return
    }
    
    $component = if ($Component) { $Component } else { "api" }
    $deployment = switch ($component) {
        "api" { $API_DEPLOYMENT }
        "mcp" { $MCP_DEPLOYMENT }
        default { $API_DEPLOYMENT }
    }
    
    Write-Info "Scaling $deployment to $Replicas replicas..."
    kubectl scale deployment/$deployment --replicas=$Replicas -n $NAMESPACE
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Scaling initiated"
        
        Write-Info "Waiting for pods to be ready..."
        kubectl wait --for=condition=ready pod -l app=$deployment -n $NAMESPACE --timeout=5m
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "All pods are ready"
        } else {
            Write-Warning "Some pods may not be ready yet"
        }
    } else {
        Write-Error "Scaling failed"
    }
}

# Logs Function
function Invoke-Logs {
    $component = if ($Component) { $Component } else { "api" }
    $deployment = switch ($component) {
        "api" { $API_DEPLOYMENT }
        "mcp" { $MCP_DEPLOYMENT }
        "postgres" { $POSTGRES_DEPLOYMENT }
        default { $API_DEPLOYMENT }
    }
    
    Write-Info "Fetching logs for $deployment (last $TailLines lines)..."
    kubectl logs deployment/$deployment -n $NAMESPACE --tail=$TailLines --follow=false
}

# Debug Function
function Invoke-Debug {
    Write-Info "Running diagnostics..."
    
    Write-Info "`n=== Pod Status ==="
    kubectl get pods -n $NAMESPACE -o wide
    
    Write-Info "`n=== Service Status ==="
    kubectl get svc -n $NAMESPACE
    
    Write-Info "`n=== Ingress Status ==="
    kubectl get ingress -n $NAMESPACE
    
    Write-Info "`n=== Recent Events ==="
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | Select-Object -Last 20
    
    Write-Info "`n=== Resource Usage ==="
    kubectl top pods -n $NAMESPACE 2>$null
    
    Write-Info "`n=== ConfigMaps ==="
    kubectl get configmap -n $NAMESPACE
    
    Write-Info "`n=== Secrets ==="
    kubectl get secrets -n $NAMESPACE
    
    Write-Info "`n=== Persistent Volumes ==="
    kubectl get pv,pvc -n $NAMESPACE
    
    # Database diagnostics
    Write-Info "`n=== Database Connections ==="
    kubectl exec deployment/$POSTGRES_DEPLOYMENT -n $NAMESPACE -- psql -U twisterlab -c "SELECT count(*) as connections, state FROM pg_stat_activity GROUP BY state;" 2>$null
    
    # API diagnostics
    Write-Info "`n=== API Health Check ==="
    try {
        $apiUrl = "http://edgeserver.twisterlab.local:30001/health"
        $response = Invoke-RestMethod -Uri $apiUrl -Method Get -TimeoutSec 10
        $response | ConvertTo-Json -Depth 3
    } catch {
        Write-Error "API unreachable: $_"
    }
}

# Rollback Function
function Invoke-Rollback {
    Write-Warning "Initiating rollback for $Environment environment..."
    Write-Warning "This will revert to the previous deployment. Continue? (Y/N)"
    $response = Read-Host
    if ($response -ne "Y") {
        Write-Info "Rollback cancelled"
        return
    }
    
    Write-Info "Rolling back API deployment..."
    kubectl rollout undo deployment/$API_DEPLOYMENT -n $NAMESPACE
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Rollback initiated"
        
        Write-Info "Waiting for rollback to complete..."
        kubectl rollout status deployment/$API_DEPLOYMENT -n $NAMESPACE --timeout=5m
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Rollback completed successfully"
            
            # Verify health
            Write-Info "Verifying system health..."
            Start-Sleep -Seconds 10
            Invoke-HealthCheck
        } else {
            Write-Error "Rollback failed or timed out"
        }
    } else {
        Write-Error "Rollback failed"
    }
}

# Security Scan Function
function Invoke-SecurityScan {
    Write-Info "Running security scans..."
    
    # Scan for secrets in codebase
    Write-Info "Scanning for exposed secrets..."
    if (Test-Path "scripts\scan_secrets.py") {
        python scripts\scan_secrets.py
        if ($LASTEXITCODE -eq 0) {
            Write-Success "No secrets found in codebase"
        } else {
            Write-Warning "Potential secrets detected - review output above"
        }
    } else {
        Write-Warning "Secret scanner not found"
    }
    
    # Check for vulnerable dependencies
    Write-Info "Checking for vulnerable dependencies..."
    pip-audit --require-hashes=false 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "No known vulnerabilities in dependencies"
    } else {
        Write-Warning "Vulnerabilities detected - review output above"
    }
    
    # Check Kubernetes security context
    Write-Info "Checking pod security contexts..."
    kubectl get pods -n $NAMESPACE -o json | ConvertFrom-Json | 
        ForEach-Object { 
            $_.items | ForEach-Object {
                $podName = $_.metadata.name
                $securityContext = $_.spec.securityContext
                if (-not $securityContext) {
                    Write-Warning "Pod $podName has no security context defined"
                } else {
                    Write-Success "Pod $podName has security context"
                }
            }
        }
    
    # Check for pods running as root
    Write-Info "Checking for pods running as root..."
    kubectl get pods -n $NAMESPACE -o json | ConvertFrom-Json | 
        ForEach-Object {
            $_.items | ForEach-Object {
                $podName = $_.metadata.name
                foreach ($container in $_.spec.containers) {
                    $runAsUser = $container.securityContext.runAsUser
                    if ($runAsUser -eq 0 -or $null -eq $runAsUser) {
                        Write-Warning "Pod $podName / Container $($container.name) may be running as root"
                    }
                }
            }
        }
}

# Main execution
Write-Info "TwisterLab DevOps Toolkit - Environment: $Environment"
Write-Info "=" * 60

switch ($Action) {
    "deploy" { Invoke-Deploy }
    "health" { Invoke-HealthCheck }
    "backup" { Invoke-Backup }
    "scale" { Invoke-Scale }
    "logs" { Invoke-Logs }
    "debug" { Invoke-Debug }
    "rollback" { Invoke-Rollback }
    "security" { Invoke-SecurityScan }
    default { Write-Error "Unknown action: $Action" }
}

Write-Info "=" * 60
Write-Info "Operation completed at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
