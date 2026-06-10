# PowerShell script to install TwisterLab MCP configuration
# Run: .\install-mcp-config.ps1

param(
    [switch]$Force,
    [switch]$ContinueOnly,
    [switch]$ClaudeOnly
)

Write-Host "=== TwisterLab MCP Configuration Installer ===" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigDir = Join-Path $ScriptDir "config"

# Verify connection to MCP server
Write-Host "`nVerifying MCP server connection..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://192.168.0.30:30080/health" -TimeoutSec 5
    Write-Host "  ✓ MCP Server: $($response.status)" -ForegroundColor Green
    Write-Host "    Tools available: $($response.tools)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ Cannot reach MCP server at http://192.168.0.30:30080" -ForegroundColor Red
    Write-Host "    Make sure EdgeServer is running and K3s mcp-unified pod is active" -ForegroundColor Gray
}

# Install Continue config
if (-not $ClaudeOnly) {
    Write-Host "`nInstalling Continue IDE configuration..." -ForegroundColor Yellow
    
    $ContinueConfigDir = Join-Path $env:USERPROFILE ".continue"
    $ContinueConfigFile = Join-Path $ContinueConfigDir "config.yaml"
    
    if (-not (Test-Path $ContinueConfigDir)) {
        New-Item -ItemType Directory -Path $ContinueConfigDir -Force | Out-Null
    }
    
    $SourceConfig = Join-Path $ConfigDir "continue-config.yaml"
    
    if (Test-Path $ContinueConfigFile) {
        if ($Force) {
            Copy-Item $SourceConfig $ContinueConfigFile -Force
            Write-Host "  ✓ Overwritten: $ContinueConfigFile" -ForegroundColor Green
        } else {
            $BackupFile = "$ContinueConfigFile.backup"
            Copy-Item $ContinueConfigFile $BackupFile
            Write-Host "  ! Backup created: $BackupFile" -ForegroundColor Yellow
            Copy-Item $SourceConfig $ContinueConfigFile -Force
            Write-Host "  ✓ Updated: $ContinueConfigFile" -ForegroundColor Green
        }
    } else {
        Copy-Item $SourceConfig $ContinueConfigFile
        Write-Host "  ✓ Created: $ContinueConfigFile" -ForegroundColor Green
    }
}

# Install Claude Desktop config
if (-not $ContinueOnly) {
    Write-Host "`nInstalling Claude Desktop configuration..." -ForegroundColor Yellow
    
    $ClaudeConfigDir = Join-Path $env:APPDATA "Claude"
    $ClaudeConfigFile = Join-Path $ClaudeConfigDir "claude_desktop_config.json"
    
    if (-not (Test-Path $ClaudeConfigDir)) {
        New-Item -ItemType Directory -Path $ClaudeConfigDir -Force | Out-Null
    }
    
    $SourceConfig = Join-Path $ConfigDir "claude_desktop_config.json"
    
    if (Test-Path $ClaudeConfigFile) {
        if ($Force) {
            Copy-Item $SourceConfig $ClaudeConfigFile -Force
            Write-Host "  ✓ Overwritten: $ClaudeConfigFile" -ForegroundColor Green
        } else {
            $BackupFile = "$ClaudeConfigFile.backup"
            Copy-Item $ClaudeConfigFile $BackupFile
            Write-Host "  ! Backup created: $BackupFile" -ForegroundColor Yellow
            
            # Merge with existing config
            $ExistingConfig = Get-Content $ClaudeConfigFile | ConvertFrom-Json
            $NewConfig = Get-Content $SourceConfig | ConvertFrom-Json
            
            if (-not $ExistingConfig.mcpServers) {
                $ExistingConfig | Add-Member -NotePropertyName "mcpServers" -NotePropertyValue @{} -Force
            }
            
            foreach ($server in $NewConfig.mcpServers.PSObject.Properties) {
                $ExistingConfig.mcpServers | Add-Member -NotePropertyName $server.Name -NotePropertyValue $server.Value -Force
            }
            
            $ExistingConfig | ConvertTo-Json -Depth 10 | Set-Content $ClaudeConfigFile
            Write-Host "  ✓ Merged: $ClaudeConfigFile" -ForegroundColor Green
        }
    } else {
        Copy-Item $SourceConfig $ClaudeConfigFile
        Write-Host "  ✓ Created: $ClaudeConfigFile" -ForegroundColor Green
    }
}

# Check for npx
Write-Host "`nChecking dependencies..." -ForegroundColor Yellow
try {
    $npxVersion = & npx --version 2>&1
    Write-Host "  ✓ npx: $npxVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ npx not found - Install Node.js from https://nodejs.org" -ForegroundColor Red
}

Write-Host "`n=== Installation Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Restart Continue IDE and Claude Desktop" -ForegroundColor Gray
Write-Host "  2. In Continue, try '/health' command" -ForegroundColor Gray
Write-Host "  3. In Claude Desktop, ask to use 'monitoring_health_check' tool" -ForegroundColor Gray
Write-Host "`nMCP Server endpoints:" -ForegroundColor Yellow
Write-Host "  Health: http://192.168.0.30:30080/health" -ForegroundColor Gray
Write-Host "  Tools:  http://192.168.0.30:30080/tools" -ForegroundColor Gray
Write-Host "  MCP:    http://192.168.0.30:30080/mcp" -ForegroundColor Gray
