# Changelog

## [3.3.0] - 2025-12-31

### Added
- **Security**: Rate Limiting Middleware (60 req/min per IP) added to API.
- **Security**: Kubernetes Network Policies (Default Deny + Ingress Rules) implemented.
- **Security**: CORS restrictions configurable via `ALLOWED_ORIGINS`.
- **Testing**: New Unit Tests for AgentRegistry, RateLimitMiddleware, and MonitoringAgent.
- **Monitoring**: Logs added for security middleware initialization and IP tracking.

### Changed
- **Refactoring**: Renamed `agents/core/monitoring.py` to `monitoring_utils.py` to fix import conflicts.
- **Refactoring**: Renamed `TwisterAgent` in `agents/core` to `CoreAgent` to resolve ambiguity with `agents/base`.
- **Configuration**: Updated `conftest.py` for correct `src` path resolution.

### Fixed
- **API**: Fixed 404/Connection errors during load testing by patching Network Policies and Port configurations.
- **Security**: Fixed Rate Limiting crashing due to missing `passlib` (made optional).

## [3.2.0]
- Initial functional version with Metrics and MCP support.