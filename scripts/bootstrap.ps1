# TwisterLab Remote Bootstrapper (Windows)
# This script clones TwisterLab and launches the local installer.
# Usage: irm https://<host>/bootstrap.ps1 | iex

$ErrorActionPreference = "Stop"

$repoUrl = "https://github.com/youneselfakir0/Twisterlab.git"
$installDir = Join-Path $HOME "twisterlab"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "*         TwisterLab Remote Installer Bootstrapper       *" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Check for Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Git is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Git (https://git-scm.com/) and try again." -ForegroundColor Yellow
    exit 1
}

# Clone or Update Repo
if (-not (Test-Path $installDir)) {
    Write-Host "Step 1: Cloning repository to $installDir..." -ForegroundColor Yellow
    git clone $repoUrl $installDir
} else {
    Write-Host "Step 1: Repository already exists at $installDir. Updating..." -ForegroundColor Yellow
    Push-Location $installDir
    git pull
    Pop-Location
}

# Run the local installer
Write-Host "Step 2: Launching local installation script..." -ForegroundColor Yellow
Push-Location $installDir
if (Test-Path "install.ps1") {
    .\install.ps1
} else {
    Write-Host "[ERROR] install.ps1 not found in the cloned repository." -ForegroundColor Red
    exit 1
}
Pop-Location

Write-Host ""
Write-Host "Done! You can now use TwisterLab." -ForegroundColor Green
