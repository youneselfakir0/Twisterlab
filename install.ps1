# TwisterLab Installer & Onboarding Bootstrapper for Windows
# This script configures python virtual environment, installs dependencies, and launches the onboarding wizard.

$ErrorActionPreference = "Stop"

Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "*  Welcome to the TwisterLab Installation Bootstrapper!  *" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Verify Python version
Write-Host "Step 1: Checking Python environment..." -ForegroundColor Yellow
$pythonPath = Get-Command python.exe -ErrorAction SilentlyContinue

if (-not $pythonPath) {
    Write-Host "[ERROR] Python not found in system PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.11 or newer (https://www.python.org/downloads/) and try again." -ForegroundColor Yellow
    exit 1
}

$pythonVersionString = & python --version
Write-Host "[OK] Found: $pythonVersionString" -ForegroundColor Green

# Parse version (requires 3.11+)
if ($pythonVersionString -match "Python (\d+)\.(\d+)") {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
        Write-Host "[ERROR] TwisterLab requires Python 3.11 or newer. Current: $($major).$($minor)" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Virtual Environment Setup
Write-Host ""
Write-Host "Step 2: Resolving Virtual Environment (.venv)..." -ForegroundColor Yellow

if (-not (Test-Path ".venv")) {
    Write-Host "   Creating new virtual environment..."
    try {
        python -m venv .venv
        Write-Host "[OK] Virtual environment created successfully" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[OK] Existing .venv virtual environment detected" -ForegroundColor Green
}

# Step 3: Install Dependencies
Write-Host ""
Write-Host "Step 3: Installing TwisterLab packages and registering CLI executable..." -ForegroundColor Yellow

$poetryPath = Get-Command poetry -ErrorAction SilentlyContinue
$venvPip = ".venv\Scripts\pip.exe"

if ($poetryPath) {
    Write-Host "   Poetry detected! Locking and installing dependencies..."
    try {
        & poetry lock
        & poetry install
        Write-Host "[OK] CLI installed and dependencies resolved via Poetry" -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Poetry install failed. Falling back to pip installation..." -ForegroundColor Yellow
        & $venvPip install -e .
        Write-Host "[OK] CLI installed and dependencies resolved via Pip" -ForegroundColor Green
    }
} else {
    Write-Host "   Poetry not found. Using local pip edit mode..."
    try {
        & $venvPip install -e .
        Write-Host "[OK] CLI installed and dependencies resolved via Pip" -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] Package installation failed." -ForegroundColor Red
        exit 1
    }
}

# Step 4: Run Onboarding Wizard
Write-Host ""
Write-Host "Step 4: Launching TwisterLab Onboarding Wizard..." -ForegroundColor Yellow
Write-Host "----------------------------------------------------------" -ForegroundColor Gray

$twisterlabCli = ".venv\Scripts\twisterlab.cmd"
if (-not (Test-Path $twisterlabCli)) {
    # Fallback to direct script execution if cmd shortcut is missing
    $venvPython = ".venv\Scripts\python.exe"
    & $venvPython -m twisterlab.cli.main onboard
} else {
    & $twisterlabCli onboard
}

Write-Host "----------------------------------------------------------" -ForegroundColor Gray
Write-Host "[OK] TwisterLab Onboarding Complete!" -ForegroundColor Green

# Step 5: PATH Registration (Optional)
Write-Host ""
Write-Host "Step 5: PATH Registration..." -ForegroundColor Yellow
$scriptsPath = (Get-Item ".venv\Scripts").FullName
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($userPath -notlike "*$scriptsPath*") {
    $choice = Read-Host "Would you like to add the TwisterLab executable to your User PATH? (y/N)"
    if ($choice -eq "y") {
        $newPath = "$userPath;$scriptsPath"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$env:Path;$scriptsPath"
        Write-Host "[OK] Added TwisterLab to User PATH. You may need to restart your terminal." -ForegroundColor Green
    } else {
        Write-Host "Skipping PATH registration." -ForegroundColor Gray
    }
} else {
    Write-Host "[OK] TwisterLab is already in your PATH." -ForegroundColor Green
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "🚀 TwisterLab v5.2.0 Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps (available from any terminal if added to PATH):" -ForegroundColor Gray
Write-Host "1. Test system connectivity: " -ForegroundColor Gray
Write-Host "   twisterlab doctor" -ForegroundColor White
Write-Host "2. Start the background server: " -ForegroundColor Gray
Write-Host "   twisterlab gateway start" -ForegroundColor White
Write-Host "3. List registered agents: " -ForegroundColor Gray
Write-Host "   twisterlab agent list" -ForegroundColor White
Write-Host ""
