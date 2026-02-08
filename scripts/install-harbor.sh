#!/bin/bash
# Phase 1 - Action 4: Harbor Registry Installation
# Date: 8 Février 2026
# Purpose: Install Harbor private container registry

set -e

echo "════════════════════════════════════════════════════════════"
echo "  PHASE 1 - ACTION 4: HARBOR REGISTRY INSTALLATION"
echo "  Open-source private container registry"
echo "════════════════════════════════════════════════════════════"
echo ""

# Configuration
HARBOR_VERSION="2.11.0"
HARBOR_DIR="/opt/harbor"
HARBOR_DATA="/var/lib/harbor"
HARBOR_HOSTNAME="harbor.twisterlab.local"
HARBOR_PORT="8090"  # Non-standard to avoid conflicts
ADMIN_PASSWORD="TwisterLab2026!"  # Change in production!

# STEP 1: Pre-flight checks
echo "STEP 1: PRE-FLIGHT CHECKS"
echo "─────────────────────────────────────────────────────────────"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found!"
    exit 1
fi
echo "✅ Docker: $(docker --version)"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "⚠️  Docker Compose plugin not found, installing..."
    sudo apt update
    sudo apt install -y docker-compose-plugin
fi
echo "✅ Docker Compose: $(docker compose version)"

# Check disk space
AVAILABLE=$(df / | tail -1 | awk '{print $4}')
if [ $AVAILABLE -lt 5242880 ]; then  # 5GB in KB
    echo "⚠️  Low disk space: $(($AVAILABLE / 1024 / 1024))GB available"
    echo "Harbor needs ~5GB. Continue anyway?"
    read -p "Proceed? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        exit 1
    fi
else
    echo "✅ Disk space: $(($AVAILABLE / 1024 / 1024))GB available"
fi

# Check ports
echo "Checking ports..."
if sudo netstat -tulpn | grep -q ":${HARBOR_PORT} "; then
    echo "⚠️  Port $HARBOR_PORT already in use!"
    echo "Harbor will use different port."
    HARBOR_PORT="8091"
fi
echo "✅ Harbor will use port: $HARBOR_PORT"
echo ""

# STEP 2: Create directories
echo "STEP 2: CREATE DIRECTORIES"
echo "─────────────────────────────────────────────────────────────"
sudo mkdir -p "$HARBOR_DIR"
sudo mkdir -p "$HARBOR_DATA"
echo "✅ Directories created"
echo ""

# STEP 3: Download Harbor
echo "STEP 3: DOWNLOAD HARBOR"
echo "─────────────────────────────────────────────────────────────"
cd /tmp

if [ -f "harbor-offline-installer-v${HARBOR_VERSION}.tgz" ]; then
    echo "ℹ️  Harbor installer already downloaded"
else
    echo "Downloading Harbor v${HARBOR_VERSION} (~600MB)..."
    echo "This may take 5-10 minutes..."
    wget -q --show-progress \
        "https://github.com/goharbor/harbor/releases/download/v${HARBOR_VERSION}/harbor-offline-installer-v${HARBOR_VERSION}.tgz" \
        || {
            echo "❌ Download failed! Trying alternative..."
            wget "https://github.com/goharbor/harbor/releases/download/v${HARBOR_VERSION}/harbor-offline-installer-v${HARBOR_VERSION}.tgz"
        }
fi

echo "✅ Harbor downloaded"
echo ""

# STEP 4: Extract
echo "STEP 4: EXTRACT HARBOR"
echo "─────────────────────────────────────────────────────────────"
if [ -d "/tmp/harbor" ]; then
    sudo rm -rf /tmp/harbor
fi

tar xzf "harbor-offline-installer-v${HARBOR_VERSION}.tgz"
sudo mv harbor/* "$HARBOR_DIR/"
echo "✅ Harbor extracted to $HARBOR_DIR"
echo ""

# STEP 5: Configure
echo "STEP 5: CONFIGURE HARBOR"
echo "─────────────────────────────────────────────────────────────"
cd "$HARBOR_DIR"

# Create config from template
sudo cp harbor.yml.tmpl harbor.yml

# Update configuration
sudo sed -i "s/^hostname: .*/hostname: ${HARBOR_HOSTNAME}/" harbor.yml
sudo sed -i "s/^  port: 80/  port: ${HARBOR_PORT}/" harbor.yml
sudo sed -i "s|^  # certificate: .*|  # certificate: /path/to/cert|" harbor.yml
sudo sed -i "s|^  # private_key: .*|  # private_key: /path/to/key|" harbor.yml
sudo sed -i "s/^harbor_admin_password: .*/harbor_admin_password: ${ADMIN_PASSWORD}/" harbor.yml
sudo sed -i "s|^data_volume: .*|data_volume: ${HARBOR_DATA}|" harbor.yml

# Disable HTTPS for simplicity (can enable later)
sudo sed -i '/^https:/,/^[^ ]/{/^https:/!{/^[^ ]/!d}}; /^https:/d' harbor.yml

echo "✅ Harbor configured:"
echo "   - Hostname: $HARBOR_HOSTNAME"
echo "   - Port: $HARBOR_PORT"
echo "   - Admin password: $ADMIN_PASSWORD"
echo "   - Data directory: $HARBOR_DATA"
echo "   - HTTPS: Disabled (HTTP only)"
echo ""

# STEP 6: Install
echo "STEP 6: INSTALL HARBOR"
echo "─────────────────────────────────────────────────────────────"
echo "Installing Harbor components..."
echo "This will take 5-10 minutes..."
echo ""

sudo ./install.sh --with-trivy

if [ $? -eq 0 ]; then
    echo "✅ Harbor installed successfully!"
else
    echo "❌ Harbor installation failed!"
    echo "Check logs: docker-compose logs"
    exit 1
fi
echo ""

# STEP 7: Verify installation
echo "STEP 7: VERIFY INSTALLATION"
echo "─────────────────────────────────────────────────────────────"
sleep 5

echo "Checking Harbor containers..."
sudo docker-compose ps

echo ""
RUNNING=$(sudo docker-compose ps | grep "Up" | wc -l)
TOTAL=$(sudo docker-compose ps | grep -v "NAME" | wc -l)

if [ $RUNNING -ge 7 ]; then
    echo "✅ Harbor is running ($RUNNING/$TOTAL containers up)"
else
    echo "⚠️  Some containers may still be starting ($RUNNING/$TOTAL up)"
    echo "Wait 1-2 minutes and check: docker-compose ps"
fi
echo ""

# STEP 8: Access information
echo "════════════════════════════════════════════════════════════"
echo "  ✅ HARBOR INSTALLATION COMPLETE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "🌐 Access Information:"
echo "─────────────────────────────────────────────────────────────"
echo "URL:      http://${HARBOR_HOSTNAME}:${HARBOR_PORT}"
echo "          or http://192.168.0.30:${HARBOR_PORT}"
echo "          or http://localhost:${HARBOR_PORT}"
echo ""
echo "Login:"
echo "  Username: admin"
echo "  Password: ${ADMIN_PASSWORD}"
echo ""
echo "📋 Next Steps:"
echo "─────────────────────────────────────────────────────────────"
echo "1. Access Web UI:"
echo "   Open browser: http://192.168.0.30:${HARBOR_PORT}"
echo "   Login with admin credentials above"
echo ""
echo "2. Test Docker login:"
echo "   docker login ${HARBOR_HOSTNAME}:${HARBOR_PORT}"
echo "   Username: admin"
echo "   Password: ${ADMIN_PASSWORD}"
echo ""
echo "3. Push test image:"
echo "   docker tag alpine:latest ${HARBOR_HOSTNAME}:${HARBOR_PORT}/library/alpine:test"
echo "   docker push ${HARBOR_HOSTNAME}:${HARBOR_PORT}/library/alpine:test"
echo ""
echo "4. Manage Harbor:"
echo "   Start:   cd $HARBOR_DIR && sudo docker-compose start"
echo "   Stop:    cd $HARBOR_DIR && sudo docker-compose stop"
echo "   Restart: cd $HARBOR_DIR && sudo docker-compose restart"
echo "   Logs:    cd $HARBOR_DIR && sudo docker-compose logs -f"
echo ""
echo "5. Add to /etc/hosts (on your local machine):"
echo "   192.168.0.30   ${HARBOR_HOSTNAME}"
echo ""
echo "📚 Documentation:"
echo "   https://goharbor.io/docs/"
echo ""
echo "🔐 Security Notes:"
echo "   - Currently HTTP only (no HTTPS)"
echo "   - Change admin password in production!"
echo "   - Consider enabling HTTPS for production use"
echo ""
echo "════════════════════════════════════════════════════════════"
