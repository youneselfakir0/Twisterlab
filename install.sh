#!/usr/bin/env bash

# TwisterLab Installer & Onboarding Bootstrapper for Linux / macOS
# This script configures python virtual environment, installs dependencies, and launches the onboarding wizard.

set -e

# ANSI Colors
GREEN="\033[92m"
YELLOW="\033[93m"
CYAN="\033[96m"
RED="\033[91m"
RESET="\033[0m"
BOLD="\033[1m"

clear
echo -e "=========================================================="
echo -e "${BOLD}${CYAN}🪂  Welcome to the TwisterLab Installation Bootstrapper!  🪂${RESET}"
echo -e "=========================================================="
echo ""

# Step 1: Check Python
echo -e "${YELLOW}Step 1: Checking Python environment...${RESET}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found in system PATH.${RESET}"
    echo -e "${YELLOW}Please install Python 3.11 or newer and try again.${RESET}"
    exit 1
fi

python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
major=$(echo "$python_version" | cut -d. -f1)
minor=$(echo "$python_version" | cut -d. -f2)

if [ "$major" -lt 3 ] || { [ "$major" -eq 3 ] && [ "$minor" -lt 11 ]; }; then
    echo -e "${RED}❌ Error: TwisterLab requires Python 3.11 or newer. Current: python3 $python_version${RESET}"
    exit 1
fi

echo -e "${GREEN}✓ Found: Python $python_version${RESET}"

# Step 2: Virtual Environment Setup
echo ""
echo -e "${YELLOW}Step 2: Resolving Virtual Environment (.venv)...${RESET}"
if [ ! -d ".venv" ]; then
    echo "   Creating new virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created successfully${RESET}"
else
    echo -e "${GREEN}✓ Existing .venv virtual environment detected${RESET}"
fi

# Step 3: Install dependencies
echo ""
echo -e "${YELLOW}Step 3: Installing TwisterLab packages and registering CLI executable...${RESET}"

if command -v poetry &> /dev/null; then
    echo "   Poetry detected! Locking and installing dependencies..."
    poetry lock
    poetry install
    echo -e "${GREEN}✓ CLI installed and dependencies resolved via Poetry${RESET}"
else
    echo "   Poetry not found. Using local pip edit mode..."
    .venv/bin/pip install -e .
    echo -e "${GREEN}✓ CLI installed and dependencies resolved via Pip${RESET}"
fi

# Step 4: Run Onboarding Wizard
echo ""
echo -e "${YELLOW}Step 4: Launching TwisterLab Onboarding Wizard...${RESET}"
echo -e "\033[90m----------------------------------------------------------${RESET}"

if [ -f ".venv/bin/twisterlab" ]; then
    .venv/bin/twisterlab onboard
else
    .venv/bin/python3 -m twisterlab.cli.main onboard
fi

echo -e "\033[90m----------------------------------------------------------${RESET}"
echo -e "${GREEN}✓ TwisterLab Onboarding Complete!${RESET}"

# Step 5: PATH Suggestion
echo ""
echo -e "${YELLOW}Step 5: PATH Suggestion...${RESET}"
abs_path=$(pwd)
bin_path="$abs_path/.venv/bin"

if [[ ":$PATH:" != *":$bin_path:"* ]]; then
    echo -e "To run 'twisterlab' from anywhere, add this to your .bashrc or .zshrc:"
    echo -e "  ${CYAN}export PATH=\"\$PATH:$bin_path\"${RESET}"
else
    echo -e "${GREEN}✓ TwisterLab is already in your PATH.${RESET}"
fi

echo ""
echo -e "=========================================================="
echo -e "${BOLD}${CYAN}🚀 TwisterLab v5.2.0 Setup Complete!${RESET}"
echo -e "=========================================================="
echo ""
echo -e "${CYAN}Next steps (available via 'twisterlab' if in PATH):${RESET}"
echo -e "1. Test system connectivity:"
echo -e "   ${BOLD}twisterlab doctor${RESET}"
echo -e "2. Start the background server:"
echo -e "   ${BOLD}twisterlab gateway start${RESET}"
echo -e "3. List registered agents:"
echo -e "   ${BOLD}twisterlab agent list${RESET}"
echo ""
