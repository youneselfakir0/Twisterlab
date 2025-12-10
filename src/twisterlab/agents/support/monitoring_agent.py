"""
Monitoring Agent - System and Agent Performance Monitoring
===========================================================

Provides continuous monitoring, metrics collection, and alerting.
"""

import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil  # type: ignore

from ..base import TwisterAgent, accepts_context_or_task

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MonitoringAgent(TwisterAgent):
    """
    MonitoringAgent provides continuous performance monitoring and alerting.

    Features:
    - System metrics collection (CPU, memory, disk, network)
    - Agent metrics tracking (response time, success rate, error rate)
    - Database metrics monitoring (connections, query time)
    - API metrics monitoring (request rate, latency, status codes)
    - Threshold-based alerting with severity levels
    - Prometheus metrics export
    - Dashboard data aggregation

    Usage:
        agent = MonitoringAgent()
        result = await agent.execute(
            "Collect metrics",
            {"operation": "collect_metrics"}
        )
    """

    def __init__(self):
        """Initialize Monitoring Agent"""
        super().__init__(
            name="monitoring",
            display_name="Monitoring Agent",
            description=("System and agent performance monitoring with alerting"),
            model="deepseek-r1",
            temperature=0.0,  # Deterministic for monitoring
        )

        # Metrics storage: metric_name -> deque of data points
        # 24h @ 1min = 1440 samples
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1440))

        # Alerts storage
        self.alerts: List[Dict[str, Any]] = []

        # Alert thresholds
        self.thresholds = {
            "cpu_usage": 80.0,  # Percent
            "memory_usage": 85.0,  # Percent
            "disk_usage": 90.0,  # Percent
            "api_response_time": 2.0,  # Seconds
            "error_rate": 10.0,  # Percent
            "agent_response_time": 5.0,  # Seconds
        }

        # Agent names to monitor
        self.monitored_agents = [
            "classifier",
            "resolver",
            "desktop_commander",
            "maestro",
            "sync",
            "backup",
        ]

    @accepts_context_or_task
    async def execute(self, task_or_context, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute monitoring operations.

        Args:
            task: Task description
            context: Must contain:
                - operation: str (collect_metrics, get_metrics,
                  check_health, get_alerts, export_prometheus)
                - metric_name: str (optional, for get_metrics)

        Returns:
            Dict with operation results
        """
        try:
            # Normalize inputs for both calling conventions
            if context is None and isinstance(task_or_context, dict):
                context = task_or_context
            operation = context.get("operation")

            if operation == "collect_metrics":
                res = await self._collect_metrics()
                res.setdefault("operation", operation)
                res.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                return res

            elif operation == "get_metrics":
                metric_name = context.get("metric_name")
                res = await self._get_metrics(metric_name)
                res.setdefault("operation", operation)
                res.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                return res

            elif operation in ("check_health", "health_check"):
                # Support both check_health (core) and health_check (legacy/real agent)
                if hasattr(self, "_health_check"):
                    res = await self._health_check({})
                else:
                    res = await self._check_health()
                res.setdefault("operation", operation)
                res.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                return res

            elif operation == "get_alerts":
                res = await self._get_alerts()
                res.setdefault("operation", operation)
                res.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                return res

            elif operation == "export_prometheus":
                res = await self._export_prometheus()
                res.setdefault("operation", operation)
                res.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                return res

            else:
                return {"status": "error", "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.error(f"Error executing monitoring task: {e}")
            return {"status": "error", "error": str(e)}

    async def _collect_metrics(self) -> Dict[str, Any]:
        """Collect all metrics and check thresholds"""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            metrics_collected = 0

            # Collect system metrics
            system_metrics = await self._collect_system_metrics()
            for metric_name, value in system_metrics.items():
                self.metrics[metric_name].append(
                    {"timestamp": timestamp, "value": value}
                )
                metrics_collected += 1

            # Collect agent metrics
            agent_metrics = await self._collect_agent_metrics()
            for metric_name, value in agent_metrics.items():
                self.metrics[metric_name].append(
                    {"timestamp": timestamp, "value": value}
                )
                metrics_collected += 1

            # Collect database metrics
            db_metrics = await self._collect_database_metrics()
            for metric_name, value in db_metrics.items():
                self.metrics[metric_name].append(
                    {"timestamp": timestamp, "value": value}
                )
                metrics_collected += 1

            # Collect API metrics
            api_metrics = await self._collect_api_metrics()
            for metric_name, value in api_metrics.items():
                self.metrics[metric_name].append(
                    {"timestamp": timestamp, "value": value}
                )
                metrics_collected += 1

            # Check thresholds and create alerts
            await self._check_thresholds()

            return {
                "status": "success",
                "metrics_collected": metrics_collected,
                "timestamp": timestamp,
            }

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {"status": "error", "error": str(e)}

    async def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system resource metrics using psutil"""
        try:
            metrics = {}

            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics["system_cpu_usage_percent"] = cpu_percent
            metrics["system_cpu_count"] = float(psutil.cpu_count())

            # Memory metrics
            memory = psutil.virtual_memory()
            metrics["system_memory_usage_percent"] = memory.percent
            mem_available_mb = memory.available / (1024 * 1024)
            metrics["system_memory_available_mb"] = mem_available_mb
            mem_total_mb = memory.total / (1024 * 1024)
            metrics["system_memory_total_mb"] = mem_total_mb

            # Disk metrics
            disk = psutil.disk_usage("/")
            metrics["system_disk_usage_percent"] = disk.percent
            metrics["system_disk_free_gb"] = disk.free / (1024 * 1024 * 1024)
            metrics["system_disk_total_gb"] = disk.total / (1024 * 1024 * 1024)

            # Network metrics
            net_io = psutil.net_io_counters()
            metrics["system_network_bytes_sent"] = float(net_io.bytes_sent)
            metrics["system_network_bytes_recv"] = float(net_io.bytes_recv)

            return metrics

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}

    async def _collect_agent_metrics(self) -> Dict[str, float]:
        """Collect metrics for all monitored agents"""
        try:
            metrics = {}

            for agent_name in self.monitored_agents:
                # Simulate agent metrics (in production, query agents)
                metrics[f"agent_{agent_name}_response_time_ms"] = 150.0
                metrics[f"agent_{agent_name}_success_rate"] = 98.5
                metrics[f"agent_{agent_name}_error_rate"] = 1.5
                metrics[f"agent_{agent_name}_requests_total"] = 1000.0

            return metrics

        except Exception as e:
            logger.error(f"Error collecting agent metrics: {e}")
            return {}

    async def _collect_database_metrics(self) -> Dict[str, float]:
        """Collect database performance metrics"""
        try:
            metrics = {}

            # Simulate database metrics (in production, would query PostgreSQL)
            metrics["db_connections_active"] = 25.0
            metrics["db_connections_idle"] = 10.0
            metrics["db_query_time_avg_ms"] = 45.0
            metrics["db_queries_total"] = 5000.0
            metrics["db_slow_queries"] = 5.0  # Queries > 1s

            return metrics

        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {}

    async def _collect_api_metrics(self) -> Dict[str, float]:
        """Collect API endpoint metrics"""
        try:
            metrics = {}

            # Simulate API metrics (in production, would query FastAPI metrics)
            metrics["api_requests_total"] = 10000.0
            metrics["api_requests_per_second"] = 50.0
            metrics["api_response_time_avg_ms"] = 120.0
            metrics["api_response_time_p95_ms"] = 250.0
            metrics["api_response_time_p99_ms"] = 450.0
            metrics["api_status_2xx"] = 9500.0
            metrics["api_status_4xx"] = 400.0
            metrics["api_status_5xx"] = 100.0

            return metrics

        except Exception as e:
            logger.error(f"Error collecting API metrics: {e}")
            return {}

    async def _check_thresholds(self):
        """Check metrics against thresholds and create alerts"""
        try:
            # Get latest metrics
            latest_metrics = {}
            for metric_name, data_points in self.metrics.items():
                if data_points:
                    latest_metrics[metric_name] = data_points[-1]["value"]

            # Check CPU
            cpu_usage = latest_metrics.get("system_cpu_usage_percent", 0)
            if cpu_usage > self.thresholds["cpu_usage"]:
                cpu_threshold = self.thresholds["cpu_usage"]
                msg = f"CPU usage is {cpu_usage:.1f}% " f"(threshold: {cpu_threshold}%)"
                await self._create_alert("High CPU Usage", msg, AlertSeverity.WARNING)

            # Check Memory
            mem_usage = latest_metrics.get("system_memory_usage_percent", 0)
            if mem_usage > self.thresholds["memory_usage"]:
                mem_threshold = self.thresholds["memory_usage"]
                msg = (
                    f"Memory usage is {mem_usage:.1f}% "
                    f"(threshold: {mem_threshold}%)"
                )
                await self._create_alert(
                    "High Memory Usage", msg, AlertSeverity.WARNING
                )

            # Check Disk
            disk_usage = latest_metrics.get("system_disk_usage_percent", 0)
            if disk_usage > self.thresholds["disk_usage"]:
                disk_threshold = self.thresholds["disk_usage"]
                msg = (
                    f"Disk usage is {disk_usage:.1f}% "
                    f"(threshold: {disk_threshold}%)"
                )
                await self._create_alert("High Disk Usage", msg, AlertSeverity.CRITICAL)

            # Check API response time
            api_time_ms = latest_metrics.get("api_response_time_avg_ms", 0)
            api_response_time = api_time_ms / 1000.0
            if api_response_time > self.thresholds["api_response_time"]:
                api_threshold = self.thresholds["api_response_time"]
                msg = (
                    f"API response time is {api_response_time:.2f}s "
                    f"(threshold: {api_threshold}s)"
                )
                await self._create_alert(
                    "Slow API Response", msg, AlertSeverity.WARNING
                )

            # Check agent response times
            for agent_name in self.monitored_agents:
                metric_name = f"agent_{agent_name}_response_time_ms"
                response_time = latest_metrics.get(metric_name, 0) / 1000.0
                agent_threshold = self.thresholds["agent_response_time"]
                if response_time > agent_threshold:
                    msg = (
                        f"Agent {agent_name} response time is "
                        f"{response_time:.2f}s (threshold: {agent_threshold}s)"
                    )
                    await self._create_alert(
                        f"Slow Agent Response: {agent_name}", msg, AlertSeverity.WARNING
                    )

            # Check error rates
            for agent_name in self.monitored_agents:
                metric_name = f"agent_{agent_name}_error_rate"
                error_rate = latest_metrics.get(metric_name, 0)
                error_threshold = self.thresholds["error_rate"]
                if error_rate > error_threshold:
                    msg = (
                        f"Agent {agent_name} error rate is "
                        f"{error_rate:.1f}% (threshold: {error_threshold}%)"
                    )
                    await self._create_alert(
                        f"High Error Rate: {agent_name}", msg, AlertSeverity.CRITICAL
                    )

        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")

    async def _create_alert(self, title: str, message: str, severity: AlertSeverity):
        """Create and store an alert"""
        try:
            alert = {
                "alert_id": f"ALERT-{len(self.alerts) + 1:04d}",
                "title": title,
                "message": message,
                "severity": severity.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "acknowledged": False,
            }

            self.alerts.append(alert)

            logger.warning(f"[{severity.value.upper()}] {title}: {message}")

            # In production, would send to alerting system
            # (Email, Slack, PagerDuty, etc.)

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    async def _get_metrics(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Get collected metrics"""
        try:
            if metric_name:
                # Get specific metric
                if metric_name in self.metrics:
                    return {
                        "status": "success",
                        "metric_name": metric_name,
                        "data_points": list(self.metrics[metric_name]),
                        "count": len(self.metrics[metric_name]),
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"Metric '{metric_name}' not found",
                    }
            else:
                # Get all metrics summary
                return {
                    "status": "success",
                    "total_metrics": len(self.metrics),
                    "metrics": list(self.metrics.keys()),
                }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {"status": "error", "error": str(e)}

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Return a concise health status for the MonitoringAgent.

        This method is used by orchestrators and other agents that request
        per-agent health, so it returns a stable structure including the last
        collected metrics summary, any outstanding alerts, and a timestamp.
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        # Provide the latest summary metrics (latest point or default 0)
        latest = {}
        for k, v in self.metrics.items():
            if v:
                latest[k] = v[-1]["value"]
        return {
            "status": "success",
            "healthy": True if not self.alerts else False,
            "last_check": timestamp,
            "alerts_count": len(self.alerts),
            "latest_metrics": latest,
            "timestamp": timestamp,
        }

    async def _check_health(self) -> Dict[str, Any]:
        """Check health of all services"""
        try:
            health_status = {"overall": "healthy", "services": {}}

            # Check PostgreSQL (simulated)
            health_status["services"]["postgresql"] = "healthy"

            # Check Redis (simulated)
            health_status["services"]["redis"] = "healthy"

            # Check agents (simulated)
            for agent_name in self.monitored_agents:
                health_status["services"][agent_name] = "healthy"

            return {
                "status": "success",
                "health": health_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error checking health: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_alerts(self) -> Dict[str, Any]:
        """Get active alerts"""
        try:
            # Filter unacknowledged alerts
            active_alerts = [
                alert for alert in self.alerts if not alert.get("acknowledged", False)
            ]

            return {
                "status": "success",
                "total_alerts": len(active_alerts),
                "alerts": active_alerts,
            }

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return {"status": "error", "error": str(e)}

    async def _export_prometheus(self) -> Dict[str, Any]:
        """Export metrics in Prometheus format"""
        try:
            prometheus_lines = []

            # Convert metrics to Prometheus format
            for metric_name, data_points in self.metrics.items():
                if data_points:
                    latest = data_points[-1]
                    # Convert to Prometheus naming convention
                    prom_name = metric_name.replace(".", "_")
                    prometheus_lines.append(f"twisterlab_{prom_name} {latest['value']}")

            return {
                "status": "success",
                "format": "prometheus",
                "metrics": "\n".join(prometheus_lines),
            }

        except Exception as e:
            logger.error(f"Error exporting Prometheus metrics: {e}")
            return {"status": "error", "error": str(e)}

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard visualization"""
        try:
            # Get latest values for key metrics
            latest_metrics = {}

            for metric_name, data_points in self.metrics.items():
                if data_points:
                    latest_metrics[metric_name] = data_points[-1]["value"]

            # Get active alerts
            active_alerts = [
                alert for alert in self.alerts if not alert.get("acknowledged", False)
            ]

            return {
                "metrics": latest_metrics,
                "alerts": active_alerts,
                "health": "healthy" if len(active_alerts) == 0 else "degraded",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            "agent": self.name,
            "status": "healthy",
            "metrics_count": len(self.metrics),
            "alerts_count": len(self.alerts),
        }
