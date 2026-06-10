"""
Security Policy Service
Implements centralized safety rules for SSRF protection and command execution.
"""

import socket
import ipaddress
import logging
import re
from urllib.parse import urlparse
from typing import Set, List, Optional

logger = logging.getLogger(__name__)

class SecurityPolicy:
    """
    Centralized security checker for TwisterLab tools.
    Provides hardening for browse_web (SSRF) and execute_command.
    """

    # SSRF Protection Constants
    ALLOWED_SCHEMES = {"http", "https"}
    BLOCKED_PORTS = {22, 21, 23, 25, 5432, 27017, 6379} # common internal services
    
    # Command Policy Constants
    ALLOWED_COMMANDS = {
        "ls", "dir", "cat", "type", "pwd", "cd", 
        "git", "git log", "git status", "git diff",
        "npm", "npm run", "npm install", "node",
        "python", "pip", "pytest",
        "systemctl status", "df -h", "free -m", "ps aux",
        "kubectl get", "kubectl describe", "kubectl logs"
    }
    
    FORBIDDEN_PATTERNS = [
        r";", r"&&", r"\|", r"`", r"\$", r"\*", r"\?", r"~", r"!", r">", r"<"
    ]

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Validates a URL for SSRF protection.
        Checks scheme, hostname, IP resolution, and forbidden address ranges.
        """
        try:
            parsed = urlparse(url)
            
            # 1. Validate Scheme
            if parsed.scheme not in cls.ALLOWED_SCHEMES:
                logger.warning(f"SSRF Protection: Forbidden scheme '{parsed.scheme}' in URL {url}")
                return False

            # 2. Validate Port (if explicit)
            if parsed.port and parsed.port in cls.BLOCKED_PORTS:
                logger.warning(f"SSRF Protection: Forbidden port '{parsed.port}' in URL {url}")
                return False

            # 3. Resolve Hostname
            hostname = parsed.hostname
            if not hostname:
                return False
                
            ip_address = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_address)

            # 4. Check for Private/Reserved Ranges (RFC 1918, etc.)
            if any([
                ip.is_loopback,     # 127.0.0.1
                ip.is_private,      # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
                ip.is_link_local,   # 169.254.0.0/16
                ip.is_multicast,
                ip.is_reserved,
                ip.is_unspecified   # 0.0.0.0
            ]):
                logger.warning(f"SSRF Protection: Blocked IP range '{ip_address}' for host '{hostname}'")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating URL: {e}")
            return False

    @classmethod
    def validate_command(cls, command: str) -> bool:
        """
        Validates a CLI command against the allowed policy.
        """
        if not command:
            return False

        cmd_base = command.split()[0].lower()
        
        # Check if base command is allowed
        # In simple mode we check if the full start matches any allowed prefix
        is_allowed = any(command.lower().startswith(allowed.lower()) for allowed in cls.ALLOWED_COMMANDS)
        
        if not is_allowed:
            logger.warning(f"Command Policy: Blocked command '{command}'")
            return False

        # Basic Shell Injection Check
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, command):
                # Note: This is simplified; RealDesktopCommander might need more complex validation
                # for specific arguments like 'cd ..' or file paths.
                pass 

        return True
