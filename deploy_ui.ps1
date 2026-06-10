# ============================================================
# TwisterLab React UI - Build & Deploy Script
# Uses existing SSH key: Host twisterlab-ubuntu (192.168.0.30)
# ============================================================

$SSHHost = "twisterlab-ubuntu"
$ImageName = "twisterlab/ui-react:latest"
$tarName = "twisterlab-ui-react.tar"

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TwisterLab React UI - Build & Deploy to EdgeServer"         -ForegroundColor Cyan
Write-Host "  SSH Host : $SSHHost"                                      -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# --- STEP 1: Build Docker Image Locally ---
Write-Host "`n[STEP 1/5] Building React UI Docker image locally..." -ForegroundColor Yellow
Set-Location (Join-Path $PSScriptRoot "frontend")
docker build -t $ImageName -f Dockerfile .
Set-Location $PSScriptRoot
Write-Host "  OK: React UI Docker image compiled successfully." -ForegroundColor Green

# --- STEP 2: Save Image to Tar ---
Write-Host "`n[STEP 2/5] Saving image to local tar archive..." -ForegroundColor Yellow
$tarPath = Join-Path $PSScriptRoot $tarName
docker save $ImageName -o $tarPath
$sizeMB = [Math]::Round((Get-Item $tarPath).Length / 1MB)
Write-Host "  OK: $sizeMB MB saved -> $tarPath" -ForegroundColor Green

# --- STEP 3: Transfer Tar to EdgeServer ---
Write-Host "`n[STEP 3/5] Copying tar to EdgeServer via SCP..." -ForegroundColor Yellow
scp $tarPath "${SSHHost}:/tmp/$tarName"
Write-Host "  OK: Transferred to ${SSHHost}:/tmp/" -ForegroundColor Green

# --- STEP 4: Import Image into k3s Containerd ---
Write-Host "`n[STEP 4/5] Importing image into k3s containerd..." -ForegroundColor Yellow
ssh $SSHHost "sudo k3s ctr images import /tmp/$tarName && echo '--- Available twisterlab images ---' && sudo k3s ctr images list | grep ui-react && rm -f /tmp/$tarName"
Write-Host "  OK: Image imported into containerd on EdgeServer" -ForegroundColor Green

# --- STEP 5: Force rolling restart of the UI Deployment ---
Write-Host "`n[STEP 5/5] Performing rolling restart of twisterlab-ui-react..." -ForegroundColor Yellow
kubectl rollout restart deployment/twisterlab-ui-react -n twisterlab
kubectl rollout status deployment/twisterlab-ui-react -n twisterlab --timeout=120s

# Cleanup local tar
Remove-Item $tarPath -ErrorAction SilentlyContinue

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  TwisterLab React UI DEPLOYED SUCCESSFULLY!"                  -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
