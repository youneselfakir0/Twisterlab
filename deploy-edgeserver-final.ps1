#Requires -Version 5.1

param(
    [string]$EdgeServerIP = "192.168.0.30",
    [string]$Username = "twister"
)

Write-Host "Déploiement TwisterLab sur EdgeServer ($EdgeServerIP)..." -ForegroundColor Green

# Test connexion SSH
Write-Host "Test connexion SSH..." -ForegroundColor Yellow
ssh -o ConnectTimeout=10 $Username@$EdgeServerIP "echo 'Connexion SSH établie'"

# Créer répertoire sur EdgeServer
ssh $Username@$EdgeServerIP "mkdir -p /home/twister/TwisterLab"

# Transfert des manifests K8s
Write-Host "Transfert fichiers K8s..." -ForegroundColor Yellow
$files = @(
    "k8s/base/namespace.yaml",
    "k8s/base/configmap.yaml",
    "k8s/base/secrets.yaml",
    "k8s/base/storage.yaml",
    "k8s/deployments/api.yaml",
    "k8s/deployments/postgres.yaml",
    "k8s/deployments/redis.yaml",
    "k8s/deployments/mcp/orchestrator.yaml",
    "k8s/deployments/monitoring/grafana.yaml",
    "k8s/deployments/monitoring/prometheus.yaml",
    "k8s/ingress/main-ingress.yaml"
)

foreach ($file in $files) {
    scp "$file" "$Username@$EdgeServerIP`:/home/twister/TwisterLab/"
}

# Transfert des scripts nettoyés
Write-Host "Transfert scripts nettoyés..." -ForegroundColor Yellow
scp "configure-sudo.sh" "$Username@$EdgeServerIP`:/home/twister/"
scp "install-k3s-clean.sh" "$Username@$EdgeServerIP`:/home/twister/"
scp "install-storage.sh" "$Username@$EdgeServerIP`:/home/twister/"
scp "install-prereq-clean.sh" "$Username@$EdgeServerIP`:/home/twister/"
scp "deploy-twisterlab-clean.sh" "$Username@$EdgeServerIP`:/home/twister/"
scp "verify-clean.sh" "$Username@$EdgeServerIP`:/home/twister/"

# Configuration sudo
Write-Host "Configuration sudo sans mot de passe..." -ForegroundColor Yellow
ssh -t $Username@$EdgeServerIP "chmod +x /home/twister/configure-sudo.sh && /home/twister/configure-sudo.sh"

# Installation K3s
Write-Host "Installation K3s sur EdgeServer..." -ForegroundColor Yellow
ssh $Username@$EdgeServerIP "chmod +x /home/twister/install-k3s-clean.sh && /home/twister/install-k3s-clean.sh"

# Installation du stockage
Write-Host "Installation stockage local..." -ForegroundColor Yellow
ssh $Username@$EdgeServerIP "chmod +x /home/twister/install-storage.sh && /home/twister/install-storage.sh"

# Installation prérequis
Write-Host "Installation prérequis..." -ForegroundColor Yellow
ssh $Username@$EdgeServerIP "chmod +x /home/twister/install-prereq-clean.sh && /home/twister/install-prereq-clean.sh"

# Déploiement TwisterLab
Write-Host "Déploiement TwisterLab..." -ForegroundColor Yellow
ssh $Username@$EdgeServerIP "chmod +x /home/twister/deploy-twisterlab-clean.sh && /home/twister/deploy-twisterlab-clean.sh"

# Vérification
Write-Host "Vérification déploiement..." -ForegroundColor Yellow
ssh $Username@$EdgeServerIP "chmod +x /home/twister/verify-clean.sh && /home/twister/verify-clean.sh"

Write-Host "Déploiement terminé sur EdgeServer!" -ForegroundColor Green
Write-Host "Services disponibles:" -ForegroundColor Cyan
Write-Host "  API: http://api.twisterlab.local" -ForegroundColor White
Write-Host "  Grafana: http://grafana.twisterlab.local" -ForegroundColor White
Write-Host "  Prometheus: http://prometheus.twisterlab.local" -ForegroundColor White