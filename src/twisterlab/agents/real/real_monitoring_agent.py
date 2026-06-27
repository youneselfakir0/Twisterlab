"""""""""

RealMonitoringAgent - Real System Metrics Collection.

RealMonitoringAgent - Real System Metrics Collection 📊RealMonitoringAgent - Real System Metrics Collection 📊

This agent collects REAL system metrics using psutil:

- CPU usage (per-core and total)

- Memory usage (RAM, swap)

- Disk usage (per partition)This agent collects REAL system metrics using psutil:This agent collects REAL system metrics using psutil:

- Network I/O

- Process information- CPU usage (per-core and total)- CPU usage (per-core and total)

- System uptime

- Memory usage (RAM, swap)- Memory usage (RAM, swap)

Falls back to simulated data if psutil is not available.

"""- Disk usage (per partition)- Disk usage (per partition)



from __future__ import annotations- Network I/O- Network I/O



import logging- Process information- Process information

import os

import platform- System uptime- System uptime

import socket

from datetime import datetime, timezone

from typing import List

Falls back to simulated data if psutil is not available.Falls back to simulated data if psutil is not available.

try:

    import psutil""""""

    PSUTIL_AVAILABLE = True

except ImportError:

    psutil = None

    PSUTIL_AVAILABLE = Falsefrom __future__ import annotationsfrom __future__ import annotations



from twisterlab.agents.core.base import (

    TwisterAgent,

    AgentCapability,import loggingimport logging

    AgentResponse,

    CapabilityType,import osimport os

    CapabilityParam,

    ParamType,import platformimport platform

)

import socketimport socket

logger = logging.getLogger(__name__)

from datetime import datetime, timezonefrom datetime import datetime, timezone



class RealMonitoringAgent(TwisterAgent):from typing import Listfrom typing import List

    """Collects real system metrics using psutil."""



    def __init__(self) -> None:

        super().__init__()# Try to import psutil for real metrics# Try to import psutil for real metrics

        self._boot_time = datetime.now(timezone.utc)

        if PSUTIL_AVAILABLE:try:try:

            logger.info("RealMonitoringAgent initialized with psutil")

        else:    import psutil    import psutil

            logger.warning("psutil not available, using simulated metrics")

    PSUTIL_AVAILABLE = True    PSUTIL_AVAILABLE = True

    @property

    def name(self) -> str:except ImportError:except ImportError:

        return "monitoring"

    psutil = None    psutil = None

    @property

    def description(self) -> str:    PSUTIL_AVAILABLE = False    PSUTIL_AVAILABLE = False

        return "Collects real system metrics (CPU, memory, disk, network) using psutil"



    def get_capabilities(self) -> List[AgentCapability]:

        return [from twisterlab.agents.core.base import (from twisterlab.agents.core.base import (

            AgentCapability(

                name="collect_metrics",    TwisterAgent,    TwisterAgent,

                description="Collect all system metrics",

                handler="handle_collect_metrics",    AgentCapability,    AgentCapability,

                capability_type=CapabilityType.QUERY,

                params=[    AgentResponse,    AgentResponse,

                    CapabilityParam(

                        "include_processes",    CapabilityType,    CapabilityType,

                        ParamType.BOOLEAN,

                        "Include top processes list",    CapabilityParam,    CapabilityParam,

                        required=False,

                        default=False,    ParamType,    ParamType,

                    ),

                ],))

                tags=["monitoring", "metrics"],

            ),

            AgentCapability(

                name="get_cpu_info",logger = logging.getLogger(__name__)logger = logging.getLogger(__name__)

                description="Get detailed CPU usage information",

                handler="handle_get_cpu_info",

                capability_type=CapabilityType.QUERY,

                params=[],

                tags=["monitoring", "cpu"],

            ),class RealMonitoringAgent(TwisterAgent):class RealMonitoringAgent(TwisterAgent):

            AgentCapability(

                name="get_memory_info",    """    """

                description="Get RAM and swap memory usage",

                handler="handle_get_memory_info",    Collects real system metrics using psutil.    Collects real system metrics using psutil.

                capability_type=CapabilityType.QUERY,

                params=[],        

                tags=["monitoring", "memory"],

            ),    Capabilities:    Capabilities:

            AgentCapability(

                name="get_disk_info",    - collect_metrics: Get all system metrics    - collect_metrics: Get all system metrics

                description="Get disk partitions and usage",

                handler="handle_get_disk_info",    - get_cpu_info: Detailed CPU information    - get_cpu_info: Detailed CPU information

                capability_type=CapabilityType.QUERY,

                params=[],    - get_memory_info: RAM and swap usage    - get_memory_info: RAM and swap usage

                tags=["monitoring", "disk"],

            ),    - get_disk_info: Disk partitions and usage    - get_disk_info: Disk partitions and usage

            AgentCapability(

                name="get_network_info",    - get_network_info: Network I/O statistics    - get_network_info: Network I/O statistics

                description="Get network I/O statistics",

                handler="handle_get_network_info",    - get_process_list: Top processes by resource usage    - get_process_list: Top processes by resource usage

                capability_type=CapabilityType.QUERY,

                params=[],    - check_service_health: Check if a service is running    - check_service_health: Check if a service is running

                tags=["monitoring", "network"],

            ),    """    """

            AgentCapability(

                name="check_service_health",

                description="Check if a service/process is running",

                handler="handle_check_service_health",    def __init__(self) -> None:    def __init__(self) -> None:

                capability_type=CapabilityType.QUERY,

                params=[        super().__init__()        super().__init__()

                    CapabilityParam(

                        "service_name",        self._boot_time = datetime.now(timezone.utc)        self._boot_time = datetime.now(timezone.utc)

                        ParamType.STRING,

                        "Name of the service to check",        if PSUTIL_AVAILABLE:        if PSUTIL_AVAILABLE:

                        required=True,

                    ),            logger.info("✅ RealMonitoringAgent initialized with psutil")            logger.info("✅ RealMonitoringAgent initialized with psutil")

                ],

                tags=["monitoring", "health"],        else:        else:

            ),

        ]            logger.warning("⚠️ psutil not available, using simulated metrics")            logger.warning("⚠️ psutil not available, using simulated metrics")



    async def handle_collect_metrics(self, include_processes: bool = False) -> AgentResponse:

        """Collect all system metrics."""

        logger.info("Collecting system metrics...")    @property    @property

        

        try:    def name(self) -> str:    def name(self) -> str:

            metrics = {

                "timestamp": datetime.now(timezone.utc).isoformat(),        return "monitoring"        return "monitoring"

                "hostname": socket.gethostname(),

                "platform": platform.system(),

                "platform_release": platform.release(),

                "data_source": "psutil" if PSUTIL_AVAILABLE else "simulated",    @property    @property

            }

                def description(self) -> str:    def description(self) -> str:

            cpu_result = await self.handle_get_cpu_info()

            if cpu_result.success:        return "Collects real system metrics (CPU, memory, disk, network) using psutil"        return "Collects real system metrics (CPU, memory, disk, network) using psutil"

                metrics["cpu"] = cpu_result.data

            

            mem_result = await self.handle_get_memory_info()

            if mem_result.success:    def get_capabilities(self) -> List[AgentCapability]:    def get_capabilities(self) -> List[AgentCapability]:

                metrics["memory"] = mem_result.data

                    return [        return [

            disk_result = await self.handle_get_disk_info()

            if disk_result.success:            AgentCapability(            AgentCapability(

                metrics["disk"] = disk_result.data

                            name="collect_metrics",                name="collect_metrics",

            net_result = await self.handle_get_network_info()

            if net_result.success:                description="Collect all system metrics (CPU, memory, disk, network)",                description="Collect all system metrics (CPU, memory, disk, network)",

                metrics["network"] = net_result.data

                            handler="handle_collect_metrics",                handler="handle_collect_metrics",

            if PSUTIL_AVAILABLE:

                boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)                capability_type=CapabilityType.QUERY,                capability_type=CapabilityType.QUERY,

                uptime_seconds = (datetime.now(timezone.utc) - boot_time).total_seconds()

                metrics["uptime_seconds"] = int(uptime_seconds)                params=[                params=[

                metrics["uptime_human"] = self._format_uptime(uptime_seconds)

                                CapabilityParam(                    CapabilityParam(

            return AgentResponse(success=True, data=metrics)

                                    "include_processes",                        "include_processes",

        except Exception as e:

            logger.error(f"Failed to collect metrics: {e}")                        ParamType.BOOLEAN,                        ParamType.BOOLEAN,

            return AgentResponse(success=False, error=str(e))

                        "Include top processes list",                        "Include top processes list",

    async def handle_get_cpu_info(self) -> AgentResponse:

        """Get CPU information."""                        required=False,                        required=False,

        if not PSUTIL_AVAILABLE:

            return self._simulated_cpu_info()                        default=False,                        default=False,

        

        try:                    ),                    ),

            cpu_percent = psutil.cpu_percent(interval=0.5)

            cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)                ],                ],

            cpu_freq = psutil.cpu_freq()

            cpu_count = psutil.cpu_count()                tags=["monitoring", "metrics", "system"],                tags=["monitoring", "metrics", "system"],

            cpu_count_logical = psutil.cpu_count(logical=True)

                        ),            ),

            data = {

                "usage_percent": cpu_percent,            AgentCapability(            AgentCapability(

                "usage_per_core": cpu_percent_per_core,

                "cores_physical": cpu_count,                name="get_cpu_info",                name="get_cpu_info",

                "cores_logical": cpu_count_logical,

                "frequency_mhz": {                description="Get detailed CPU usage information",                description="Get detailed CPU usage information",

                    "current": cpu_freq.current if cpu_freq else None,

                    "min": cpu_freq.min if cpu_freq else None,                handler="handle_get_cpu_info",                handler="handle_get_cpu_info",

                    "max": cpu_freq.max if cpu_freq else None,

                } if cpu_freq else None,                capability_type=CapabilityType.QUERY,                capability_type=CapabilityType.QUERY,

                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,

            }                params=[],                params=[],

            

            return AgentResponse(success=True, data=data)                tags=["monitoring", "cpu"],                tags=["monitoring", "cpu"],

            

        except Exception as e:            ),            ),

            return AgentResponse(success=False, error=str(e))

            AgentCapability(            AgentCapability(

    async def handle_get_memory_info(self) -> AgentResponse:

        """Get memory information."""                name="get_memory_info",                name="get_memory_info",

        if not PSUTIL_AVAILABLE:

            return self._simulated_memory_info()                description="Get RAM and swap memory usage",                description="Get RAM and swap memory usage",

        

        try:                handler="handle_get_memory_info",                handler="handle_get_memory_info",

            mem = psutil.virtual_memory()

            swap = psutil.swap_memory()                capability_type=CapabilityType.QUERY,                capability_type=CapabilityType.QUERY,

            

            data = {                params=[],                params=[],

                "ram": {

                    "total_gb": round(mem.total / (1024**3), 2),                tags=["monitoring", "memory"],                tags=["monitoring", "memory"],

                    "available_gb": round(mem.available / (1024**3), 2),

                    "used_gb": round(mem.used / (1024**3), 2),            ),            ),

                    "percent_used": mem.percent,

                },            AgentCapability(            AgentCapability(

                "swap": {

                    "total_gb": round(swap.total / (1024**3), 2),                name="get_disk_info",                name="get_disk_info",

                    "used_gb": round(swap.used / (1024**3), 2),

                    "free_gb": round(swap.free / (1024**3), 2),                description="Get disk partitions and usage statistics",                description="Get disk partitions and usage statistics",

                    "percent_used": swap.percent,

                },                handler="handle_get_disk_info",                handler="handle_get_disk_info",

            }

                            capability_type=CapabilityType.QUERY,                capability_type=CapabilityType.QUERY,

            return AgentResponse(success=True, data=data)

                            params=[                params=[

        except Exception as e:

            return AgentResponse(success=False, error=str(e))                    CapabilityParam(                    CapabilityParam(



    async def handle_get_disk_info(self) -> AgentResponse:                        "path",                        "path",

        """Get disk information."""

        if not PSUTIL_AVAILABLE:                        ParamType.STRING,                        ParamType.STRING,

            return self._simulated_disk_info()

                                "Specific path to check",                        "Specific path to check",

        try:

            partitions = []                        required=False,                        required=False,

            for partition in psutil.disk_partitions(all=False):

                try:                        default="/",                        default="/",

                    usage = psutil.disk_usage(partition.mountpoint)

                    partitions.append({                    ),                    ),

                        "device": partition.device,

                        "mountpoint": partition.mountpoint,                ],                ],

                        "fstype": partition.fstype,

                        "total_gb": round(usage.total / (1024**3), 2),                tags=["monitoring", "disk"],                tags=["monitoring", "disk"],

                        "used_gb": round(usage.used / (1024**3), 2),

                        "free_gb": round(usage.free / (1024**3), 2),            ),            ),

                        "percent_used": usage.percent,

                    })            AgentCapability(            AgentCapability(

                except (PermissionError, OSError):

                    continue                name="get_network_info",                name="get_network_info",

            

            disk_io = psutil.disk_io_counters()                description="Get network I/O statistics",                description="Get network I/O statistics",

            io_stats = None

            if disk_io:                handler="handle_get_network_info",                handler="handle_get_network_info",

                io_stats = {

                    "read_bytes": disk_io.read_bytes,                capability_type=CapabilityType.QUERY,                capability_type=CapabilityType.QUERY,

                    "write_bytes": disk_io.write_bytes,

                    "read_count": disk_io.read_count,                params=[],                params=[],

                    "write_count": disk_io.write_count,

                }                tags=["monitoring", "network"],                tags=["monitoring", "network"],

            

            data = {"partitions": partitions, "io_stats": io_stats}            ),            ),

            return AgentResponse(success=True, data=data)

                        AgentCapability(            AgentCapability(

        except Exception as e:

            return AgentResponse(success=False, error=str(e))                name="get_process_list",                name="get_process_list",



    async def handle_get_network_info(self) -> AgentResponse:                description="Get top processes by CPU or memory usage",                description="Get top processes by CPU or memory usage",

        """Get network information."""

        if not PSUTIL_AVAILABLE:                handler="handle_get_process_list",                handler="handle_get_process_list",

            return self._simulated_network_info()

                        capability_type=CapabilityType.QUERY,                capability_type=CapabilityType.QUERY,

        try:

            net_io = psutil.net_io_counters()                params=[                params=[

            net_io_per_nic = psutil.net_io_counters(pernic=True)

                                CapabilityParam(                    CapabilityParam(

            interfaces = {}

            for nic_name, counters in net_io_per_nic.items():                        "sort_by",                        "sort_by",

                interfaces[nic_name] = {

                    "bytes_sent": counters.bytes_sent,                        ParamType.STRING,                        ParamType.STRING,

                    "bytes_recv": counters.bytes_recv,

                    "packets_sent": counters.packets_sent,                        "Sort by 'cpu' or 'memory'",                        "Sort by 'cpu' or 'memory'",

                    "packets_recv": counters.packets_recv,

                }                        required=False,                        required=False,

            

            data = {                        default="cpu",                        default="cpu",

                "total": {

                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),                    ),                    ),

                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),

                    "packets_sent": net_io.packets_sent,                    CapabilityParam(                    CapabilityParam(

                    "packets_recv": net_io.packets_recv,

                },                        "limit",                        "limit",

                "interfaces": interfaces,

            }                        ParamType.INTEGER,                        ParamType.INTEGER,

            

            return AgentResponse(success=True, data=data)                        "Number of processes to return",                        "Number of processes to return",

            

        except Exception as e:                        required=False,                        required=False,

            return AgentResponse(success=False, error=str(e))

                        default=10,                        default=10,

    async def handle_check_service_health(self, service_name: str) -> AgentResponse:

        """Check if a service is running."""                    ),                    ),

        if not PSUTIL_AVAILABLE:

            return AgentResponse(                ],                ],

                success=True,

                data={"service": service_name, "running": True, "simulated": True}                tags=["monitoring", "processes"],                tags=["monitoring", "processes"],

            )

                    ),            ),

        try:

            service_name_lower = service_name.lower()            AgentCapability(            AgentCapability(

            matching = []

                            name="check_service_health",                name="check_service_health",

            for proc in psutil.process_iter(['pid', 'name', 'status']):

                try:                description="Check if a service/process is running",                description="Check if a service/process is running",

                    if service_name_lower in proc.info['name'].lower():

                        matching.append({                handler="handle_check_service_health",                handler="handle_check_service_health",

                            "pid": proc.info['pid'],

                            "name": proc.info['name'],                capability_type=CapabilityType.QUERY,                capability_type=CapabilityType.QUERY,

                            "status": proc.info['status'],

                        })                params=[                params=[

                except (psutil.NoSuchProcess, psutil.AccessDenied):

                    continue                    CapabilityParam(                    CapabilityParam(

            

            is_running = len(matching) > 0                        "service_name",                        "service_name",

            return AgentResponse(

                success=True,                        ParamType.STRING,                        ParamType.STRING,

                data={

                    "service": service_name,                        "Name of the service to check (e.g., 'nginx', 'postgres')",                        "Name of the service to check (e.g., 'nginx', 'postgres')",

                    "running": is_running,

                    "process_count": len(matching),                        required=True,                        required=True,

                    "processes": matching[:5],

                    "health_status": "healthy" if is_running else "not_found",                    ),                    ),

                }

            )                ],                ],

            

        except Exception as e:                tags=["monitoring", "health", "service"],                tags=["monitoring", "health", "service"],

            return AgentResponse(success=False, error=str(e))

            ),            ),

    def _simulated_cpu_info(self) -> AgentResponse:

        import random        ]        ]

        return AgentResponse(

            success=True,

            data={

                "usage_percent": round(random.uniform(10, 70), 1),    # =========================================================================    # =========================================================================

                "usage_per_core": [round(random.uniform(5, 80), 1) for _ in range(4)],

                "cores_physical": 4,    # HANDLERS    # HANDLERS

                "cores_logical": 8,

                "simulated": True,    # =========================================================================    # =========================================================================

            }

        )



    def _simulated_memory_info(self) -> AgentResponse:    async def handle_collect_metrics(self, include_processes: bool = False) -> AgentResponse:    async def handle_collect_metrics(self, include_processes: bool = False) -> AgentResponse:

        import random

        used = round(random.uniform(40, 80), 1)        """Collect all system metrics."""        """Collect all system metrics."""

        return AgentResponse(

            success=True,        logger.info("📊 Collecting system metrics...")        logger.info("📊 Collecting system metrics...")

            data={

                "ram": {"total_gb": 16.0, "used_gb": round(16.0 * used / 100, 2), "percent_used": used},                

                "swap": {"total_gb": 8.0, "used_gb": 1.2, "percent_used": 15.0},

                "simulated": True,        try:        try:

            }

        )            metrics = {            metrics = {



    def _simulated_disk_info(self) -> AgentResponse:                "timestamp": datetime.now(timezone.utc).isoformat(),                "timestamp": datetime.now(timezone.utc).isoformat(),

        return AgentResponse(

            success=True,                "hostname": socket.gethostname(),                "hostname": socket.gethostname(),

            data={

                "partitions": [{"device": "/dev/sda1", "mountpoint": "/", "total_gb": 500.0, "used_gb": 234.5, "percent_used": 46.9}],                "platform": platform.system(),                "platform": platform.system(),

                "simulated": True,

            }                "platform_release": platform.release(),                "platform_release": platform.release(),

        )

                "data_source": "psutil" if PSUTIL_AVAILABLE else "simulated",                "data_source": "psutil" if PSUTIL_AVAILABLE else "simulated",

    def _simulated_network_info(self) -> AgentResponse:

        return AgentResponse(            }            }

            success=True,

            data={                        

                "total": {"bytes_sent_mb": 1234.5, "bytes_recv_mb": 5678.9},

                "interfaces": {"eth0": {"bytes_sent": 1294023680, "bytes_recv": 5954904064}},            # CPU            # CPU

                "simulated": True,

            }            cpu_result = await self.handle_get_cpu_info()            cpu_result = await self.handle_get_cpu_info()

        )

            if cpu_result.success:            if cpu_result.success:

    def _format_uptime(self, seconds: float) -> str:

        days, remainder = divmod(int(seconds), 86400)                metrics["cpu"] = cpu_result.data                metrics["cpu"] = cpu_result.data

        hours, remainder = divmod(remainder, 3600)

        minutes, _ = divmod(remainder, 60)                        

        parts = []

        if days:            # Memory            # Memory

            parts.append(f"{days}d")

        if hours:            mem_result = await self.handle_get_memory_info()            mem_result = await self.handle_get_memory_info()

            parts.append(f"{hours}h")

        if minutes:            if mem_result.success:            if mem_result.success:

            parts.append(f"{minutes}m")

        return " ".join(parts) or "0m"                metrics["memory"] = mem_result.data                metrics["memory"] = mem_result.data



                        

__all__ = ["RealMonitoringAgent", "PSUTIL_AVAILABLE"]

            # Disk            # Disk

            disk_result = await self.handle_get_disk_info()            disk_result = await self.handle_get_disk_info()

            if disk_result.success:            if disk_result.success:

                metrics["disk"] = disk_result.data                metrics["disk"] = disk_result.data

                        

            # Network            # Network

            net_result = await self.handle_get_network_info()            net_result = await self.handle_get_network_info()

            if net_result.success:            if net_result.success:

                metrics["network"] = net_result.data                metrics["network"] = net_result.data

                        

            # Processes (optional)            # Processes (optional)

            if include_processes:            if include_processes:

                proc_result = await self.handle_get_process_list()                proc_result = await self.handle_get_process_list()

                if proc_result.success:                if proc_result.success:

                    metrics["top_processes"] = proc_result.data                    metrics["top_processes"] = proc_result.data

                        

            # System uptime            # System uptime

            if PSUTIL_AVAILABLE:            if PSUTIL_AVAILABLE:

                boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)                boot_time = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)

                uptime_seconds = (datetime.now(timezone.utc) - boot_time).total_seconds()                uptime_seconds = (datetime.now(timezone.utc) - boot_time).total_seconds()

                metrics["uptime_seconds"] = int(uptime_seconds)                metrics["uptime_seconds"] = int(uptime_seconds)

                metrics["uptime_human"] = self._format_uptime(uptime_seconds)                metrics["uptime_human"] = self._format_uptime(uptime_seconds)

                        

            logger.info("✅ Metrics collected successfully")            logger.info("✅ Metrics collected successfully")

            return AgentResponse(success=True, data=metrics)            return AgentResponse(success=True, data=metrics)

                        

        except Exception as e:        except Exception as e:

            logger.error(f"❌ Failed to collect metrics: {e}")            logger.error(f"❌ Failed to collect metrics: {e}")

            return AgentResponse(success=False, error=str(e))            return AgentResponse(success=False, error=str(e))



    async def handle_get_cpu_info(self) -> AgentResponse:    async def handle_get_cpu_info(self) -> AgentResponse:

        """Get CPU information."""        """Get CPU information."""

        if not PSUTIL_AVAILABLE:        if not PSUTIL_AVAILABLE:

            return self._simulated_cpu_info()            return self._simulated_cpu_info()

                

        try:        try:

            cpu_percent = psutil.cpu_percent(interval=0.5)            cpu_percent = psutil.cpu_percent(interval=0.5)

            cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)            cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)

            cpu_freq = psutil.cpu_freq()            cpu_freq = psutil.cpu_freq()

            cpu_count = psutil.cpu_count()            cpu_count = psutil.cpu_count()

            cpu_count_logical = psutil.cpu_count(logical=True)            cpu_count_logical = psutil.cpu_count(logical=True)

                        

            data = {            data = {

                "usage_percent": cpu_percent,                "usage_percent": cpu_percent,

                "usage_per_core": cpu_percent_per_core,                "usage_per_core": cpu_percent_per_core,

                "cores_physical": cpu_count,                "cores_physical": cpu_count,

                "cores_logical": cpu_count_logical,                "cores_logical": cpu_count_logical,

                "frequency_mhz": {                "frequency_mhz": {

                    "current": cpu_freq.current if cpu_freq else None,                    "current": cpu_freq.current if cpu_freq else None,

                    "min": cpu_freq.min if cpu_freq else None,                    "min": cpu_freq.min if cpu_freq else None,

                    "max": cpu_freq.max if cpu_freq else None,                    "max": cpu_freq.max if cpu_freq else None,

                } if cpu_freq else None,                } if cpu_freq else None,

                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,

            }            }

                        

            return AgentResponse(success=True, data=data)            return AgentResponse(success=True, data=data)

                        

        except Exception as e:        except Exception as e:

            return AgentResponse(success=False, error=str(e))            return AgentResponse(success=False, error=str(e))



    async def handle_get_memory_info(self) -> AgentResponse:    async def handle_get_memory_info(self) -> AgentResponse:

        """Get memory information."""        """Get memory information."""

        if not PSUTIL_AVAILABLE:        if not PSUTIL_AVAILABLE:

            return self._simulated_memory_info()            return self._simulated_memory_info()

                

        try:        try:

            mem = psutil.virtual_memory()            mem = psutil.virtual_memory()

            swap = psutil.swap_memory()            swap = psutil.swap_memory()

                        

            data = {            data = {

                "ram": {                "ram": {

                    "total_gb": round(mem.total / (1024**3), 2),                    "total_gb": round(mem.total / (1024**3), 2),

                    "available_gb": round(mem.available / (1024**3), 2),                    "available_gb": round(mem.available / (1024**3), 2),

                    "used_gb": round(mem.used / (1024**3), 2),                    "used_gb": round(mem.used / (1024**3), 2),

                    "percent_used": mem.percent,                    "percent_used": mem.percent,

                    "cached_gb": round(getattr(mem, 'cached', 0) / (1024**3), 2),                    "cached_gb": round(getattr(mem, 'cached', 0) / (1024**3), 2),

                    "buffers_gb": round(getattr(mem, 'buffers', 0) / (1024**3), 2),                    "buffers_gb": round(getattr(mem, 'buffers', 0) / (1024**3), 2),

                },                },

                "swap": {                "swap": {

                    "total_gb": round(swap.total / (1024**3), 2),                    "total_gb": round(swap.total / (1024**3), 2),

                    "used_gb": round(swap.used / (1024**3), 2),                    "used_gb": round(swap.used / (1024**3), 2),

                    "free_gb": round(swap.free / (1024**3), 2),                    "free_gb": round(swap.free / (1024**3), 2),

                    "percent_used": swap.percent,                    "percent_used": swap.percent,

                },                },

            }            }

                        

            return AgentResponse(success=True, data=data)            return AgentResponse(success=True, data=data)

                        

        except Exception as e:        except Exception as e:

            return AgentResponse(success=False, error=str(e))            return AgentResponse(success=False, error=str(e))



    async def handle_get_disk_info(self, path: str = "/") -> AgentResponse:    async def handle_get_disk_info(self, path: str = "/") -> AgentResponse:

        """Get disk information."""        """Get disk information."""

        if not PSUTIL_AVAILABLE:        if not PSUTIL_AVAILABLE:

            return self._simulated_disk_info()            return self._simulated_disk_info()

                

        try:        try:

            partitions = []            partitions = []

            for partition in psutil.disk_partitions(all=False):            for partition in psutil.disk_partitions(all=False):

                try:                try:

                    usage = psutil.disk_usage(partition.mountpoint)                    usage = psutil.disk_usage(partition.mountpoint)

                    partitions.append({                    partitions.append({

                        "device": partition.device,                        "device": partition.device,

                        "mountpoint": partition.mountpoint,                        "mountpoint": partition.mountpoint,

                        "fstype": partition.fstype,                        "fstype": partition.fstype,

                        "total_gb": round(usage.total / (1024**3), 2),                        "total_gb": round(usage.total / (1024**3), 2),

                        "used_gb": round(usage.used / (1024**3), 2),                        "used_gb": round(usage.used / (1024**3), 2),

                        "free_gb": round(usage.free / (1024**3), 2),                        "free_gb": round(usage.free / (1024**3), 2),

                        "percent_used": usage.percent,                        "percent_used": usage.percent,

                    })                    })

                except (PermissionError, OSError):                except (PermissionError, OSError):

                    continue                    continue

                        

            # Disk I/O            # Disk I/O

            disk_io = psutil.disk_io_counters()            disk_io = psutil.disk_io_counters()

            io_stats = None            io_stats = None

            if disk_io:            if disk_io:

                io_stats = {                io_stats = {

                    "read_bytes": disk_io.read_bytes,                    "read_bytes": disk_io.read_bytes,

                    "write_bytes": disk_io.write_bytes,                    "write_bytes": disk_io.write_bytes,

                    "read_count": disk_io.read_count,                    "read_count": disk_io.read_count,

                    "write_count": disk_io.write_count,                    "write_count": disk_io.write_count,

                }                }

                        

            data = {            data = {

                "partitions": partitions,                "partitions": partitions,

                "io_stats": io_stats,                "io_stats": io_stats,

            }            }

                        

            return AgentResponse(success=True, data=data)            return AgentResponse(success=True, data=data)

                        

        except Exception as e:        except Exception as e:

            return AgentResponse(success=False, error=str(e))            return AgentResponse(success=False, error=str(e))



    async def handle_get_network_info(self) -> AgentResponse:    async def handle_get_network_info(self) -> AgentResponse:

        """Get network information."""        """Get network information."""

        if not PSUTIL_AVAILABLE:        if not PSUTIL_AVAILABLE:

            return self._simulated_network_info()            return self._simulated_network_info()

                

        try:        try:

            net_io = psutil.net_io_counters()            net_io = psutil.net_io_counters()

            net_io_per_nic = psutil.net_io_counters(pernic=True)            net_io_per_nic = psutil.net_io_counters(pernic=True)

                        

            interfaces = {}            interfaces = {}

            for nic_name, counters in net_io_per_nic.items():            for nic_name, counters in net_io_per_nic.items():

                interfaces[nic_name] = {                interfaces[nic_name] = {

                    "bytes_sent": counters.bytes_sent,                    "bytes_sent": counters.bytes_sent,

                    "bytes_recv": counters.bytes_recv,                    "bytes_recv": counters.bytes_recv,

                    "packets_sent": counters.packets_sent,                    "packets_sent": counters.packets_sent,

                    "packets_recv": counters.packets_recv,                    "packets_recv": counters.packets_recv,

                    "errors_in": counters.errin,                    "errors_in": counters.errin,

                    "errors_out": counters.errout,                    "errors_out": counters.errout,

                }                }

                        

            # Network connections            # Network connections

            connections = []            connections = []

            try:            try:

                for conn in psutil.net_connections(kind='inet')[:20]:  # Limit to 20                for conn in psutil.net_connections(kind='inet')[:20]:  # Limit to 20

                    connections.append({                    connections.append({

                        "type": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",                        "type": "TCP" if conn.type == socket.SOCK_STREAM else "UDP",

                        "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,                        "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,

                        "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,                        "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,

                        "status": conn.status if hasattr(conn, 'status') else None,                        "status": conn.status if hasattr(conn, 'status') else None,

                    })                    })

            except (PermissionError, psutil.AccessDenied):            except (PermissionError, psutil.AccessDenied):

                pass                pass

                        

            data = {            data = {

                "total": {                "total": {

                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),                    "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),

                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),                    "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),

                    "packets_sent": net_io.packets_sent,                    "packets_sent": net_io.packets_sent,

                    "packets_recv": net_io.packets_recv,                    "packets_recv": net_io.packets_recv,

                },                },

                "interfaces": interfaces,                "interfaces": interfaces,

                "active_connections": connections,                "active_connections": connections,

            }            }

                        

            return AgentResponse(success=True, data=data)            return AgentResponse(success=True, data=data)

                        

        except Exception as e:        except Exception as e:

            return AgentResponse(success=False, error=str(e))            return AgentResponse(success=False, error=str(e))



    async def handle_get_process_list(    async def handle_get_process_list(

        self, sort_by: str = "cpu", limit: int = 10        self, sort_by: str = "cpu", limit: int = 10

    ) -> AgentResponse:    ) -> AgentResponse:

        """Get top processes."""        """Get top processes."""

        if not PSUTIL_AVAILABLE:        if not PSUTIL_AVAILABLE:

            return self._simulated_process_list()            return self._simulated_process_list()

                

        try:        try:

            processes = []            processes = []

            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):

                try:                try:

                    info = proc.info                    info = proc.info

                    processes.append({                    processes.append({

                        "pid": info['pid'],                        "pid": info['pid'],

                        "name": info['name'],                        "name": info['name'],

                        "cpu_percent": info['cpu_percent'] or 0,                        "cpu_percent": info['cpu_percent'] or 0,

                        "memory_percent": round(info['memory_percent'] or 0, 2),                        "memory_percent": round(info['memory_percent'] or 0, 2),

                        "status": info['status'],                        "status": info['status'],

                    })                    })

                except (psutil.NoSuchProcess, psutil.AccessDenied):                except (psutil.NoSuchProcess, psutil.AccessDenied):

                    continue                    continue

                        

            # Sort            # Sort

            sort_key = "cpu_percent" if sort_by == "cpu" else "memory_percent"            sort_key = "cpu_percent" if sort_by == "cpu" else "memory_percent"

            processes.sort(key=lambda x: x[sort_key], reverse=True)            processes.sort(key=lambda x: x[sort_key], reverse=True)

                        

            data = {            data = {

                "processes": processes[:limit],                "processes": processes[:limit],

                "total_count": len(processes),                "total_count": len(processes),

                "sort_by": sort_by,                "sort_by": sort_by,

            }            }

                        

            return AgentResponse(success=True, data=data)            return AgentResponse(success=True, data=data)

                        

        except Exception as e:        except Exception as e:

            return AgentResponse(success=False, error=str(e))            return AgentResponse(success=False, error=str(e))



    async def handle_check_service_health(self, service_name: str) -> AgentResponse:    async def handle_check_service_health(self, service_name: str) -> AgentResponse:

        """Check if a service is running."""        """Check if a service is running."""

        if not PSUTIL_AVAILABLE:        if not PSUTIL_AVAILABLE:

            return AgentResponse(            return AgentResponse(

                success=True,                success=True,

                data={                data={

                    "service": service_name,                    "service": service_name,

                    "running": True,                    "running": True,

                    "simulated": True,                    "simulated": True,

                    "message": "psutil not available, returning simulated status"                    "message": "psutil not available, returning simulated status"

                }                }

            )            )

                

        try:        try:

            service_name_lower = service_name.lower()            service_name_lower = service_name.lower()

            matching_processes = []            matching_processes = []

                        

            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):            for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):

                try:                try:

                    if service_name_lower in proc.info['name'].lower():                    if service_name_lower in proc.info['name'].lower():

                        matching_processes.append({                        matching_processes.append({

                            "pid": proc.info['pid'],                            "pid": proc.info['pid'],

                            "name": proc.info['name'],                            "name": proc.info['name'],

                            "status": proc.info['status'],                            "status": proc.info['status'],

                            "cpu_percent": proc.info['cpu_percent'],                            "cpu_percent": proc.info['cpu_percent'],

                            "memory_percent": round(proc.info['memory_percent'] or 0, 2),                            "memory_percent": round(proc.info['memory_percent'] or 0, 2),

                        })                        })

                except (psutil.NoSuchProcess, psutil.AccessDenied):                except (psutil.NoSuchProcess, psutil.AccessDenied):

                    continue                    continue

                        

            is_running = len(matching_processes) > 0            is_running = len(matching_processes) > 0

                        

            data = {            data = {

                "service": service_name,                "service": service_name,

                "running": is_running,                "running": is_running,

                "process_count": len(matching_processes),                "process_count": len(matching_processes),

                "processes": matching_processes[:5],  # Limit to 5                "processes": matching_processes[:5],  # Limit to 5

                "health_status": "healthy" if is_running else "not_found",                "health_status": "healthy" if is_running else "not_found",

            }            }

                        

            return AgentResponse(success=True, data=data)            return AgentResponse(success=True, data=data)

                        

        except Exception as e:        except Exception as e:

            return AgentResponse(success=False, error=str(e))            return AgentResponse(success=False, error=str(e))



    # =========================================================================    # =========================================================================

    # SIMULATED DATA (fallback when psutil not available)    # SIMULATED DATA (fallback when psutil not available)

    # =========================================================================    # =========================================================================



    def _simulated_cpu_info(self) -> AgentResponse:    def _simulated_cpu_info(self) -> AgentResponse:

        """Return simulated CPU data."""        """Return simulated CPU data."""

        import random        import random

        return AgentResponse(        return AgentResponse(

            success=True,            success=True,

            data={            data={

                "usage_percent": round(random.uniform(10, 70), 1),                "usage_percent": round(random.uniform(10, 70), 1),

                "usage_per_core": [round(random.uniform(5, 80), 1) for _ in range(4)],                "usage_per_core": [round(random.uniform(5, 80), 1) for _ in range(4)],

                "cores_physical": 4,                "cores_physical": 4,

                "cores_logical": 8,                "cores_logical": 8,

                "frequency_mhz": {"current": 2400, "min": 800, "max": 3600},                "frequency_mhz": {"current": 2400, "min": 800, "max": 3600},

                "simulated": True,                "simulated": True,

            }            }

        )        )



    def _simulated_memory_info(self) -> AgentResponse:    def _simulated_memory_info(self) -> AgentResponse:

        """Return simulated memory data."""        """Return simulated memory data."""

        import random        import random

        used_percent = round(random.uniform(40, 80), 1)        used_percent = round(random.uniform(40, 80), 1)

        return AgentResponse(        return AgentResponse(

            success=True,            success=True,

            data={            data={

                "ram": {                "ram": {

                    "total_gb": 16.0,                    "total_gb": 16.0,

                    "available_gb": round(16.0 * (100 - used_percent) / 100, 2),                    "available_gb": round(16.0 * (100 - used_percent) / 100, 2),

                    "used_gb": round(16.0 * used_percent / 100, 2),                    "used_gb": round(16.0 * used_percent / 100, 2),

                    "percent_used": used_percent,                    "percent_used": used_percent,

                },                },

                "swap": {                "swap": {

                    "total_gb": 8.0,                    "total_gb": 8.0,

                    "used_gb": 1.2,                    "used_gb": 1.2,

                    "free_gb": 6.8,                    "free_gb": 6.8,

                    "percent_used": 15.0,                    "percent_used": 15.0,

                },                },

                "simulated": True,                "simulated": True,

            }            }

        )        )



    def _simulated_disk_info(self) -> AgentResponse:    def _simulated_disk_info(self) -> AgentResponse:

        """Return simulated disk data."""        """Return simulated disk data."""

        return AgentResponse(        return AgentResponse(

            success=True,            success=True,

            data={            data={

                "partitions": [                "partitions": [

                    {                    {

                        "device": "/dev/sda1",                        "device": "/dev/sda1",

                        "mountpoint": "/",                        "mountpoint": "/",

                        "fstype": "ext4",                        "fstype": "ext4",

                        "total_gb": 500.0,                        "total_gb": 500.0,

                        "used_gb": 234.5,                        "used_gb": 234.5,

                        "free_gb": 265.5,                        "free_gb": 265.5,

                        "percent_used": 46.9,                        "percent_used": 46.9,

                    }                    }

                ],                ],

                "simulated": True,                "simulated": True,

            }            }

        )        )



    def _simulated_network_info(self) -> AgentResponse:    def _simulated_network_info(self) -> AgentResponse:

        """Return simulated network data."""        """Return simulated network data."""

        return AgentResponse(        return AgentResponse(

            success=True,            success=True,

            data={            data={

                "total": {                "total": {

                    "bytes_sent_mb": 1234.5,                    "bytes_sent_mb": 1234.5,

                    "bytes_recv_mb": 5678.9,                    "bytes_recv_mb": 5678.9,

                    "packets_sent": 123456,                    "packets_sent": 123456,

                    "packets_recv": 789012,                    "packets_recv": 789012,

                },                },

                "interfaces": {                "interfaces": {

                    "eth0": {                    "eth0": {

                        "bytes_sent": 1294023680,                        "bytes_sent": 1294023680,

                        "bytes_recv": 5954904064,                        "bytes_recv": 5954904064,

                        "packets_sent": 123456,                        "packets_sent": 123456,

                        "packets_recv": 789012,                        "packets_recv": 789012,

                    }                    }

                },                },

                "simulated": True,                "simulated": True,

            }            }

        )        )



    def _simulated_process_list(self) -> AgentResponse:    def _simulated_process_list(self) -> AgentResponse:

        """Return simulated process list."""        """Return simulated process list."""

        return AgentResponse(        return AgentResponse(

            success=True,            success=True,

            data={            data={

                "processes": [                "processes": [

                    {"pid": 1, "name": "systemd", "cpu_percent": 0.1, "memory_percent": 0.5, "status": "running"},                    {"pid": 1, "name": "systemd", "cpu_percent": 0.1, "memory_percent": 0.5, "status": "running"},

                    {"pid": 1234, "name": "python", "cpu_percent": 15.2, "memory_percent": 3.4, "status": "running"},                    {"pid": 1234, "name": "python", "cpu_percent": 15.2, "memory_percent": 3.4, "status": "running"},

                    {"pid": 5678, "name": "postgres", "cpu_percent": 8.7, "memory_percent": 12.3, "status": "running"},                    {"pid": 5678, "name": "postgres", "cpu_percent": 8.7, "memory_percent": 12.3, "status": "running"},

                ],                ],

                "total_count": 150,                "total_count": 150,

                "simulated": True,                "simulated": True,

            }            }

        )        )



    def _format_uptime(self, seconds: float) -> str:    def _format_uptime(self, seconds: float) -> str:

        """Format uptime in human readable format."""        """Format uptime in human readable format."""

        days, remainder = divmod(int(seconds), 86400)        days, remainder = divmod(int(seconds), 86400)

        hours, remainder = divmod(remainder, 3600)        hours, remainder = divmod(remainder, 3600)

        minutes, _ = divmod(remainder, 60)        minutes, _ = divmod(remainder, 60)

                

        parts = []        parts = []

        if days:        if days:

            parts.append(f"{days}d")            parts.append(f"{days}d")

        if hours:        if hours:

            parts.append(f"{hours}h")            parts.append(f"{hours}h")

        if minutes:        if minutes:

            parts.append(f"{minutes}m")            parts.append(f"{minutes}m")

                

        return " ".join(parts) or "0m"        return " ".join(parts) or "0m"





__all__ = ["RealMonitoringAgent", "PSUTIL_AVAILABLE"]__all__ = ["RealMonitoringAgent", "PSUTIL_AVAILABLE"]

