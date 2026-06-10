#!/bin/bash
# MCP Unified Image Build Script
# Run this on EdgeServer

set -e

BUILD_DIR="/tmp/twisterlab-mcp-build-$(date +%s)"
IMAGE_NAME="twisterlab/mcp-unified:latest"

echo "=========================================="
echo "MCP Unified Image Build"
echo "=========================================="
echo "Build directory: $BUILD_DIR"
echo "Image name: $IMAGE_NAME"
echo ""

# Create build directory
echo "📁 Creating build directory..."
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo "✅ Build directory created: $(pwd)"
echo ""

# Note: Files should be copied separately via scp
# This script expects:
# - src/ directory
# - requirements.txt
# - Dockerfile

echo "⏳ Waiting for source files to be copied..."
echo "   Expecting: src/, requirements.txt, Dockerfile"
echo ""

# This will be run after files are copied
if [ ! -d "src" ] || [ ! -f "requirements.txt" ] || [ ! -f "Dockerfile" ]; then
    echo "❌ ERROR: Required files not found!"
    echo "   Please copy: src/, requirements.txt, Dockerfile to $BUILD_DIR"
    exit 1
fi

echo "✅ Source files found"
echo ""

# Build the image
echo "🔨 Building Docker image..."
echo "   This may take 5-10 minutes..."
echo ""

sudo docker build \
    --progress=plain \
    --no-cache \
    -t "$IMAGE_NAME" \
    -f Dockerfile \
    . 2>&1 | tee build.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "✅ Docker build completed successfully!"
    echo ""
    
    # Import to K3s
    echo "📦 Importing image to K3s containerd..."
    sudo docker save "$IMAGE_NAME" | sudo k3s ctr images import -
    
    echo ""
    echo "✅ Image imported to K3s!"
    echo ""
    
    # Verify
    echo "🔍 Verifying image in K3s..."
    sudo k3s crictl images | grep twisterlab/mcp-unified || echo "Warning: Image not found in crictl"
    
    echo ""
    echo "=========================================="
    echo "✅ BUILD COMPLETE!"
    echo "=========================================="
    echo "Image: $IMAGE_NAME"
    echo "Build log: $BUILD_DIR/build.log"
    echo ""
    echo "Clean up with: rm -rf $BUILD_DIR"
    echo ""
else
    echo ""
    echo "❌ Docker build failed!"
    echo "Check build log: $BUILD_DIR/build.log"
    exit 1
fi
