"""API package for TwisterLab."""
import sys

# CRITICAL: Add /app to sys.path BEFORE any imports to ensure twisterlab package is found
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

# from . import main  # Removed to avoid circular imports

__all__ = ["main"]
