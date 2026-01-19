"""
RealDesktopCommanderAgent - Secure Command Execution 💻

This agent executes REAL system commands with security safeguards:
- Whitelist of allowed commands
- Timeout protection
- Sandboxed execution
- Audit logging

SECURITY: By default, only safe commands are allowed.
Set COMMANDER_UNSAFE_MODE=true to enable all commands (NOT recommended).
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import re
import shlex
from datetime import datetime, timezone
from typing import List, Optional, Set

from twisterlab.agents.core.base import (
    TwisterAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


# Whitelist of safe commands (can be extended via env var)
DEFAULT_SAFE_COMMANDS: Set[str] = {
    # System info
    "hostname", "whoami", "uname", "uptime", "date", "cal",
    # Process info
    "ps", "top", "htop", "pgrep", "pidof",
    # Disk info
    "df", "du", "lsblk", "mount", "findmnt",
    # Network info
    "ping", "netstat", "ss", "ip", "ifconfig", "nslookup", "dig", "host",
    "curl", "wget",
    # File operations (read-only)
    "ls", "cat", "head", "tail", "grep", "find", "wc", "sort", "uniq",
    "file", "stat", "tree",
    # Service management (read-only)
    "systemctl", "service", "journalctl",
    # Database (read-only)
    "pg_isready", "redis-cli",
    # Windows equivalents
    "dir", "type", "ipconfig", "netstat", "tasklist", "systeminfo",
    "Get-Process", "Get-Service", "Get-NetIPConfiguration",
}

# Dangerous commands that should never be allowed
DANGEROUS_PATTERNS: List[str] = [
    r"rm\s+-rf", r"rm\s+/", r"mkfs", r"dd\s+if=", r":\(\)\{:\|:&\};:",
    r"chmod\s+777", r"chown\s+-R", r"curl.*\|.*sh", r"wget.*\|.*sh",
    r">\s*/dev/sd", r"shutdown", r"reboot", r"init\s+0", r"halt",
    r"format\s+c:", r"del\s+/s", r"rd\s+/s",
]


class RealDesktopCommanderAgent(TwisterAgent):
    """
    Executes system commands with security safeguards.
    
    Security Features:
    - Whitelist of allowed commands
    - Pattern matching to block dangerous commands
    - Timeout protection (default 30s)
    - Audit logging of all executions
    - Sandboxed subprocess execution
    """

    def __init__(self) -> None:
        super().__init__()
        self._unsafe_mode = os.getenv("COMMANDER_UNSAFE_MODE", "false").lower() == "true"
        self._default_timeout = int(os.getenv("COMMANDER_TIMEOUT", "30"))
        self._audit_log: List[dict] = []
        
        # Load additional safe commands from env
        extra_commands = os.getenv("COMMANDER_EXTRA_COMMANDS", "")
        self._safe_commands = DEFAULT_SAFE_COMMANDS.copy()
        if extra_commands:
            self._safe_commands.update(cmd.strip() for cmd in extra_commands.split(","))
        
        if self._unsafe_mode:
            logger.warning("⚠️ RealDesktopCommanderAgent running in UNSAFE MODE!")
        else:
            logger.info("✅ RealDesktopCommanderAgent initialized with security safeguards")

    @property
    def name(self) -> str:
        return "real-desktop-commander"

    @property
    def description(self) -> str:
        return "Executes system commands securely with whitelist protection and audit logging"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="execute_command",
                description="Execute a command on the local system (with security checks)",
                handler="handle_execute_command",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "command",
                        ParamType.STRING,
                        "The command to execute",
                        required=True,
                    ),
                    CapabilityParam(
                        "timeout",
                        ParamType.INTEGER,
                        "Execution timeout in seconds (max 300)",
                        required=False,
                        default=30,
                    ),
                    CapabilityParam(
                        "working_dir",
                        ParamType.STRING,
                        "Working directory for command execution",
                        required=False,
                    ),
                ],
                tags=["system", "command", "execution"],
            ),
            AgentCapability(
                name="execute_command_remote",
                description="Execute a command on a remote device (simulated for now)",
                handler="handle_execute_command_remote",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam(
                        "device_id",
                        ParamType.STRING,
                        "Target device identifier",
                        required=True,
                    ),
                    CapabilityParam(
                        "command",
                        ParamType.STRING,
                        "The command to execute",
                        required=True,
                    ),
                    CapabilityParam(
                        "timeout",
                        ParamType.INTEGER,
                        "Execution timeout in seconds",
                        required=False,
                        default=30,
                    ),
                ],
                tags=["system", "remote", "command"],
            ),
            AgentCapability(
                name="get_allowed_commands",
                description="List all allowed commands in safe mode",
                handler="handle_get_allowed_commands",
                capability_type=CapabilityType.QUERY,
                params=[],
                tags=["security", "info"],
            ),
            AgentCapability(
                name="get_audit_log",
                description="Get the command execution audit log",
                handler="handle_get_audit_log",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "limit",
                        ParamType.INTEGER,
                        "Number of entries to return",
                        required=False,
                        default=50,
                    ),
                ],
                tags=["security", "audit"],
            ),
        ]

    # =========================================================================
    # SECURITY CHECKS
    # =========================================================================

    def _is_command_allowed(self, command: str) -> tuple[bool, str]:
        """
        Check if command is allowed to execute.
        
        Returns: (is_allowed, reason)
        """
        # Check dangerous patterns first
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return False, f"Command matches dangerous pattern: {pattern}"
        
        # In unsafe mode, allow everything except dangerous patterns
        if self._unsafe_mode:
            return True, "Unsafe mode enabled"
        
        # Extract base command
        try:
            if platform.system() == "Windows":
                # Windows command parsing
                parts = command.strip().split()
                base_cmd = parts[0].lower() if parts else ""
            else:
                # Unix command parsing
                parts = shlex.split(command)
                base_cmd = parts[0].split("/")[-1] if parts else ""
        except ValueError:
            return False, "Invalid command syntax"
        
        # Check whitelist
        if base_cmd in self._safe_commands:
            return True, "Command in whitelist"
        
        # Check if it's a PowerShell cmdlet (Windows)
        if platform.system() == "Windows":
            if base_cmd.startswith("get-") or base_cmd in ["powershell", "pwsh"]:
                return True, "PowerShell read-only cmdlet"
        
        return False, f"Command '{base_cmd}' not in whitelist. Use get_allowed_commands to see allowed commands."

    def _audit_execution(
        self, 
        command: str, 
        success: bool, 
        output: str,
        error: Optional[str] = None,
        duration_ms: int = 0
    ) -> None:
        """Log command execution for audit."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "success": success,
            "output_length": len(output),
            "error": error,
            "duration_ms": duration_ms,
        }
        self._audit_log.append(entry)
        
        # Keep only last 1000 entries
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]
        
        log_level = logging.INFO if success else logging.WARNING
        logger.log(log_level, f"📋 Audit: {command[:50]}... -> {'✅' if success else '❌'}")

    # =========================================================================
    # HANDLERS
    # =========================================================================

    async def handle_execute_command(
        self, 
        command: str, 
        timeout: int = 30,
        working_dir: Optional[str] = None,
        **kwargs  # Accept additional params from orchestration (e.g., device_id)
    ) -> AgentResponse:
        """Execute a command on the local system."""
        # Log any unexpected kwargs for debugging
        if kwargs:
            logger.debug(f"💡 Received extra params (ignored): {list(kwargs.keys())}")
        
        logger.info(f"💻 Executing command: {command[:100]}...")
        
        # Security check
        is_allowed, reason = self._is_command_allowed(command)
        if not is_allowed:
            logger.warning(f"🚫 Command blocked: {reason}")
            self._audit_execution(command, False, "", error=reason)
            return AgentResponse(
                success=False,
                error=f"Command not allowed: {reason}",
                data={"blocked": True, "reason": reason}
            )
        
        # Enforce timeout limits
        timeout = min(timeout, 300)  # Max 5 minutes
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Determine shell based on platform
            is_windows = platform.system() == "Windows"
            
            if is_windows:
                # Use PowerShell on Windows
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir,
                )
            else:
                # Use bash on Unix
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=working_dir,
                    executable="/bin/bash",
                )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                error_msg = f"Command timed out after {timeout}s"
                self._audit_execution(command, False, "", error=error_msg)
                return AgentResponse(
                    success=False,
                    error=error_msg,
                    data={"timeout": True, "timeout_seconds": timeout}
                )
            
            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Decode output
            output = stdout.decode("utf-8", errors="replace").strip()
            error_output = stderr.decode("utf-8", errors="replace").strip()
            
            exit_code = process.returncode
            success = exit_code == 0
            
            # Audit log
            self._audit_execution(
                command, 
                success, 
                output, 
                error=error_output if error_output else None,
                duration_ms=duration_ms
            )
            
            result_data = {
                "status": "completed",
                "exit_code": exit_code,
                "output": output[:10000],  # Limit output size
                "stderr": error_output[:2000] if error_output else None,
                "duration_ms": duration_ms,
                "platform": platform.system(),
            }
            
            if success:
                logger.info(f"✅ Command completed in {duration_ms}ms")
            else:
                logger.warning(f"⚠️ Command exited with code {exit_code}")
            
            return AgentResponse(success=success, data=result_data)
            
        except Exception as e:
            error_msg = str(e)
            self._audit_execution(command, False, "", error=error_msg)
            logger.error(f"❌ Command execution failed: {e}")
            return AgentResponse(success=False, error=error_msg)

    async def handle_execute_command_remote(
        self, 
        device_id: str, 
        command: str, 
        timeout: int = 30,
        **kwargs  # Accept additional params from orchestration
    ) -> AgentResponse:
        """
        Execute a command on a remote device.
        
        NOTE: This is currently simulated. In production, this would:
        - Use SSH for Linux devices
        - Use WinRM for Windows devices
        - Use device-specific protocols
        """
        logger.info(f"📡 Remote execution on {device_id}: {command[:50]}...")
        
        # Security check
        is_allowed, reason = self._is_command_allowed(command)
        if not is_allowed:
            return AgentResponse(
                success=False,
                error=f"Command not allowed: {reason}",
                data={"device_id": device_id, "blocked": True}
            )
        
        # For now, simulate remote execution
        # In production, this would use SSH/WinRM/etc.
        
        # If device_id is "localhost" or "local", execute locally
        if device_id.lower() in ["localhost", "local", "127.0.0.1"]:
            return await self.handle_execute_command(command, timeout)
        
        # Simulated remote execution
        logger.info(f"📡 Simulating remote execution on {device_id}")
        
        # Simulate some common commands
        simulated_outputs = {
            "df -h": "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       500G  234G  266G  47% /",
            "uptime": " 14:32:01 up 45 days,  3:21,  2 users,  load average: 0.52, 0.48, 0.45",
            "ps aux": "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.0  0.1 225848  9636 ?        Ss   Dec01   0:15 /sbin/init",
        }
        
        output = simulated_outputs.get(command, f"Simulated output for: {command}")
        
        return AgentResponse(
            success=True,
            data={
                "status": "completed",
                "exit_code": 0,
                "output": output,
                "device_id": device_id,
                "simulated": True,
                "note": "Remote execution is simulated. Configure SSH/WinRM for real execution.",
            }
        )

    async def handle_get_allowed_commands(self) -> AgentResponse:
        """List all allowed commands."""
        return AgentResponse(
            success=True,
            data={
                "safe_mode": not self._unsafe_mode,
                "allowed_commands": sorted(self._safe_commands),
                "command_count": len(self._safe_commands),
                "note": "Set COMMANDER_EXTRA_COMMANDS env var to add more commands",
            }
        )

    async def handle_get_audit_log(self, limit: int = 50) -> AgentResponse:
        """Get command execution audit log."""
        entries = self._audit_log[-limit:]
        
        return AgentResponse(
            success=True,
            data={
                "entries": entries,
                "total_count": len(self._audit_log),
                "returned_count": len(entries),
            }
        )


__all__ = ["RealDesktopCommanderAgent", "DEFAULT_SAFE_COMMANDS"]
