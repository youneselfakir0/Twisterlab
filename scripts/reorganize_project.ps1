# =============================================================================
# TwisterLab - Script de Reorganisation du Projet
# =============================================================================
# Ce script reorganise les fichiers selon la structure cible definie :
#   deploy/k8s/     -> Manifestes YAML/JSON Kubernetes
#   deploy/scripts/ -> Scripts de build et correction
#   scripts/        -> Outils utilitaires et diagnostics
#   integrations/   -> Workflows n8n et integrations externes
#   src/twisterlab/ui/ -> Interface utilisateur
#   logs/           -> Dumps K8s et fichiers de logs
#   data/           -> Fichiers de donnees JSON
#   external/       -> Projets externes (seminaire, etc.)
#   archives/       -> Anciennes versions compressees
# =============================================================================

$ROOT = "c:\Users\Administrator\Documents\twisterlab"
$Errors = @()
$Moved = @()

function Move-SafeItem {
    param($Source, $Dest)
    if (Test-Path $Source) {
        $destDir = Split-Path $Dest -Parent
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        if (Test-Path $Dest) {
            Write-Host "  [SKIP] Deja present: $(Split-Path $Dest -Leaf)" -ForegroundColor DarkGray
        } else {
            try {
                Move-Item -Path $Source -Destination $Dest -Force
                $script:Moved += "$(Split-Path $Source -Leaf) -> $(Split-Path $Dest -Parent -Resolve)"
                Write-Host "  [OK]   $(Split-Path $Source -Leaf)" -ForegroundColor Green
            } catch {
                $script:Errors += "ERREUR: $Source -> $_.Exception.Message"
                Write-Host "  [ERR]  $(Split-Path $Source -Leaf): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "  [N/A]  Source introuvable: $Source" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " TwisterLab - Reorganisation du Projet" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# =============================================================================
# ETAPE 1 : Deplacer les archives .tar.gz de deploy/ vers archives/
# =============================================================================
Write-Host "[1/5] Archives de deploy/ -> archives/" -ForegroundColor Yellow

$archivesDir = Join-Path $ROOT "archives"
if (-not (Test-Path $archivesDir)) {
    New-Item -ItemType Directory -Path $archivesDir -Force | Out-Null
}

$deployArchives = Get-ChildItem -Path (Join-Path $ROOT "deploy") -Filter "*.tar.gz"
foreach ($archive in $deployArchives) {
    Move-SafeItem -Source $archive.FullName -Dest (Join-Path $archivesDir $archive.Name)
}

# Aussi deplacer le fichier .zip de deploy/ si present
$deployZips = Get-ChildItem -Path (Join-Path $ROOT "deploy") -Filter "*.zip"
foreach ($zip in $deployZips) {
    Move-SafeItem -Source $zip.FullName -Dest (Join-Path $archivesDir $zip.Name)
}

# =============================================================================
# ETAPE 2 : Deplacer les gros fichiers logs de la racine vers logs/
# =============================================================================
Write-Host ""
Write-Host "[2/5] Fichiers logs racine -> logs/" -ForegroundColor Yellow

$logsDir = Join-Path $ROOT "logs"
$rootLogFiles = @(
    "proxy.log",
    "server_debug.log",
    "server_error.log",
    "disk_check.log",
    "mcp_paramiko.log",
    "mcp_proxy_debug.log",
    "err.log"
)
foreach ($logFile in $rootLogFiles) {
    Move-SafeItem -Source (Join-Path $ROOT $logFile) -Dest (Join-Path $logsDir $logFile)
}

# =============================================================================
# ETAPE 3 : Verifier que deploy/k8s contient bien les manifestes
# =============================================================================
Write-Host ""
Write-Host "[3/5] Verification deploy/k8s/ (manifestes YAML/JSON)" -ForegroundColor Yellow

$k8sDir = Join-Path $ROOT "deploy\k8s"
$k8sCount = (Get-ChildItem -Path $k8sDir -Include "*.yaml","*.json" -Recurse).Count
Write-Host "  [OK]  $k8sCount fichiers YAML/JSON trouves dans deploy/k8s/" -ForegroundColor Green

# =============================================================================
# ETAPE 4 : Verifier que deploy/scripts contient bien les scripts build/fix
# =============================================================================
Write-Host ""
Write-Host "[4/5] Verification deploy/scripts/ (scripts build & fix)" -ForegroundColor Yellow

$deployScriptsDir = Join-Path $ROOT "deploy\scripts"
$deployScriptsCount = (Get-ChildItem -Path $deployScriptsDir -Include "*.py","*.ps1","*.sh" -Recurse).Count
Write-Host "  [OK]  $deployScriptsCount scripts trouves dans deploy/scripts/" -ForegroundColor Green

# =============================================================================
# ETAPE 5 : Rapport final
# =============================================================================
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " RAPPORT FINAL" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Fichiers deplaces : $($Moved.Count)" -ForegroundColor Green
foreach ($m in $Moved) {
    Write-Host "  -> $m" -ForegroundColor DarkGreen
}

if ($Errors.Count -gt 0) {
    Write-Host ""
    Write-Host "Erreurs : $($Errors.Count)" -ForegroundColor Red
    foreach ($e in $Errors) {
        Write-Host "  $e" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "Aucune erreur detectee." -ForegroundColor Green
}

# Afficher l'etat final de la racine
Write-Host ""
Write-Host "--- Etat de la racine apres reorganisation ---" -ForegroundColor Yellow
$rootItems = Get-ChildItem -Path $ROOT | Where-Object { !$_.PSIsContainer }
Write-Host "  Fichiers a la racine : $($rootItems.Count)" -ForegroundColor Cyan
$rootItems | Select-Object Name | ForEach-Object { Write-Host "    $($_.Name)" -ForegroundColor DarkCyan }

Write-Host ""
Write-Host "Reorganisation terminee." -ForegroundColor Cyan
