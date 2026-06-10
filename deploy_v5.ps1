# ============================================================
# TwisterLab API v5.0 - Transfer & Deploy Script
# Uses existing SSH key: Host twisterlab-ubuntu (192.168.0.30)
# User: twister | No password needed - key auth configured
# ============================================================

param(
    [string]$SSHHost    = "twisterlab-ubuntu",  # Alias from ~/.ssh/config
    [string]$ImageLocal = "localhost:5000/twisterlab-api:v5.0.9",
    [string]$ImageRemote = "localhost:5000/twisterlab-api:v5.0.9"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TwisterLab API v5.0 - Transfer & Deploy to EdgeServer"    -ForegroundColor Cyan
Write-Host "  SSH Host : $SSHHost (key auth)"                           -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# --- STEP 1: Save image to tar ---
Write-Host "`n[STEP 1/5] Saving Docker image to tar..." -ForegroundColor Yellow
$tarPath = Join-Path $PSScriptRoot "twisterlab-api-v5.tar"
docker save $ImageLocal -o $tarPath
$sizeMB = [Math]::Round((Get-Item $tarPath).Length / 1MB)
Write-Host "  OK: $sizeMB MB saved -> $tarPath" -ForegroundColor Green

# --- STEP 2: Copy tar to EdgeServer ---
Write-Host "`n[STEP 2/5] Copying tar to EdgeServer via SCP..." -ForegroundColor Yellow
scp $tarPath "${SSHHost}:/tmp/twisterlab-api-v5.tar"
Write-Host "  OK: Transferred to ${SSHHost}:/tmp/" -ForegroundColor Green

# --- STEP 3: Import image into k3s containerd ---
Write-Host "`n[STEP 3/5] Importing image into k3s containerd..." -ForegroundColor Yellow
ssh $SSHHost "sudo k3s ctr images import /tmp/twisterlab-api-v5.tar && echo '--- Available twisterlab images ---' && sudo k3s ctr images list | grep twisterlab && rm -f /tmp/twisterlab-api-v5.tar"
Write-Host "  OK: Image imported into k3s" -ForegroundColor Green

# --- STEP 4: Update Kubernetes deployment ---
Write-Host "`n[STEP 4/5] Updating Kubernetes deployment to $ImageRemote..." -ForegroundColor Yellow

kubectl set image deployment/twisterlab "twisterlab=$ImageRemote" -n twisterlab

# Patch to remove all ConfigMap volume mounts - only keep archive PVC
$patchFile = Join-Path $PSScriptRoot "deployment_patch_v5.json"
@{
    spec = @{
        template = @{
            metadata = @{
                annotations = @{
                    "twisterlab/build"  = "v5.0.9"
                    "twisterlab/hotfix" = "none"
                    "kubectl.kubernetes.io/restartedAt" = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
                }
            }
            spec = @{
                volumes = @(
                    @{ name = "archives"; persistentVolumeClaim = @{ claimName = "twisterlab-archive-pvc" } }
                )
                containers = @(
                    @{
                        name         = "twisterlab"
                        image        = $ImageRemote
                        volumeMounts = @(
                            @{ name = "archives"; mountPath = "/app/archives" }
                        )
                        resources    = @{
                            requests = @{ cpu = "500m";  memory = "512Mi" }
                            limits   = @{ cpu = "2000m"; memory = "1024Mi" }
                        }
                    }
                )
            }
        }
    }
} | ConvertTo-Json -Depth 10 | Out-File -FilePath $patchFile -Encoding utf8

kubectl patch deployment twisterlab -n twisterlab --type merge --patch-file $patchFile
Write-Host "  OK: Deployment patched - ConfigMap overrides removed" -ForegroundColor Green

Write-Host "`n  Waiting for rollout..." -ForegroundColor Yellow
kubectl rollout status deployment/twisterlab -n twisterlab --timeout=120s

# --- STEP 5: Cleanup hotfix ConfigMaps ---
Write-Host "`n[STEP 5/5] Retiring legacy hotfix ConfigMaps..." -ForegroundColor Yellow
@(
    "ui-hotfix-v382", "api-hotfix-v1", "api-hotfix-v3",
    "db-hotfix-v1", "hotfix-services-trading", "hotfix-utils-trading",
    "trading-hotfix-v2", "utils-hotfix-v2"
) | ForEach-Object {
    kubectl delete configmap $_ -n twisterlab --ignore-not-found
    Write-Host "  Deleted: $_" -ForegroundColor Gray
}

# Cleanup local tar
Remove-Item $tarPath -ErrorAction SilentlyContinue

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  TwisterLab API v5.0 DEPLOYED SUCCESSFULLY"                 -ForegroundColor Green
Write-Host "  Image      : $ImageRemote"                                  -ForegroundColor Green
Write-Host "  ConfigMaps : All hotfixes retired"                          -ForegroundColor Green
Write-Host "  Source     : Fully consolidated in image"                   -ForegroundColor Green
Write-Host "  Resources  : cpu req=500m lim=2000m | mem req=512Mi lim=1024Mi" -ForegroundColor Green
Write-Host "  HPA        : Autoscaler targets restored"                   -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

Write-Host "`n[HEALTH CHECK]" -ForegroundColor Yellow
Start-Sleep -Seconds 8
kubectl get pods -n twisterlab -l app=twisterlab,component=api
Write-Host ""
kubectl get configmaps -n twisterlab
