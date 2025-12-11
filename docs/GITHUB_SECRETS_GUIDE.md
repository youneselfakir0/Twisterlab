# GitHub Secrets Configuration Guide

## 📋 Required Secrets for CI/CD Workflows

This document lists all GitHub Secrets that need to be configured for the TwisterLab CI/CD pipelines to work properly.

---

## 🔐 Secrets Overview

### **Automatically Available** (No Action Required)
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### **Required for CD Workflow** (Deployment)

#### Kubernetes Configuration
- **`KUBE_CONFIG_STAGING`** (Base64 encoded)
  - Description: Kubeconfig file for staging Kubernetes cluster
  - How to generate:
    ```bash
    cat ~/.kube/config | base64 -w 0
    ```
  - Usage: Deploy to staging environment

- **`KUBE_CONFIG_PRODUCTION`** (Base64 encoded)
  - Description: Kubeconfig file for production Kubernetes cluster
  - How to generate: Same as staging
  - Usage: Deploy to production environment

#### Database & Redis
- **`STAGING_DATABASE_URL`**
  - Format: `postgresql+asyncpg://user:password@host:5432/dbname`
  - Usage: Staging database connection

- **`STAGING_REDIS_URL`**
  - Format: `redis://host:6379`
  - Usage: Staging Redis connection

- **`PRODUCTION_DATABASE_URL`**
  - Format: `postgresql+asyncpg://user:password@host:5432/dbname`
  - Usage: Production database connection

- **`PRODUCTION_REDIS_URL`**
  - Format: `redis://host:6379`
  - Usage: Production Redis connection

#### AWS (Backup Storage)
- **`AWS_ACCESS_KEY_ID`**
  - Description: AWS access key for S3 backups
  - Usage: Pre-deployment database backups

- **`AWS_SECRET_ACCESS_KEY`**
  - Description: AWS secret key for S3 backups
  - Usage: Pre-deployment database backups

#### Notifications
- **`SLACK_WEBHOOK_URL`**
  - Description: Slack webhook for deployment notifications
  - How to generate: https://api.slack.com/messaging/webhooks
  - Usage: CD and Release workflows

- **`STATUS_PAGE_TOKEN`** (Optional)
  - Description: Token for updating status page
  - Usage: Deployment status updates

### **Required for Release Workflow** (Publishing)

#### PyPI Publishing
- **`PYPI_API_TOKEN`**
  - Description: PyPI API token for publishing packages
  - How to generate: https://pypi.org/manage/account/token/
  - Usage: Publish stable releases to PyPI

#### Email Notifications
- **`MAIL_USERNAME`**
  - Description: Email account username
  - Usage: Send release notifications

- **`MAIL_PASSWORD`**
  - Description: Email account password or app password
  - Usage: Send release notifications

---

## 🚀 How to Configure Secrets in GitHub

### Step 1: Navigate to Repository Settings
1. Go to: https://github.com/youneselfakir0/Twisterlab/settings/secrets/actions
2. Click **"New repository secret"**

### Step 2: Add Each Secret
For each secret listed above:
1. Enter the **Name** (exactly as shown above)
2. Enter the **Value** (the actual secret)
3. Click **"Add secret"**

### Step 3: Verify Configuration
After adding secrets, you can verify by:
- Running the CD workflow manually: Actions → CD - Continuous Deployment → Run workflow
- Creating a new tag: `git tag v0.1.0-test && git push origin v0.1.0-test`

---

## 🧪 Testing CD Workflow Without Full Secrets

To test the CD workflow without full production setup:

### Option 1: Use Dummy Values
For testing purposes, you can set dummy values:
```bash
KUBE_CONFIG_STAGING=ZHVtbXkK  # base64 of "dummy"
STAGING_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test
STAGING_REDIS_URL=redis://localhost:6379
```

### Option 2: Skip Production Deployment
The CD workflow has a `workflow_dispatch` trigger that allows manual runs with environment selection:
- Select "staging" environment only
- This will skip production-specific secrets

### Option 3: Use continue-on-error
You can temporarily modify the workflow to add `continue-on-error: true` to deployment steps for testing.

---

## 📊 Secret Priority Levels

### **Critical** (Required for basic deployment)
- ✅ `KUBE_CONFIG_STAGING`
- ✅ `STAGING_DATABASE_URL`
- ✅ `STAGING_REDIS_URL`

### **Important** (Required for production)
- ⚠️ `KUBE_CONFIG_PRODUCTION`
- ⚠️ `PRODUCTION_DATABASE_URL`
- ⚠️ `PRODUCTION_REDIS_URL`
- ⚠️ `AWS_ACCESS_KEY_ID`
- ⚠️ `AWS_SECRET_ACCESS_KEY`

### **Optional** (Enhanced features)
- 💡 `SLACK_WEBHOOK_URL` - Notifications
- 💡 `STATUS_PAGE_TOKEN` - Status page updates
- 💡 `PYPI_API_TOKEN` - PyPI publishing
- 💡 `MAIL_USERNAME` - Email notifications
- 💡 `MAIL_PASSWORD` - Email notifications

---

## 🔒 Security Best Practices

1. **Never commit secrets** to the repository
2. **Use environment-specific secrets** (separate staging/production)
3. **Rotate secrets regularly** (every 90 days recommended)
4. **Use read-only tokens** where possible
5. **Enable secret scanning** in repository settings
6. **Use GitHub Environments** for additional protection:
   - Settings → Environments → New environment
   - Add required reviewers for production deployments

---

## 🎯 Current Status

### ✅ Working Without Secrets
- CI Enhanced workflow (linting, testing, building)
- Basic build and test workflows
- Security scanning workflows

### ⏸️ Requires Secrets
- CD Enhanced workflow (deployment stages will fail)
- Release Enhanced workflow (PyPI publishing will fail)
- Blue-Green deployments
- Pre-deployment backups

---

## 📝 Next Steps

1. **Minimum Viable Setup** (for testing):
   - Add `KUBE_CONFIG_STAGING` (can be dummy for testing)
   - Add `STAGING_DATABASE_URL` (can point to local DB)
   - Add `STAGING_REDIS_URL` (can point to local Redis)

2. **Full Production Setup**:
   - Configure all critical and important secrets
   - Set up GitHub Environments with approvals
   - Test with staging environment first
   - Deploy to production after validation

3. **Optional Enhancements**:
   - Add Slack webhook for notifications
   - Configure AWS for backups
   - Set up PyPI token for releases
   - Configure email notifications

---

## 🆘 Troubleshooting

### Secret Not Found Error
```
Error: Secret KUBE_CONFIG_STAGING not found
```
**Solution**: Verify secret name matches exactly (case-sensitive)

### Invalid Base64 Error
```
Error: invalid base64 data
```
**Solution**: Ensure kubeconfig is properly base64 encoded with `-w 0` flag

### Permission Denied
```
Error: The workflow is not valid. .github/workflows/cd-enhanced.yml: Unexpected value 'secrets'
```
**Solution**: Check workflow syntax and secret references

---

## 📚 Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Kubernetes Config Documentation](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
- [AWS S3 Credentials](https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html)

---

**Last Updated**: December 10, 2025  
**Workflows Version**: CI Enhanced v1.0, CD Enhanced v1.0, Release Enhanced v1.0
