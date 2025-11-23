#!/bin/bash
set -e

echo "=== Construction des images Docker ==="

# Image API
echo "Construction twisterlab-api:latest..."
docker build -t twisterlab-api:latest -f Dockerfile.api .

# Image MCP
echo "Construction twisterlab-mcp:latest..."
docker build -t twisterlab-mcp:latest -f Dockerfile.mcp .

echo "Images construites avec succès"