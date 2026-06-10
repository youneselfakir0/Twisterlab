#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy agent fixes to EdgeServer and rebuild Docker image.
    
.DESCRIPTION
    Copies fixed Python files to EdgeServer, rebuilds the mcp-unified image,
    pushes to Harbor registry, and rolls out the deployment.
    
.USAGE
    .\scripts\deploy-fix-agents.ps1
#>

$EDGESERVER = "192.168.0.30"
$SSH_USER = "younes"  # Change if needed
$REMOTE_REPO = "/opt/twisterlab"  # Change to your repo path on EdgeServer
$HARBOR = "192.168.0.30:8090"
$IMAGE = "library/mcp-unified"
$NEW_TAG = "v3.9-fix-agents"

Write-Host "=== TwisterLab Agent Fix Deployment ===" -ForegroundColor Cyan
Write-Host "Target: $EDGESERVER | Image: $IMAGE`:$NEW_TAG"
Write-Host ""

# Files to sync
$FILES = @(
    "src/twisterlab/agents/real/real_desktop_commander_agent.py",
    "src/twisterlab/agents/real/real_monitoring_agent.py"
)

# Step 1: Copy fixed files to EdgeServer
Write-Host "[1/4] Copying fixed files to EdgeServer..." -ForegroundColor Yellow
foreach ($file in $FILES) {
    $remotePath = "$SSH_USER`@$EDGESERVER`:$REMOTE_REPO/$file"
    Write-Host "  -> $file"
    & scp $file $remotePath
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to copy $file"
        exit 1
    }
}
Write-Host "  Files copied!" -ForegroundColor Green

# Step 2: Build new image on EdgeServer
Write-Host ""
Write-Host "[2/4] Building Docker image on EdgeServer..." -ForegroundColor Yellow
& ssh "$SSH_USER`@$EDGESERVER" @"
    cd $REMOTE_REPO
    docker build -t $HARBOR/$IMAGE`:$NEW_TAG .
    if [ `$? -ne 0 ]; then echo 'BUILD FAILED'; exit 1; fi
    echo 'Build complete!'
"@

if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker build failed on EdgeServer"
    exit 1
}

# Step 3: Push to Harbor
Write-Host ""
Write-Host "[3/4] Pushing to Harbor registry..." -ForegroundColor Yellow
& ssh "$SSH_USER`@$EDGESERVER" @"
    docker push $HARBOR/$IMAGE`:$NEW_TAG
    docker tag $HARBOR/$IMAGE`:$NEW_TAG $HARBOR/$IMAGE`:latest
    docker push $HARBOR/$IMAGE`:latest
"@

if ($LASTEXITCODE -ne 0) {
    Write-Error "Push to Harbor failed"
    exit 1
}
Write-Host "  Image pushed!" -ForegroundColor Green

# Step 4: Update K8s deployment
Write-Host ""
Write-Host "[4/4] Rolling out new deployment..." -ForegroundColor Yellow
kubectl set image deployment/mcp-unified mcp-unified="$HARBOR/$IMAGE`:$NEW_TAG" -n twisterlab
kubectl rollout status deployment/mcp-unified -n twisterlab --timeout=120s

Write-Host ""
Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
Write-Host "Image: $HARBOR/$IMAGE`:$NEW_TAG"
Write-Host "Test: Invoke-RestMethod http://192.168.0.30:30393/tools/maestro_orchestrate ..."
