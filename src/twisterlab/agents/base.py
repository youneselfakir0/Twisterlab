"""
TwisterLab Base Agent with Multi-Framework Schema Export.

Provides schema compatibility with:
- Microsoft Agent Framework
- LangChain Agents
- Semantic Kernel
- OpenAI Assistants API
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class TwisterAgent(ABC):
    """
    Base class for all TwisterLab agents with multi-framework export support.

    Attributes:
        name: Agent unique identifier
        display_name: Human-readable agent name
        description: Agent purpose and capabilities
        role: Agent role in the system
        instructions: System instructions/prompt for the agent
        tools: List of available tools/functions
        model: LLM model to use (e.g., "gpt-4", "llama-3.2")
        temperature: LLM temperature setting
        metadata: Additional metadata
    """

    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
        role: str = "assistant",
        instructions: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        model: str = "llama-3.2",
        temperature: float = 0.7,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.description = description
        self.role = role
        self.instructions = instructions or f"You are {display_name}, {description}"
        self.tools = tools or []
        self.model = model
        self.temperature = temperature
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc).isoformat() + "Z"

    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute agent task (to be implemented by subclasses)."""
        pass

    def to_schema(self, format: str = "microsoft") -> Dict[str, Any]:
        """
        Export agent schema in standard format for interoperability.

        Args:
            format: Target format - "microsoft" | "langchain" | "semantic-kernel" | "openai"

        Returns:
            Dict conforming to the official specification of the target format

        Raises:
            ValueError: If format is not supported

        References:
            - Microsoft: https://learn.microsoft.com/en-us/azure/ai-services/agents/
            - LangChain: https://python.langchain.com/docs/modules/agents/
            - Semantic Kernel: https://learn.microsoft.com/en-us/semantic-kernel/overview/
            - OpenAI: https://platform.openai.com/docs/assistants/overview
        """
        format = format.lower()

        if format == "microsoft":
            return self._to_microsoft_schema()
        elif format == "langchain":
            return self._to_langchain_schema()
        elif format == "semantic-kernel":
            return self._to_semantic_kernel_schema()
        elif format == "openai":
            return self._to_openai_assistant_schema()
        else:
            raise ValueError(
                f"Unknown format: {format}. "
                f"Supported: microsoft, langchain, semantic-kernel, openai"
            )

    def _to_microsoft_schema(self) -> Dict[str, Any]:
        """
        Export to Microsoft Agent Framework format (Production-ready).

        Based on Microsoft Agent Framework specification:
        https://learn.microsoft.com/en-us/azure/ai-services/agents/

        Microsoft Agent Format:
        {
            "id": "agent-id",
            "object": "agent",
            "created_at": timestamp,
            "name": "Agent Name",
            "description": "Agent description",
            "model": "model-name",
            "instructions": "System instructions",
            "tools": [...],
            "metadata": {...}
        }
        """
        return {
            "id": self.name,
            "object": "agent",
            "created_at": int(
                datetime.fromisoformat(self.created_at.replace("Z", "+00:00")).timestamp()
            ),
            "name": self.display_name,
            "description": self.description,
            "model": self.model,
            "instructions": self.instructions,
            "tools": self._convert_tools_to_microsoft_format(),
            "metadata": {
                **self.metadata,
                "role": self.role,
                "temperature": self.temperature,
                "framework": "twisterlab",
                "version": "1.0.0",
            },
        }

    # Default capability and health helpers for all agents
    def get_capabilities(self) -> Dict[str, Any]:
        """Return a dictionary describing the agent's capabilities.

        By default returns the list of available tools and model metadata.
        Agents can override to provide richer capability info.
        """
        return {
            "name": self.name,
            "display_name": self.display_name,
            "tools": [tool.get("function", {}).get("name", "unknown") for tool in self.tools],
            "model": self.model,
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Return a minimal health status for the agent.

        Subclasses should override with more detailed checks.
        """
        return {
            "agent": self.name,
            "status": "healthy",
            "checks": {
                "tools_available": len(self.tools),
            },
        }

    def _to_langchain_schema(self) -> Dict[str, Any]:
        """
        Export to LangChain Agent format (Stub - v2.0 planned).

        Based on LangChain Agents specification:
        https://python.langchain.com/docs/modules/agents/

        LangChain Agent Format:
        {
            "name": "agent_name",
            "description": "Agent description",
            "llm": {...},
            "tools": [...],
            "agent_type": "zero-shot-react-description",
            "memory": {...}
        }
        """
        return {
            "_format": "langchain",
            "_status": "stub",
            "_note": "Full LangChain compatibility planned for v2.0",
            "name": self.name,
            "description": self.description,
            "llm": {"model_name": self.model, "temperature": self.temperature},
            "tools": [tool.get("function", {}).get("name", "unknown") for tool in self.tools],
            "agent_type": "zero-shot-react-description",
            "memory": None,
            "metadata": self.metadata,
        }

    def _to_semantic_kernel_schema(self) -> Dict[str, Any]:
        """
        Export to Semantic Kernel format (Stub - v2.0 planned).

        Based on Semantic Kernel specification:
        https://learn.microsoft.com/en-us/semantic-kernel/overview/

        Semantic Kernel Format:
        {
            "name": "SkillName",
            "description": "Skill description",
            "functions": [...],
            "settings": {...}
        }
        """
        return {
            "_format": "semantic-kernel",
            "_status": "stub",
            "_note": "Full Semantic Kernel compatibility planned for v2.0",
            "name": self.display_name,
            "description": self.description,
            "functions": [
                {
                    "name": tool.get("function", {}).get("name", "unknown"),
                    "description": tool.get("function", {}).get("description", ""),
                    "parameters": tool.get("function", {}).get("parameters", {}),
                }
                for tool in self.tools
            ],
            "settings": {"model": self.model, "temperature": self.temperature, "role": self.role},
            "metadata": self.metadata,
        }

    def _to_openai_assistant_schema(self) -> Dict[str, Any]:
        """
        Export to OpenAI Assistants API format (Stub - v2.0 planned).

        Based on OpenAI Assistants API specification:
        https://platform.openai.com/docs/assistants/overview

        OpenAI Assistant Format:
        {
            "id": "asst_xxx",
            "object": "assistant",
            "created_at": timestamp,
            "name": "Assistant Name",
            "description": "Assistant description",
            "model": "gpt-4",
            "instructions": "System instructions",
            "tools": [...],
            "metadata": {...}
        }
        """
        return {
            "_format": "openai-assistant",
            "_status": "stub",
            "_note": "Full OpenAI Assistants API compatibility planned for v2.0",
            "id": f"asst_{self.name}",
            "object": "assistant",
            "created_at": int(
                datetime.fromisoformat(self.created_at.replace("Z", "+00:00")).timestamp()
            ),
            "name": self.display_name,
            "description": self.description,
            "model": self.model,
            "instructions": self.instructions,
            "tools": self._convert_tools_to_openai_format(),
            "file_ids": [],
            "metadata": {
                **self.metadata,
                "role": self.role,
                "temperature": self.temperature,
                "framework": "twisterlab",
            },
        }

    def get_capabilities_list(self) -> List[str]:
        """Return agent capabilities as a list of names for compatibility with BaseAgent API.

        This method returns the 'capabilities' attribute if present (expected to be a list of
        strings), otherwise it falls back to a list of tool function names derived from
        registered tools.
        """
        if getattr(self, "capabilities", None) is not None:
            return getattr(self, "capabilities", [])
        return [tool.get("function", {}).get("name", "unknown") for tool in self.tools]

    def _convert_tools_to_microsoft_format(self) -> List[Dict[str, Any]]:
        """
        Convert TwisterLab tools to Microsoft Agent Framework format.

        Microsoft Tool Format:
        {
            "type": "function",
            "function": {
                "name": "function_name",
                "description": "Function description",
                "parameters": {...}
            }
        }
        """
        microsoft_tools = []

        for tool in self.tools:
            if tool.get("type") == "function":
                microsoft_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool["function"]["name"],
                            "description": tool["function"].get("description", ""),
                            "parameters": tool["function"].get(
                                "parameters", {"type": "object", "properties": {}, "required": []}
                            ),
                        },
                    }
                )

        return microsoft_tools

    def _convert_tools_to_openai_format(self) -> List[Dict[str, Any]]:
        """
        Convert TwisterLab tools to OpenAI Assistants API format.

        OpenAI Tool Format (same as Microsoft):
        {
            "type": "function" | "code_interpreter" | "retrieval",
            "function": {...}
        }
        """
        # OpenAI format is similar to Microsoft format
        return self._convert_tools_to_microsoft_format()

    def export_to_file(self, filepath: str, format: str = "microsoft") -> None:
        """
        Export agent schema to JSON file.

        Args:
            filepath: Output file path
            format: Target format (microsoft, langchain, semantic-kernel, openai)
        """
        schema = self.to_schema(format)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"TwisterAgent(name='{self.name}', role='{self.role}', tools={len(self.tools)})"


class HelpdeskAgent(TwisterAgent):
    """IT Helpdesk Agent for TwisterLab v1.0."""

    def __init__(self) -> None:
        super().__init__(
            name="helpdesk-resolver",
            display_name="IT Helpdesk Resolver",
            description=(
                "Resolves common IT helpdesk tickets automatically "
                "(password resets, software installs, access requests)"
            ),
            role="helpdesk",
            instructions=(
                "You are an IT Helpdesk Agent specializing in resolving common IT support tickets. "
                "You can automatically handle password resets, software installations, access "
                "requests, and basic troubleshooting. For complex issues, escalate to human agents."
            ),
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "reset_password",
                        "description": "Reset user password in Active Directory",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "username": {
                                    "type": "string",
                                    "description": "Username to reset password for",
                                },
                                "temporary_password": {
                                    "type": "string",
                                    "description": "Temporary password to set",
                                },
                            },
                            "required": ["username"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "install_software",
                        "description": "Install software via Desktop Commander on user's machine",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "device_id": {
                                    "type": "string",
                                    "description": "Target device identifier",
                                },
                                "software_name": {
                                    "type": "string",
                                    "description": "Name of software to install",
                                },
                                "version": {
                                    "type": "string",
                                    "description": "Software version (optional)",
                                },
                            },
                            "required": ["device_id", "software_name"],
                        },
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "grant_access",
                        "description": "Grant user access to a resource or group",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "username": {
                                    "type": "string",
                                    "description": "Username to grant access to",
                                },
                                "resource": {
                                    "type": "string",
                                    "description": "Resource or group name",
                                },
                            },
                            "required": ["username", "resource"],
                        },
                    },
                },
            ],
            model="llama-3.2",
            temperature=0.3,  # Low temperature for consistent IT operations
            metadata={"department": "IT", "sla_target": "2 minutes", "automation_rate": "60-70%"},
        )

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute helpdesk task."""
        # Implementation would go here
        return {"status": "success", "task": task}

    class TicketClassifierAgent(TwisterAgent):
        """Ticket Classifier Agent for TwisterLab."""

        def __init__(self) -> None:
            super().__init__(
                name="classifier",
                display_name="Ticket Classifier",
                description=(
                    "Classifies incoming helpdesk tickets by category, " "priority, and complexity"
                ),
                role="classifier",
                instructions=(
                    "You are a Ticket Classifier Agent.\n"
                    "Analyze incoming helpdesk tickets and classify them by:\n"
                    "1. Category (password, software, access, hardware, network, other)\n"
                    "2. Priority (low, medium, high, urgent)\n"
                    "3. Complexity (simple, moderate, complex)\n"
                    "4. Confidence score (0.0-1.0)\n\n"
                    "Provide structured output for routing decisions."
                ),
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "classify_ticket",
                            "description": "Classify a helpdesk ticket",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "ticket_id": {
                                        "type": "string",
                                        "description": "Ticket identifier",
                                    },
                                    "subject": {"type": "string", "description": "Ticket subject"},
                                    "description": {
                                        "type": "string",
                                        "description": "Ticket description",
                                    },
                                },
                                "required": ["ticket_id", "subject", "description"],
                            },
                        },
                    }
                ],
                model="deepseek-r1",  # Using DeepSeek-R1 for classification
                temperature=0.2,  # Very low for consistent classification
                metadata={"department": "IT", "accuracy_target": "95%", "avg_time": "<5 seconds"},
            )

        async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
            """Execute classification task."""
            return {"status": "success", "task": task}

    class DesktopCommanderAgent(TwisterAgent):
        """Desktop Commander Agent for TwisterLab."""

        def __init__(self) -> None:
            super().__init__(
                name="desktop-commander",
                display_name="Desktop Commander",
                description=(
                    "Distributed agent system for remote desktop management "
                    "and command execution"
                ),
                role="desktop-commander",
                instructions=(
                    "You are a Desktop Commander Agent managing remote desktop clients. "
                    "You can execute commands, deploy software, gather system information, and "
                    "perform remote diagnostics on registered client machines. All operations are "
                    "logged and secured with zero-trust architecture."
                ),
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "execute_command",
                            "description": "Execute command on remote desktop client",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "device_id": {
                                        "type": "string",
                                        "description": "Target device identifier",
                                    },
                                    "command": {
                                        "type": "string",
                                        "description": "Command to execute (from whitelist only)",
                                    },
                                    "timeout": {
                                        "type": "integer",
                                        "description": "Command timeout in seconds (default: 300)",
                                    },
                                },
                                "required": ["device_id", "command"],
                            },
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "deploy_package",
                            "description": "Deploy software package to remote device",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "device_id": {
                                        "type": "string",
                                        "description": "Target device identifier",
                                    },
                                    "package_url": {
                                        "type": "string",
                                        "description": "Package download URL",
                                    },
                                    "install_args": {
                                        "type": "string",
                                        "description": "Installation arguments",
                                    },
                                },
                                "required": ["device_id", "package_url"],
                            },
                        },
                    },
                    {
                        "type": "function",
                        "function": {
                            "name": "get_system_info",
                            "description": "Gather system information from remote device",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "device_id": {
                                        "type": "string",
                                        "description": "Target device identifier",
                                    },
                                    "info_type": {
                                        "type": "string",
                                        "enum": ["hardware", "software", "network", "all"],
                                        "description": "Type of information to gather",
                                    },
                                },
                                "required": ["device_id"],
                            },
                        },
                    },
                ],
                model="llama-3.2",
                temperature=0.1,  # Very low for precise command execution
                metadata={
                    "department": "IT",
                    "security_level": "zero-trust",
                    "max_concurrent_commands": 10,
                },
            )

        async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Any:
            """Execute desktop commander task."""
            return {"status": "success", "task": task}
