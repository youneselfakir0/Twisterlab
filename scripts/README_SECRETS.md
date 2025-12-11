# 🚀 Configuring Secrets for CD/Release Workflows

This directory contains tools and documentation for configuring GitHub Secrets required by the CI/CD pipelines.

## 📚 Documentation

- **[GitHub Secrets Guide](../docs/GITHUB_SECRETS_GUIDE.md)** - Complete reference of all required secrets

## 🛠️ Quick Setup Tools

### Option 1: Interactive PowerShell Script (Recommended)

Run the interactive configuration helper:

```powershell
.\scripts\configure-github-secrets.ps1
```

This script will:
- ✅ Check if GitHub CLI is installed
- ✅ Verify authentication
- ✅ Show current secrets status
- ✅ Guide you through configuring each secret

**Dry run mode** (check status without making changes):
```powershell
.\scripts\configure-github-secrets.ps1 -DryRun
```

### Option 2: Manual Configuration via GitHub CLI

```bash
# Set a secret
gh secret set SECRET_NAME --body "secret-value" --repo youneselfakir0/Twisterlab

# List existing secrets
gh secret list --repo youneselfakir0/Twisterlab

# Delete a secret
gh secret delete SECRET_NAME --repo youneselfakir0/Twisterlab
```

### Option 3: Web UI

1. Go to: https://github.com/youneselfakir0/Twisterlab/settings/secrets/actions
2. Click "New repository secret"
3. Enter name and value
4. Click "Add secret"

## 🎯 Minimum Setup for Testing

To test the CD workflow without full production infrastructure:

```powershell
# Required for basic testing
gh secret set KUBE_CONFIG_STAGING --body "$(cat ~/.kube/config | base64 -w 0)"
gh secret set STAGING_DATABASE_URL --body "postgresql+asyncpg://user:pass@localhost:5432/twisterlab_test"
gh secret set STAGING_REDIS_URL --body "redis://localhost:6379"
```

## 📋 Secrets Checklist

### Critical (Required for Deployment)
- [ ] `KUBE_CONFIG_STAGING`
- [ ] `STAGING_DATABASE_URL`
- [ ] `STAGING_REDIS_URL`

### Important (Production Ready)
- [ ] `KUBE_CONFIG_PRODUCTION`
- [ ] `PRODUCTION_DATABASE_URL`
- [ ] `PRODUCTION_REDIS_URL`
- [ ] `AWS_ACCESS_KEY_ID`
- [ ] `AWS_SECRET_ACCESS_KEY`

### Optional (Enhanced Features)
- [ ] `SLACK_WEBHOOK_URL`
- [ ] `PYPI_API_TOKEN`
- [ ] `MAIL_USERNAME`
- [ ] `MAIL_PASSWORD`

## 🧪 Testing the CD Workflow

After configuring secrets, test the workflow:

### Manual Trigger (Staging Only)
```bash
gh workflow run cd-enhanced.yml \
  --repo youneselfakir0/Twisterlab \
  --field environment=staging \
  --field version=latest
```

### View Workflow Runs
```bash
gh run list --repo youneselfakir0/Twisterlab --workflow=cd-enhanced.yml
```

### Watch Live Logs
```bash
gh run watch --repo youneselfakir0/Twisterlab
```

## 🔒 Security Best Practices

1. **Never commit secrets to Git**
   - Secrets should ONLY be in GitHub Settings
   - Use `.env` files locally (in `.gitignore`)

2. **Use separate credentials for staging/production**
   - Different database passwords
   - Different AWS keys
   - Different Kubernetes clusters

3. **Rotate secrets regularly**
   - Every 90 days minimum
   - After any security incident

4. **Use read-only tokens where possible**
   - Limit AWS IAM permissions
   - Use Kubernetes service accounts with minimal RBAC

## 🆘 Troubleshooting

### GitHub CLI Not Installed
```bash
# Windows (via Chocolatey)
choco install gh

# Windows (via Winget)
winget install GitHub.cli

# Or download from: https://cli.github.com/
```

### Not Authenticated
```bash
gh auth login
# Follow the prompts
```

### Secret Not Found Error in Workflow
- Verify secret name matches exactly (case-sensitive)
- Check repository permissions
- Ensure you're configuring the right repository

### Base64 Encoding Issues
```bash
# Linux/macOS
cat ~/.kube/config | base64 -w 0

# Windows PowerShell
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content ~/.kube/config -Raw)))
```

## 📖 Additional Resources

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [TwisterLab CD Workflow](.github/workflows/cd-enhanced.yml)
- [TwisterLab Release Workflow](.github/workflows/release-enhanced.yml)

## 🎓 Learning Path

1. **Start Here**: Read the [GitHub Secrets Guide](../docs/GITHUB_SECRETS_GUIDE.md)
2. **Configure**: Run `configure-github-secrets.ps1` with `-DryRun` first
3. **Test Staging**: Set up minimal staging secrets and test deployment
4. **Go Production**: Add production secrets when ready
5. **Monitor**: Check workflow runs at https://github.com/youneselfakir0/Twisterlab/actions

---

**Need Help?** Check the [full documentation](../docs/GITHUB_SECRETS_GUIDE.md) or review the [workflow files](.github/workflows/)
