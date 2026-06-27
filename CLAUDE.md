# TwisterLab — Claude Code Project Root

## Working Directory
All file operations MUST be relative to this directory:
`C:\Users\Administrator\Documents\twisterlab`

Never write files to `C:\Users\Administrator\.claude\` or any subdirectory of it.

## Project Structure
```
twisterlab/
├── src/          # Core application source
├── vse/          # Version Synchronization Engine (new)
├── tests/        # All unit/integration tests
├── k8s/          # Kubernetes manifests
├── deploy/       # Deployment scripts
├── docs/         # Documentation
├── scripts/      # Utility scripts (100+)
├── monitoring/   # Prometheus/Grafana config
├── frontend/     # React UI
└── requirements.txt
```

## Rules
- New modules go under `src/` or their named top-level dir (e.g. `vse/`)
- Tests go under `tests/`
- Always verify file writes with a directory listing after creation
- Never duplicate entries in `requirements.txt`
