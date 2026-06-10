#!/usr/bin/env bash

# TwisterLab Remote Bootstrapper (Linux/macOS)
# This script clones TwisterLab and launches the local installer.
# Usage: curl -sSL https://<host>/bootstrap.sh | bash

set -e

# ANSI Colors
GREEN="\033[92m"
YELLOW="\033[93m"
CYAN="\033[96m"
RED="\033[91m"
RESET="\033[0m"
BOLD="\033[1m"

REPO_URL="https://github.com/youneselfakir0/Twisterlab.git"
INSTALL_DIR="$HOME/twisterlab"

clear
echo -e "=========================================================="
echo -e "${BOLD}${CYAN}🪂  TwisterLab Remote Installer Bootstrapper  🪂${RESET}"
echo -e "=========================================================="
echo ""

# Check for Git
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Error: git not found in system PATH.${RESET}"
    echo -e "${YELLOW}Please install Git and try again.${RESET}"
    exit 1
fi

# Clone or Update Repo
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}Step 1: Cloning repository to $INSTALL_DIR...${RESET}"
    git clone "$REPO_URL" "$INSTALL_DIR"
else
    echo -e "${YELLOW}Step 1: Repository already exists at $INSTALL_DIR. Updating...${RESET}"
    cd "$INSTALL_DIR"
    git pull
    cd - > /dev/null
fi

# Run the local installer
echo -e "${YELLOW}Step 2: Launching local installation script...${RESET}"
cd "$INSTALL_DIR"
if [ -f "install.sh" ]; then
    chmod +x install.sh
    ./install.sh
else
    echo -e "${RED}❌ Error: install.sh not found in the cloned repository.${RESET}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Done! You can now use TwisterLab.${RESET}"
