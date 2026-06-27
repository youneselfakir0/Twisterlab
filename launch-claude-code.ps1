#!/usr/bin/env pwsh

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Claude Code + TwisterLab (via Ollama Launch - Official)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Check Ollama is running
$proc = Get-Process ollama -ErrorAction SilentlyContinue
if (-not $proc) {
    Write-Host "ERROR: Ollama is not running" -ForegroundColor Red
    Write-Host "Launch in separate terminal: ollama serve" -ForegroundColor Yellow
    exit 1
}

Write-Host "Model       : gemma4:latest" -ForegroundColor Green
Write-Host "Repository  : $(Get-Location)" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Claude Code via Ollama Launch..." -ForegroundColor Yellow
Write-Host ""

# Change to TwisterLab directory
Set-Location -Path "C:\Users\Administrator\Documents\twisterlab"

# Launch Claude Code via Ollama native integration
& ollama launch claude --model gemma4:latest

Write-Host ""
Write-Host "Claude Code closed" -ForegroundColor Green
