# GitHub Secrets Configuration Helper
# This script helps configure GitHub secrets for TwisterLab CI/CD workflows

param(
    [Parameter(Mandatory=$false)]
    [string]$Owner = "youneselfakir0",
    
    [Parameter(Mandatory=$false)]
    [string]$Repo = "Twisterlab",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "  GitHub Secrets Configuration Helper" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Check if GitHub CLI is installed
try {
    $ghVersion = gh --version 2>&1 | Select-Object -First 1
    Write-Host "✅ GitHub CLI detected: $ghVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ GitHub CLI not found. Please install it from:" -ForegroundColor Red
    Write-Host "   https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# Check authentication
Write-Host "`nChecking GitHub authentication..." -ForegroundColor Yellow
try {
    $authStatus = gh auth status 2>&1
    Write-Host "✅ Authenticated to GitHub" -ForegroundColor Green
} catch {
    Write-Host "❌ Not authenticated. Please run: gh auth login" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Target Repository: $Owner/$Repo" -ForegroundColor Cyan
Write-Host ""

# Define required secrets with descriptions
$secrets = @(
    @{
        Name = "KUBE_CONFIG_STAGING"
        Description = "Base64-encoded Kubernetes config for staging"
        Required = $true
        Example = "base64-encoded-kubeconfig"
    },
    @{
        Name = "KUBE_CONFIG_PRODUCTION"
        Description = "Base64-encoded Kubernetes config for production"
        Required = $false
        Example = "base64-encoded-kubeconfig"
    },
    @{
        Name = "STAGING_DATABASE_URL"
        Description = "Staging PostgreSQL connection string"
        Required = $true
        Example = "postgresql+asyncpg://user:pass@host:5432/twisterlab_staging"
    },
    @{
        Name = "STAGING_REDIS_URL"
        Description = "Staging Redis connection string"
        Required = $true
        Example = "redis://localhost:6379"
    },
    @{
        Name = "PRODUCTION_DATABASE_URL"
        Description = "Production PostgreSQL connection string"
        Required = $false
        Example = "postgresql+asyncpg://user:pass@host:5432/twisterlab"
    },
    @{
        Name = "PRODUCTION_REDIS_URL"
        Description = "Production Redis connection string"
        Required = $false
        Example = "redis://prod-host:6379"
    },
    @{
        Name = "AWS_ACCESS_KEY_ID"
        Description = "AWS Access Key for S3 backups"
        Required = $false
        Example = "AKIAIOSFODNN7EXAMPLE"
    },
    @{
        Name = "AWS_SECRET_ACCESS_KEY"
        Description = "AWS Secret Key for S3 backups"
        Required = $false
        Example = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    },
    @{
        Name = "SLACK_WEBHOOK_URL"
        Description = "Slack webhook URL for notifications"
        Required = $false
        Example = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
    },
    @{
        Name = "PYPI_API_TOKEN"
        Description = "PyPI API token for package publishing"
        Required = $false
        Example = "pypi-AgEIcHlwaS5vcmcC..."
    },
    @{
        Name = "MAIL_USERNAME"
        Description = "Email username for notifications"
        Required = $false
        Example = "noreply@twisterlab.com"
    },
    @{
        Name = "MAIL_PASSWORD"
        Description = "Email password or app password"
        Required = $false
        Example = "app-specific-password"
    }
)

Write-Host "📋 Secrets Configuration Status:" -ForegroundColor Yellow
Write-Host ""

# Check existing secrets
$existingSecrets = @()
try {
    $secretsList = gh secret list --repo "$Owner/$Repo" 2>&1 | Out-String
    $existingSecrets = $secretsList -split "`n" | ForEach-Object { 
        if ($_ -match '^([A-Z_]+)\s+') { $matches[1] }
    }
} catch {
    Write-Host "⚠️  Could not fetch existing secrets (this is normal if none exist)" -ForegroundColor Yellow
}

foreach ($secret in $secrets) {
    $exists = $existingSecrets -contains $secret.Name
    $indicator = if ($exists) { "✅" } else { "❌" }
    $required = if ($secret.Required) { "[REQUIRED]" } else { "[OPTIONAL]" }
    
    Write-Host "$indicator $($secret.Name) $required" -ForegroundColor $(if ($exists) { "Green" } else { "Red" })
    Write-Host "   $($secret.Description)" -ForegroundColor Gray
    if (-not $exists) {
        Write-Host "   Example: $($secret.Example)" -ForegroundColor DarkGray
    }
    Write-Host ""
}

# Offer to configure secrets
Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan

if ($DryRun) {
    Write-Host "🔍 Dry Run Mode - No changes will be made" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To actually configure secrets, run:" -ForegroundColor Green
    Write-Host "  .\scripts\configure-github-secrets.ps1" -ForegroundColor Cyan
    exit 0
}

$configure = Read-Host "`nWould you like to configure missing secrets interactively? (y/n)"

if ($configure -ne 'y') {
    Write-Host "`n✋ Configuration cancelled." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 To configure secrets manually, use:" -ForegroundColor Cyan
    Write-Host "   gh secret set <SECRET_NAME> --body '<value>' --repo $Owner/$Repo" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   Or visit:" -ForegroundColor Cyan
    Write-Host "   https://github.com/$Owner/$Repo/settings/secrets/actions" -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "🔧 Interactive Secret Configuration" -ForegroundColor Cyan
Write-Host "   (Press Enter to skip optional secrets)" -ForegroundColor Gray
Write-Host ""

foreach ($secret in $secrets) {
    $exists = $existingSecrets -contains $secret.Name
    
    if ($exists) {
        $overwrite = Read-Host "Secret '$($secret.Name)' already exists. Overwrite? (y/n)"
        if ($overwrite -ne 'y') {
            Write-Host "  ⏭️  Skipped $($secret.Name)" -ForegroundColor Yellow
            continue
        }
    }
    
    $requiredText = if ($secret.Required) { " [REQUIRED]" } else { " [Optional]" }
    Write-Host ""
    Write-Host "🔐 $($secret.Name)$requiredText" -ForegroundColor Cyan
    Write-Host "   $($secret.Description)" -ForegroundColor Gray
    Write-Host "   Example: $($secret.Example)" -ForegroundColor DarkGray
    
    $value = Read-Host "   Enter value (or press Enter to skip)"
    
    if ([string]::IsNullOrWhiteSpace($value)) {
        if ($secret.Required) {
            Write-Host "  ⚠️  Warning: Required secret skipped!" -ForegroundColor Yellow
        } else {
            Write-Host "  ⏭️  Skipped" -ForegroundColor Gray
        }
        continue
    }
    
    try {
        gh secret set $secret.Name --body $value --repo "$Owner/$Repo"
        Write-Host "  ✅ Secret '$($secret.Name)' configured successfully" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Failed to set secret '$($secret.Name)': $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "✅ Secret configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Verify secrets at: https://github.com/$Owner/$Repo/settings/secrets/actions" -ForegroundColor Gray
Write-Host "   2. Test CD workflow: gh workflow run cd-enhanced.yml --repo $Owner/$Repo" -ForegroundColor Gray
Write-Host "   3. Check workflow runs: https://github.com/$Owner/$Repo/actions" -ForegroundColor Gray
Write-Host ""
