"""TwisterLab package entry point."""

import sys

# CRITICAL: Add /app to sys.path BEFORE any submodule imports to ensure package is found
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

__all__ = ["api", "agents", "utils"]
