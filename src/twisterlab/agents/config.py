"""
TwisterLab Agent Configuration
Centralizes all agent settings, Ollama configuration, and model assignments.
"""

import os

# ===========================
# OLLAMA CONFIGURATION
# ===========================

# Ollama URL - PRIMARY (Corertx RTX 3060 12GB)
# For local testing: export OLLAMA_URL=http://localhost:11434
# For production: uses corertx (192.168.0.20:11434) with GPU acceleration
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL") or os.getenv(
    "OLLAMA_URL", "http://192.168.0.20:11434"
)

# Ollama FALLBACK - BACKUP (Edgeserver GTX 1050 2GB)
# If PRIMARY fails, automatically failover to BACKUP for continuity
OLLAMA_FALLBACK = os.getenv("OLLAMA_FALLBACK", "http://192.168.0.30:11434")

OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# Model Selection Strategy
# After performance testing on GTX 1050:
# - llama3.2:1b: 2-7s (FAST, good quality)
# - phi3:mini: 69s (SLOW, excellent quality but impractical)
# - tinyllama: 2.9s (FAST but doesn't follow instructions)
#
# DECISION: Use llama3.2:1b for ALL tasks (best speed/quality trade-off)

OLLAMA_MODELS = {
    "classifier": "llama3.2:1b",  # Fast ticket classification (6.9s tested)
    "resolver": "llama3.2:1b",  # SOP generation (2.6s tested)
    "commander": "llama3.2:1b",  # Command validation (2-3s expected)
    "monitoring": "llama3.2:1b",  # Metric analysis
    "general": "llama3.2:1b",  # Fallback for any agent
}

# ===========================
# OLLAMA GENERATION OPTIONS
# ===========================

# Optimized for GTX 1050 (2GB VRAM) + speed + accuracy
OLLAMA_OPTIONS = {
    "classifier": {
        "temperature": 0.1,  # Very deterministic (consistent categories)
        "num_predict": 10,  # Short answers only (1 word)
        "top_p": 0.9,
        "stop": ["\n", ".", "Category:", "Answer:"],
    },
    "resolver": {
        "temperature": 0.3,  # Slightly creative (varied SOPs)
        "num_predict": 200,  # Detailed troubleshooting steps
        "top_p": 0.95,
        "repeat_penalty": 1.1,  # Avoid repetition
    },
    "commander": {
        "temperature": 0.0,  # Absolutely deterministic (safety critical)
        "num_predict": 50,  # Enough for YES/NO answer with reasoning
        "top_p": 1.0,
        # NO stop tokens - let it generate YES or NO fully
    },
    "monitoring": {
        "temperature": 0.2,  # Mostly deterministic
        "num_predict": 100,  # Medium-length analysis
        "top_p": 0.9,
    },
}

# ===========================
# AGENT SETTINGS
# ===========================

# Classification categories
VALID_TICKET_CATEGORIES = [
    "network",  # WiFi, Ethernet, VPN, DNS, connectivity
    "software",  # Applications, updates, licenses, crashes
    "hardware",  # Devices, peripherals, screens, printers
    "security",  # Passwords, access, permissions, malware
    "performance",  # Slow computer, lag, freezing
    "database",  # SQL errors, connection issues, data corruption
    "email",  # Outlook, SMTP, spam, attachments
    "other",  # Anything not fitting above
]

# Agent routing map (category -> responsible agent)
AGENT_ROUTING_MAP = {
    "network": "desktop_commander",  # Network diagnostics (ping, ipconfig, etc.)
    "software": "resolver",  # Software troubleshooting SOPs
    "hardware": "resolver",  # Hardware replacement/repair SOPs
    "security": "resolver",  # Security policies and procedures
    "performance": "desktop_commander",  # Performance diagnostics (tasklist, systeminfo)
    "database": "resolver",  # Database recovery SOPs
    "email": "resolver",  # Email configuration SOPs
    "other": "resolver",  # Default to resolver for unknown
}

# Safe command whitelist (fallback if LLM fails)
SAFE_COMMANDS_WHITELIST = [
    "ipconfig",
    "ping",
    "tracert",
    "nslookup",
    "systeminfo",
    "tasklist",
    "netstat",
    "hostname",
    "whoami",
    "ver",
]

# Static SOPs (fallback if LLM fails)
STATIC_SOPS = {
    "network": [
        "Check network cable connection",
        "Verify IP configuration (ipconfig /all)",
        "Ping default gateway (ping 192.168.0.1)",
        "Flush DNS cache (ipconfig /flushdns)",
        "Test with another device on same network",
    ],
    "software": [
        "Restart the application",
        "Check for software updates",
        "Verify license activation",
        "Reinstall the application",
        "Contact software vendor support",
    ],
    "hardware": [
        "Check physical connections",
        "Restart the device",
        "Update device drivers",
        "Test with different hardware",
        "Contact hardware vendor support",
    ],
    "security": [
        "Reset user password via Active Directory",
        "Verify user permissions",
        "Run antivirus scan",
        "Check firewall rules",
        "Review security logs",
    ],
    "performance": [
        "Check CPU usage (Task Manager)",
        "Check RAM usage (Task Manager)",
        "Check disk space (This PC)",
        "Restart the computer",
        "Run disk cleanup",
    ],
    "database": [
        "Check database connection string",
        "Verify SQL Server service is running",
        "Test with SQL Management Studio",
        "Review database error logs",
        "Contact database administrator",
    ],
    "email": [
        "Verify email credentials",
        "Check Outlook connectivity",
        "Test SMTP/IMAP settings",
        "Clear Outlook cache",
        "Recreate Outlook profile",
    ],
    "other": [
        "Contact IT helpdesk for assistance",
        "Provide detailed error message",
        "Include screenshot if possible",
    ],
}

# ===========================
# PERFORMANCE SETTINGS
# ===========================

# LLM timeouts (seconds)
LLM_TIMEOUTS = {
    "classifier": 15,  # Classification should be fast
    "resolver": 60,  # SOP generation can take longer
    "commander": 20,  # Validation should be quick
    "monitoring": 30,  # Analysis medium time
}

# Retry settings
LLM_MAX_RETRIES = 2
LLM_RETRY_DELAY = 2  # seconds

# ===========================
# LOGGING & MONITORING
# ===========================

# Log LLM performance metrics
LOG_LLM_METRICS = True

# Metric names for Prometheus
METRICS_LLM_DURATION = "twisterlab_llm_duration_seconds"
METRICS_LLM_TOKENS = "twisterlab_llm_tokens_total"
METRICS_LLM_ERRORS = "twisterlab_llm_errors_total"
METRICS_LLM_FALLBACKS = "twisterlab_llm_fallbacks_total"
