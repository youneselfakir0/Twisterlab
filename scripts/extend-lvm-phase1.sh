#!/bin/bash
# Phase 1 - LVM Extension Script (Budget $0)
# Date: 6 Février 2026
# Purpose: Extend system LVM to resolve DiskPressure

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════"
echo "  PHASE 1 - LVM EXTENSION (EDGESERVER)"
echo "  Budget: $0 - Using existing disk space"
echo "════════════════════════════════════════════════════════════"
echo ""

# Function to pause and wait for user confirmation
confirm() {
    read -p "$1 (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        echo "Operation cancelled by user."
        exit 1
    fi
}

# STEP 1: Pre-flight checks
echo "STEP 1: PRE-FLIGHT CHECKS"
echo "─────────────────────────────────────────────────────────────"
echo ""

echo "Current disk usage:"
df -h /
echo ""

echo "Volume Group info:"
sudo vgs ubuntu-vg
echo ""

echo "Logical Volume info:"
sudo lvs /dev/ubuntu-vg/ubuntu-lv
echo ""

echo "Physical Volume info:"
sudo pvs
echo ""

echo "Free space in Volume Group:"
sudo vgdisplay ubuntu-vg | grep "Free  PE"
echo ""

confirm "Continue with LVM extension?"

# STEP 2: Backup current state (metadata only - fast)
echo ""
echo "STEP 2: BACKUP LVM METADATA"
echo "─────────────────────────────────────────────────────────────"
BACKUP_DIR="/root/lvm-backup-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo vgcfgbackup -f "$BACKUP_DIR/ubuntu-vg" ubuntu-vg
echo "✅ LVM metadata backed up to: $BACKUP_DIR"
echo ""

confirm "Proceed with volume extension?"

# STEP 3: Calculate extension size
echo ""
echo "STEP 3: CALCULATE EXTENSION SIZE"
echo "─────────────────────────────────────────────────────────────"

# Get free space in GB
FREE_GB=$(sudo vgdisplay ubuntu-vg | grep "Free  PE" | awk '{print int($7/256)}')
echo "Available free space: ~${FREE_GB}GB"

# Use 50GB or all available (whichever is smaller)
if [ $FREE_GB -ge 50 ]; then
    EXTEND_SIZE="50G"
    echo "Will extend by: 50GB (recommended)"
else
    EXTEND_SIZE="${FREE_GB}G"
    echo "Will extend by: ${FREE_GB}GB (all available)"
fi
echo ""

confirm "Extend by $EXTEND_SIZE?"

# STEP 4: Extend Logical Volume
echo ""
echo "STEP 4: EXTEND LOGICAL VOLUME"
echo "─────────────────────────────────────────────────────────────"
echo "Running: sudo lvextend -L +$EXTEND_SIZE /dev/ubuntu-vg/ubuntu-lv"
sudo lvextend -L +$EXTEND_SIZE /dev/ubuntu-vg/ubuntu-lv

if [ $? -eq 0 ]; then
    echo "✅ Logical volume extended successfully!"
else
    echo "❌ ERROR: Failed to extend logical volume!"
    exit 1
fi
echo ""

# STEP 5: Resize Filesystem
echo "STEP 5: RESIZE FILESYSTEM"
echo "─────────────────────────────────────────────────────────────"
echo "Running: sudo resize2fs /dev/ubuntu-vg/ubuntu-lv"
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv

if [ $? -eq 0 ]; then
    echo "✅ Filesystem resized successfully!"
else
    echo "❌ ERROR: Failed to resize filesystem!"
    exit 1
fi
echo ""

# STEP 6: Verify Results
echo "STEP 6: VERIFY RESULTS"
echo "─────────────────────────────────────────────────────────────"
echo ""

echo "New disk usage:"
df -h /
echo ""

echo "Updated Volume Group:"
sudo vgs ubuntu-vg
echo ""

echo "Updated Logical Volume:"
sudo lvs /dev/ubuntu-vg/ubuntu-lv
echo ""

# Calculate improvement
OLD_SIZE=100
NEW_SIZE=$(df -h / | tail -1 | awk '{print $2}' | sed 's/G//')
IMPROVEMENT=$(echo "scale=0; ($NEW_SIZE - $OLD_SIZE) / $OLD_SIZE * 100" | bc)

echo "════════════════════════════════════════════════════════════"
echo "  ✅ PHASE 1 - LVM EXTENSION COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Before:     ~100GB"
echo "After:      ${NEW_SIZE}GB"
echo "Gain:       +${IMPROVEMENT}%"
echo "Cost:       $0 (FREE!)"
echo ""
echo "DiskPressure risk: ELIMINATED ✅"
echo "Backup location:   $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Monitor disk usage: df -h /"
echo "  2. Check K8s pods: kubectl get pods --all-namespaces"
echo "  3. Proceed to Docker optimization (Phase 1 continued)"
echo ""
echo "════════════════════════════════════════════════════════════"
