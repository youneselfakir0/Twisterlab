#!/bin/bash
# ============================================================
# TwisterLab - GitHub Self-Hosted Runner Installation
# Run this script on EdgeServer (192.168.0.30)
# ============================================================

set -e

RUNNER_TOKEN="AOV55KRYM6FJLQSFMSU5NRTJNJMRK"
REPO_URL="https://github.com/youneselfakir0/Twisterlab"
RUNNER_NAME="edgeserver-runner"
RUNNER_LABELS="self-hosted,linux,k3s,twisterlab"
RUNNER_DIR="/opt/actions-runner"

echo "=== GitHub Self-Hosted Runner Installation ==="
echo "Repository: $REPO_URL"
echo "Runner Name: $RUNNER_NAME"
echo ""

# Create runner directory
sudo mkdir -p $RUNNER_DIR
sudo chown $USER:$USER $RUNNER_DIR
cd $RUNNER_DIR

# Download latest runner
echo "📥 Downloading GitHub Actions Runner..."
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | grep -oP '"tag_name": "v\K[^"]+')
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
  https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Extract
echo "📦 Extracting..."
tar xzf actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Configure runner
echo "⚙️ Configuring runner..."
./config.sh --url $REPO_URL \
  --token $RUNNER_TOKEN \
  --name $RUNNER_NAME \
  --labels $RUNNER_LABELS \
  --unattended \
  --replace

# Install as service
echo "🔧 Installing as systemd service..."
sudo ./svc.sh install
sudo ./svc.sh start

# Verify
echo ""
echo "✅ Runner installed and started!"
echo ""
sudo ./svc.sh status

echo ""
echo "=== Installation Complete ==="
echo "The runner '$RUNNER_NAME' is now registered and running."
echo "Check GitHub: $REPO_URL/settings/actions/runners"
