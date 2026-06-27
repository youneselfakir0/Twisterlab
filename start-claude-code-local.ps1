#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Claude Code + Gemma4 Launcher - Simplified Version
    Uses 'ollama list' for model detection (more reliable)
#>

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Claude Code + Gemma4 - Diagnostic and Launch" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# ============================================
# 1. VERIFY OLLAMA IS RUNNING
# ============================================
Write-Host "[1/3] Checking Ollama..." -ForegroundColor Cyan

$proc = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $proc) {
    Write-Host "[ERROR] Ollama is not running" -ForegroundColor Red
    Write-Host "Launch in separate terminal:" -ForegroundColor Yellow
    Write-Host "  ollama serve" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
Write-Host "[OK] Ollama is running (PID $($proc.Id))" -ForegroundColor Green

# ============================================
# 2. GET AVAILABLE MODELS
# ============================================
Write-Host ""
Write-Host "[2/3] Selecting model..." -ForegroundColor Cyan

# Use 'ollama list' command (more reliable than API)
$models_output = ollama list 2>$null
$model_lines = $models_output | Select-String -Pattern "^[a-zA-Z]" | Where-Object { $_ -notmatch "^NAME" } | ForEach-Object { $_.Line.Split()[0] }

if (-not $model_lines) {
    Write-Host "[ERROR] Could not read models from ollama list" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Available models:" -ForegroundColor Green
$model_lines | Where-Object { $_ } | ForEach-Object { Write-Host "     - $_" -ForegroundColor Green }

# ============================================
# 3. SELECT BEST MODEL (PRIORITY ORDER)
# ============================================
$model = $null

# Priority 1: gemma4:latest
if ($model_lines -contains "gemma4:latest") {
    $model = "gemma4:latest"
    Write-Host ""
    Write-Host "[OK] Using gemma4:latest" -ForegroundColor Green
}
# Priority 2: qwen2.5-coder:7b
elseif ($model_lines -contains "qwen2.5-coder:7b") {
    $model = "qwen2.5-coder:7b"
    Write-Host ""
    Write-Host "[WARN] gemma4 not found, using qwen2.5-coder:7b" -ForegroundColor Yellow
}
# Priority 3: qwen2.5-coder:latest
elseif ($model_lines -contains "qwen2.5-coder:latest") {
    $model = "qwen2.5-coder:latest"
    Write-Host ""
    Write-Host "[WARN] gemma4 not found, using qwen2.5-coder:latest" -ForegroundColor Yellow
}
# Priority 4: deepseek-r1:latest
elseif ($model_lines -contains "deepseek-r1:latest") {
    $model = "deepseek-r1:latest"
    Write-Host ""
    Write-Host "[WARN] Using deepseek-r1:latest" -ForegroundColor Yellow
}
# Fallback: First available model
else {
    $model = $model_lines[0]
    Write-Host ""
    Write-Host "[WARN] Using first available model: $model" -ForegroundColor Yellow
}

if (-not $model) {
    Write-Host "[ERROR] No models available" -ForegroundColor Red
    exit 1
}

# ============================================
# 4. CHECK LOCLAUDE
# ============================================
Write-Host ""
Write-Host "[3/3] Checking loclaude..." -ForegroundColor Cyan

$loclaude_version = loclaude --version 2>$null
if (-not $loclaude_version) {
    Write-Host "[ERROR] loclaude not installed" -ForegroundColor Red
    Write-Host "Install with: npm install -g loclaude" -ForegroundColor Yellow
    exit 1
}
Write-Host "[OK] $loclaude_version" -ForegroundColor Green

# ============================================
# 5. SUMMARY & LAUNCH
# ============================================
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Configuration Ready" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Model          : $model" -ForegroundColor Green
Write-Host "  Ollama         : http://localhost:11434" -ForegroundColor Green
Write-Host "  Directory      : $PSScriptRoot" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Claude Code..." -ForegroundColor Yellow
Write-Host ""

# Build command
$dir = $PSScriptRoot
$cmd = "loclaude start --model $model --mcp-server twisterlab http://192.168.0.30:30393/mcp --directory `"$dir`""

# Execute
Invoke-Expression $cmd

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] loclaude failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Claude Code closed" -ForegroundColor Green
