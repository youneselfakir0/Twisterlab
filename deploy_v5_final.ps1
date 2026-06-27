
# ============================================================
# TwisterLab Mission Control v5 - FINAL SENIOR PATCH DEPLOY
# This script builds and deploys BOTH UI and API to EdgeServer
# Version: v5.0.10 (Odysseus Senior Patch)
# ============================================================

$SSHHost = "twisterlab-ubuntu"
$Version = "v5.0.12"
$ApiImage = "twisterlab-api:$Version"
$UiImage = "twisterlab-ui-react:$Version"

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  🚀 DEPLOYING SENIOR PATCH v5.0.10"                         -ForegroundColor Cyan
Write-Host "  SSH Host : $SSHHost"                                      -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# --- STEP 1: Build API ---
Write-Host "`n[1/6] Building API Docker image ($ApiImage)..." -ForegroundColor Yellow
docker build -t $ApiImage -f Dockerfile.api .
Write-Host "  OK: API image built." -ForegroundColor Green

# --- STEP 2: Build UI (NO CACHE) ---
Write-Host "`n[2/6] Building UI Docker image ($UiImage) - CLEAN BUILD..." -ForegroundColor Yellow
Set-Location frontend
docker build --no-cache -t $UiImage -f Dockerfile .
Set-Location ..
Write-Host "  OK: UI image built." -ForegroundColor Green

# --- STEP 3: Transfer API ---
Write-Host "`n[3/6] Transferring API image..." -ForegroundColor Yellow
$apiTar = "api_patch.tar"
docker save $ApiImage -o $apiTar
scp -o BatchMode=yes $apiTar "${SSHHost}:/tmp/$apiTar"
ssh -o BatchMode=yes $SSHHost "sudo k3s ctr images import /tmp/$apiTar && rm -f /tmp/$apiTar"
Remove-Item $apiTar
Write-Host "  OK: API transferred and imported." -ForegroundColor Green

# --- STEP 4: Transfer UI ---
Write-Host "`n[4/6] Transferring UI image..." -ForegroundColor Yellow
$uiTar = "ui_patch.tar"
docker save $UiImage -o $uiTar
scp -o BatchMode=yes $uiTar "${SSHHost}:/tmp/$uiTar"
ssh -o BatchMode=yes $SSHHost "sudo k3s ctr images import /tmp/$uiTar && rm -f /tmp/$uiTar"
Remove-Item $uiTar
Write-Host "  OK: UI transferred and imported." -ForegroundColor Green

# --- STEP 5: Update Kubernetes ---
Write-Host "`n[5/6] Updating Kubernetes Deployments..." -ForegroundColor Yellow
kubectl set image deployment/twisterlab "twisterlab=$ApiImage" -n twisterlab
kubectl set image deployment/twisterlab-ui-react "twisterlab-ui-react=$UiImage" -n twisterlab

Write-Host "  Waiting for Rollout (API)..." -ForegroundColor Gray
kubectl rollout status deployment/twisterlab -n twisterlab --timeout=120s
Write-Host "  Waiting for Rollout (UI)..." -ForegroundColor Gray
kubectl rollout status deployment/twisterlab-ui-react -n twisterlab --timeout=120s

# --- STEP 6: Final Verification ---
Write-Host "`n[6/6] Verifying Deployment Status..." -ForegroundColor Yellow
ssh -o BatchMode=yes $SSHHost "sudo k3s ctr images list | grep $Version"
kubectl get pods -n twisterlab

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  ✅ DEPLOYMENT v5.0.10 COMPLETE"                            -ForegroundColor Green
Write-Host "  Dashboard: http://centre.twisterlab.local/"               -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
