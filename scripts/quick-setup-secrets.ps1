#!/usr/bin/env pwsh
# Quick setup script for GitHub Secrets with local/test values
# Use this for testing workflows before real infrastructure is ready

Write-Host "🔐 Quick Setup - GitHub Secrets for Testing" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if gh CLI is available
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "❌ GitHub CLI (gh) not found. Install from: https://cli.github.com/" -ForegroundColor Red
    exit 1
}

Write-Host "📊 Current secrets:" -ForegroundColor Yellow
gh secret list
Write-Host ""

# Staging secrets (minimal for testing)
Write-Host "🎯 Setting up staging secrets..." -ForegroundColor Green

# STAGING_REDIS_URL (local Redis)
Write-Host "Setting STAGING_REDIS_URL..."
"redis://localhost:6379/0" | gh secret set STAGING_REDIS_URL
Write-Host "✅ STAGING_REDIS_URL configured" -ForegroundColor Green

# KUBE_CONFIG_STAGING (placeholder)
Write-Host "Setting KUBE_CONFIG_STAGING..."
@"
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://staging-cluster.twisterlab.local:6443
    insecure-skip-tls-verify: true
  name: staging-cluster
contexts:
- context:
    cluster: staging-cluster
    user: staging-user
    namespace: twisterlab-staging
  name: staging
current-context: staging
users:
- name: staging-user
  user:
    token: placeholder-token-replace-with-real
"@ | gh secret set KUBE_CONFIG_STAGING
Write-Host "✅ KUBE_CONFIG_STAGING configured (placeholder)" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 Minimal staging secrets configured!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Updated secrets list:" -ForegroundColor Yellow
gh secret list
Write-Host ""

Write-Host "⚠️  IMPORTANT NOTES:" -ForegroundColor Yellow
Write-Host "1. KUBE_CONFIG_STAGING is a placeholder - update with real kubeconfig" -ForegroundColor Yellow
Write-Host "2. STAGING_DATABASE_URL already configured ✅" -ForegroundColor Green
Write-Host "3. STAGING_REDIS_URL set to local Redis (update for remote)" -ForegroundColor Yellow
Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Cyan
Write-Host "   - Update KUBE_CONFIG_STAGING with real cluster config" -ForegroundColor White
Write-Host "   - Test staging deployment: gh workflow run cd-enhanced.yml" -ForegroundColor White
Write-Host "   - Check issue #11 for full setup guide" -ForegroundColor White
