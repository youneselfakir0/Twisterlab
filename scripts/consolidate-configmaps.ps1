#!/usr/bin/env pwsh
# ============================================================
# Script de migration : Consolidation des ConfigMaps hotfix
# TwisterLab -- 2026-02-21
# ============================================================
# Usage : .\scripts\consolidate-configmaps.ps1
# ============================================================

$Namespace = "twisterlab"
$NewCMName = "twisterlab-patches-v1"
$OutputFile = "k8s\base\configmap-patches-consolidated.yaml"

$HotfixCMs = @(
    "agent-classifier-hotfix",
    "agent-resolver-hotfix",
    "api-hotfix-v1",
    "browser-agent-fix",
    "desktop-commander-fix",
    "maestro-fix",
    "mcp-unified-fixes",
    "registry-fix"
)

Write-Host ""
Write-Host "TwisterLab -- Consolidation des ConfigMaps hotfix" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# ── Etape 1 : Extraction du contenu live ─────────────────────────────────────
Write-Host "Etape 1/4 -- Extraction du contenu live..." -ForegroundColor Yellow

$allData = @{}
$sourceMap = @{}   # cle -> nom de la CM source

foreach ($cm in $HotfixCMs) {
    Write-Host "  -> Lecture : $cm" -ForegroundColor Gray
    try {
        $raw = kubectl get configmap $cm -n $Namespace -o json 2>&1 | ConvertFrom-Json
        if ($raw.data) {
            $raw.data.PSObject.Properties | ForEach-Object {
                $key = $_.Name
                $val = $_.Value
                if ($allData.ContainsKey($key)) {
                    Write-Host "    [!] Cle dupliquee : '$key' (depuis $cm)" -ForegroundColor Yellow
                    $key = "${cm}__${key}"
                }
                $allData[$key] = $val
                $sourceMap[$key] = $cm
            }
        }
        else {
            Write-Host "    [i] $cm : aucune donnee (data vide)" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "    [X] Impossible de lire ${cm} : $_" -ForegroundColor Red
    }
}

Write-Host "  OK -- $($allData.Count) cles extraites au total" -ForegroundColor Green

# ── Etape 2 : Generation du YAML consolide ───────────────────────────────────
Write-Host ""
Write-Host "Etape 2/4 -- Generation du YAML consolide..." -ForegroundColor Yellow

$date = Get-Date -Format 'yyyy-MM-dd HH:mm'
$replaces = $HotfixCMs -join ', '

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add("# Auto-genere par consolidate-configmaps.ps1 -- $date")
$lines.Add("# Remplace : $replaces")
$lines.Add("apiVersion: v1")
$lines.Add("kind: ConfigMap")
$lines.Add("metadata:")
$lines.Add("  name: $NewCMName")
$lines.Add("  namespace: $Namespace")
$lines.Add("  labels:")
$lines.Add("    app: twisterlab")
$lines.Add("    component: patches")
$lines.Add("    version: '1.0'")
$lines.Add("  annotations:")
$lines.Add("    consolidated-date: '$(Get-Date -Format 'yyyy-MM-dd')'")
$lines.Add("    replaces: '$replaces'")
$lines.Add("data:")

foreach ($key in ($allData.Keys | Sort-Object)) {
    $src = $sourceMap[$key]
    $lines.Add("  # Source: $src")
    $lines.Add("  ${key}: |")
    $valLines = $allData[$key] -split "`r?`n"
    foreach ($vl in $valLines) {
        $lines.Add("    $vl")
    }
    $lines.Add("")
}

$lines | Out-File -FilePath $OutputFile -Encoding utf8
Write-Host "  OK -- YAML ecrit dans : $OutputFile" -ForegroundColor Green

# ── Etape 3 : Application dans K8s ───────────────────────────────────────────
Write-Host ""
Write-Host "Etape 3/4 -- Application dans Kubernetes..." -ForegroundColor Yellow

kubectl apply -f $OutputFile
if ($LASTEXITCODE -eq 0) {
    Write-Host "  OK -- ConfigMap '$NewCMName' appliquee avec succes" -ForegroundColor Green
}
else {
    Write-Host "  [X] Erreur lors de l'application. Abandon." -ForegroundColor Red
    Write-Host "      Les anciennes ConfigMaps sont conservees." -ForegroundColor Red
    exit 1
}

# ── Etape 4 : Suppression des anciennes ConfigMaps ───────────────────────────
Write-Host ""
Write-Host "Etape 4/4 -- Suppression des anciennes ConfigMaps..." -ForegroundColor Yellow

$confirm = Read-Host "  Confirmer la suppression des $($HotfixCMs.Count) ConfigMaps hotfix ? (oui/non)"
if ($confirm -ne "oui") {
    Write-Host "  Suppression annulee -- les anciennes ConfigMaps sont conservees." -ForegroundColor Yellow
    exit 0
}

foreach ($cm in $HotfixCMs) {
    kubectl delete configmap $cm -n $Namespace 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Supprime : $cm" -ForegroundColor Green
    }
    else {
        Write-Host "  [!]  Impossible de supprimer $cm (deja absent ?)" -ForegroundColor Yellow
    }
}

# ── Resume ────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Migration terminee !" -ForegroundColor Green
Write-Host ""
Write-Host "  ConfigMap creee      : $NewCMName" -ForegroundColor White
Write-Host "  Cles migrees         : $($allData.Count)" -ForegroundColor White
Write-Host "  ConfigMaps supprimees: $($HotfixCMs.Count)" -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT : Mettez a jour les deployments qui montaient" -ForegroundColor Yellow
Write-Host "les anciennes ConfigMaps pour referencer '$NewCMName'" -ForegroundColor Yellow
Write-Host ""
