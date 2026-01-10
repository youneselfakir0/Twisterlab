# Changelog

## [3.5.0] - 2026-01-09

### 🚀 Major Release: Real Agent Implementations

This release transforms TwisterLab from a demo into a **production-ready** platform with real agent implementations.

### Added

- **Real MonitoringAgent**: Now uses `psutil` for real CPU/RAM/Disk metrics
  - Returns actual system hostname, platform, and timestamp
  - No more hardcoded values
  
- **Real DesktopCommanderAgent**: Complete rewrite with security features
  - 51+ whitelisted safe commands (hostname, df, ps, netstat, etc.)
  - Pattern matching to block dangerous commands (rm -rf, format, etc.)
  - Timeout protection (max 300 seconds)
  - Audit logging of all command executions
  - Subprocess-based real command execution
  
- **Kubernetes HA Deployment** (`k8s/deployments/twisterlab-api-ha.yaml`)
  - HorizontalPodAutoscaler (3-10 replicas based on CPU/Memory)
  - PodDisruptionBudget (min 2 pods available)
  - Anti-affinity rules for node distribution
  - NetworkPolicy for security isolation
  
- **Ingress Configuration** (`k8s/services/ingress.yaml`)
  - TLS/SSL termination
  - Rate limiting (100 req/s)
  - CORS headers
  - Security headers (X-Frame-Options, XSS-Protection, etc.)
  
- **Alertmanager Configuration** (`monitoring/alertmanager/alertmanager.yml`)
  - Multi-channel alerts (Slack, Email)
  - Severity-based routing (critical → immediate, medium → ops)
  - Inhibition rules to prevent alert storms
  
- **Prometheus Alert Rules** (`monitoring/prometheus/rules/twisterlab_alerts.yml`)
  - 25+ alert rules covering API, Agents, Tickets, Security, Infrastructure
  - Predictive alerts (anomaly detection, capacity warning)
  
- **Grafana Dashboard Improvements** (`monitoring/grafana/dashboards/`)
  - System Health row with CPU/RAM/Disk gauges
  - Agent Latency Heatmap
  - API Throughput panel
  - Desktop Commander execution stats
  - Service status indicators
  
- **E2E Demo Script** (`demo_e2e.py`)
  - Complete incident resolution demonstration
  - Shows real metrics from psutil
  - Maestro orchestration with 100% success rate
  
- **E2E Test Scenarios** (`tests/e2e/test_4_incident_scenarios.py`)
  - Database performance incident flow
  - Application down scenario
  - Security breach simulation
  - Agent chaining tests

### Changed

- **README.md**: Updated to v3.5.0 with new features documentation
- **test_real_agents.py**: Fixed test signatures for new method interfaces

### Fixed

- **Maestro Import**: Fixed circular import issue with agent_registry
- **MonitoringAgent**: Changed from `execute()` to `handle_collect_metrics()` returning `AgentResponse`
- **DesktopCommanderAgent**: Removed `device_id` parameter from local execution

### Metrics

- ✅ **89 unit tests passing**
- ✅ **Real system metrics**: CPU ~19%, RAM ~54%, Disk ~60%
- ✅ **Maestro orchestration**: 100% success rate
- ✅ **E2E demo**: Complete flow validated

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