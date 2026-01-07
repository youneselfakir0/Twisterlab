# Changelog

## [3.4.0] - 2026-01-05

### Added
- **CI/CD**: Coverage reporting with Codecov integration
- **CI/CD**: Integration tests job in GitHub Actions
- **CI/CD**: Security scan with Bandit
- **CI/CD**: Format check with Ruff

### Changed
- **Code Quality**: Migrated `@validator` to `@field_validator` (Pydantic v2)
- **Code Quality**: Migrated `declarative_base()` to SQLAlchemy 2.0 style
- **Code Quality**: Fixed duplicate import in `security.py`
- **Code Quality**: Fixed `BrowserAgent` → `RealBrowserAgent` naming consistency
- **Documentation**: Updated README to v3.4.0 with Codecov badge
- **Documentation**: Updated copilot-instructions.md with complete file references

### Removed
- **Cleanup**: Deleted `archive/` folder (legacy code)
- **Cleanup**: Deleted `docs/archive/` folder (old reports)
- **Cleanup**: Deleted `k8s/archive/` folder (old manifests)
- **Cleanup**: Deleted `src/twisterlab/agents/mcp_agents/` (obsolete)
- **Cleanup**: Deleted duplicate files in `agents/api/` (routes_*.py, monitoring.py)
- **Cleanup**: Deleted stub `api/security.py` (real file in agents/api/)
- **Cleanup**: Deleted `archive/legacy_tests/` (duplicate of tests/)

### Fixed
- **Tests**: Fixed 3 failing tests (singleton_pattern, rate_limit_block, rate_limit_multiple_ips)
- **Tests**: All 39 tests passing (25 unit + 14 integration)

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