#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Claude Code + Gemma4 One-Shot Launcher
    
.DESCRIPTION
    Lance Claude Code avec gemma4:latest, teste toutes les dépendances,
    et offre un fallback sur qwen2.5-coder ou deepseek-r1 si besoin.
    
.EXAMPLE
    pwsh -ExecutionPolicy Bypass -File GEMMA4_LAUNCH.ps1
#>

param(
    [string]$Model = "gemma4:latest",
    [switch]$WithMCP,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"

# ============================================
# COULEURS
# ============================================
$Green = @{ ForegroundColor = 'Green' }
$Yellow = @{ ForegroundColor = 'Yellow' }
$Red = @{ ForegroundColor = 'Red' }

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════╗" @Green
Write-Host "║  Claude Code + Gemma4 Launcher                   ║" @Green
Write-Host "║  (Configuration 24-06-2026)                      ║" @Green
Write-Host "╚═══════════════════════════════════════════════════╝" @Green
Write-Host ""

# ============================================
# 1. VÉRIFIER OLLAMA
# ============================================
Write-Host "[1/4] Vérification d'Ollama..." -ForegroundColor Cyan

try {
    $response = curl -s -w "%{http_code}" http://localhost:11434/api/tags 2>$null
    if ($LASTEXITCODE -eq 0 -and $response -like "*200*") {
        Write-Host "✅ Ollama est accessible sur localhost:11434" @Green
    } else {
        Write-Host "❌ Ollama ne répond pas" @Red
        Write-Host "   Lance dans un terminal séparé: ollama serve" @Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Erreur: Ollama indisponible" @Red
    Write-Host "   Lance dans un terminal séparé: ollama serve" @Yellow
    exit 1
}

# ============================================
# 2. DÉTECTER LES MODÈLES
# ============================================
Write-Host ""
Write-Host "[2/4] Détection des modèles Ollama..." -ForegroundColor Cyan

$models = @()
try {
    $output = curl -s http://localhost:11434/api/tags 2>$null | Select-String "gemma4|qwen2.5-coder|deepseek-r1" -AllMatches
    if ($output) {
        Write-Host "✅ Modèles trouvés:" @Green
        Write-Host $output
    }
} catch {
    Write-Host "⚠️  Impossible de vérifier les modèles" @Yellow
}

# ============================================
# 3. VÉRIFIER LE MODÈLE SÉLECTIONNÉ
# ============================================
Write-Host ""
Write-Host "[3/4] Vérification du modèle: $Model" -ForegroundColor Cyan

$modelFound = $false
foreach ($line in (curl -s http://localhost:11434/api/tags 2>$null | Select-String -Pattern $Model)) {
    if ($line -match $Model) {
        Write-Host "✅ $Model est disponible" @Green
        $modelFound = $true
        break
    }
}

if (-not $modelFound) {
    Write-Host "⚠️  $Model non trouvé" @Yellow
    Write-Host "   Essais avec les alternatives..." @Yellow
    
    # Fallback sur gemma4
    if ($Model -ne "gemma4:latest") {
        $Model = "gemma4:latest"
        Write-Host "   → Basculé sur $Model" @Green
    }
}

# ============================================
# 4. VÉRIFIER LOCLAUDE
# ============================================
Write-Host ""
Write-Host "[4/4] Vérification de loclaude..." -ForegroundColor Cyan

try {
    $version = loclaude --version 2>$null
    if ($version) {
        Write-Host "✅ $version" @Green
    } else {
        throw "loclaude not found"
    }
} catch {
    Write-Host "❌ loclaude n'est pas installé" @Red
    Write-Host "   Install: npm install -g loclaude" @Yellow
    exit 1
}

# ============================================
# RÉSUMÉ
# ============================================
Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════╗" @Green
Write-Host "║  Configuration Prête                             ║" @Green
Write-Host "╚═══════════════════════════════════════════════════╝" @Green
Write-Host ""
Write-Host "  Modèle        : $Model" @Green
Write-Host "  Ollama        : http://localhost:11434" @Green
Write-Host "  Répertoire    : $PSScriptRoot" @Green

if ($WithMCP) {
    Write-Host "  MCP Server    : http://192.168.0.30:30393/mcp" @Green
}

Write-Host ""
Write-Host "Lancement de Claude Code en 3 secondes..." @Yellow
Start-Sleep -Seconds 3

# ============================================
# LANCER LOCLAUDE
# ============================================
$cmd = "loclaude start --model $Model"

if ($WithMCP) {
    $cmd += " --mcp-server twisterlab http://192.168.0.30:30393/mcp"
}

$cmd += " --directory `"$PSScriptRoot`""

if ($Verbose) {
    Write-Host ""
    Write-Host "Commande d'exécution:" @Cyan
    Write-Host $cmd @Yellow
    Write-Host ""
}

Invoke-Expression $cmd

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ loclaude a échoué" @Red
    exit 1
}

Write-Host ""
Write-Host "✅ Claude Code fermé" @Green
