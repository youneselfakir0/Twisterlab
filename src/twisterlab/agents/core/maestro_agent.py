"""
Maestro Agent

MCP-agnostic orchestration agent for TwisterLab.
Coordinates other agents and provides LLM-powered reasoning.
"""

from __future__ import annotations

import logging
from typing import List

from .base import (
    CoreAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    CapabilityParam,
    ParamType,
)
from twisterlab.services.base import LLMMessage

logger = logging.getLogger(__name__)


class MaestroAgent(CoreAgent):
    """
    Orchestration agent for TwisterLab.

    Provides capabilities for:
    - LLM chat and generation
    - Agent coordination
    """

    @property
    def name(self) -> str:
        return "maestro"

    @property
    def description(self) -> str:
        return "Orchestration agent with LLM-powered reasoning"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            # LLM Operations
            AgentCapability(
                name="chat",
                description="Send a message to the LLM and get a response",
                handler="handle_chat",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "message",
                        ParamType.STRING,
                        "Message to send to the LLM",
                    ),
                    CapabilityParam(
                        "model",
                        ParamType.STRING,
                        "Model to use",
                        required=False,
                        default="qwen3:8b",
                    ),
                    CapabilityParam(
                        "system_prompt",
                        ParamType.STRING,
                        "System prompt for context",
                        required=False,
                    ),
                ],
                tags=["llm", "chat"],
            ),
            AgentCapability(
                name="generate",
                description="Generate text completion from LLM",
                handler="handle_generate",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "prompt",
                        ParamType.STRING,
                        "Prompt for generation",
                    ),
                    CapabilityParam(
                        "model",
                        ParamType.STRING,
                        "Model to use",
                        required=False,
                        default="qwen3:8b",
                    ),
                ],
                tags=["llm", "generate"],
            ),
            # Orchestration (Simplified)
            AgentCapability(
                name="list_agents",
                description="List all available agents and their capabilities",
                handler="handle_list_agents",
                capability_type=CapabilityType.QUERY,
                tags=["agents", "discovery"],
            ),
            # Analysis
            AgentCapability(
                name="analyze",
                description="Analyze data or code using LLM",
                handler="handle_analyze",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam(
                        "content",
                        ParamType.STRING,
                        "Content to analyze",
                    ),
                    CapabilityParam(
                        "analysis_type",
                        ParamType.STRING,
                        "Type of analysis",
                        required=False,
                        default="general",
                        enum=["general", "code", "data", "logs", "security"],
                    ),
                ],
                tags=["llm", "analysis"],
            ),
        ]

    # =========================================================================
    # Handler Methods
    # =========================================================================

    async def handle_chat(
        self, message: str, model: str = "qwen3:8b", system_prompt: str = None
    ) -> AgentResponse:
        """Send a chat message to the LLM."""
        try:
            llm = self.registry.get_llm()

            messages = []
            if system_prompt:
                messages.append(LLMMessage(role="system", content=system_prompt))
            messages.append(LLMMessage(role="user", content=message))

            response = await llm.chat(messages, model=model)

            return AgentResponse(
                success=True,
                data={
                    "model": model,
                    "response": response.content,
                    "tokens": response.total_tokens,
                },
            )
        except Exception as e:
            logger.exception("Chat failed")
            return AgentResponse(success=False, error=str(e))

    async def handle_generate(
        self, prompt: str, model: str = "qwen3:8b"
    ) -> AgentResponse:
        """Generate text from prompt."""
        try:
            llm = self.registry.get_llm()
            response = await llm.generate(prompt, model=model)

            return AgentResponse(
                success=True,
                data={
                    "model": model,
                    "response": response.content,
                    "tokens": response.total_tokens,
                },
            )
        except Exception as e:
            logger.exception("Generation failed")
            return AgentResponse(success=False, error=str(e))

    async def handle_list_agents(self) -> AgentResponse:
        """List available agents."""
        try:
            # In production, this would query an AgentRegistry
            agents = [
                {
                    "name": "maestro",
                    "description": "Orchestration agent",
                    "capabilities": [
                        "chat",
                        "generate",
                        "orchestrate",
                        "list_agents",
                        "analyze",
                    ],
                },
                {
                    "name": "monitoring",
                    "description": "Infrastructure monitoring",
                    "capabilities": [
                        "health_check",
                        "get_system_metrics",
                        "list_containers",
                        "get_container_logs",
                    ],
                },
                {
                    "name": "database",
                    "description": "Database operations",
                    "capabilities": ["execute_query", "list_tables", "describe_table"],
                },
                {
                    "name": "cache",
                    "description": "Cache operations",
                    "capabilities": [
                        "cache_get",
                        "cache_set",
                        "cache_delete",
                        "cache_keys",
                        "cache_stats",
                    ],
                },
            ]

            return AgentResponse(
                success=True,
                data={
                    "agents": agents,
                    "count": len(agents),
                },
            )
        except Exception as e:
            logger.exception("List agents failed")
            return AgentResponse(success=False, error=str(e))

    async def handle_analyze(
        self, content: str, analysis_type: str = "general"
    ) -> AgentResponse:
        """Analyze content using LLM."""
        try:
            llm = self.registry.get_llm()

            prompts = {
                "general": "Analyze the following content and provide insights:",
                "code": "Analyze the following code for issues, improvements, and best practices:",
                "data": "Analyze the following data and identify patterns, anomalies, and insights:",
                "logs": "Analyze the following logs for errors, warnings, and issues:",
                "security": "Analyze the following for security vulnerabilities and risks:",
            }

            system_prompt = prompts.get(analysis_type, prompts["general"])

            response = await llm.chat(
                [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=content),
                ],
                model="qwen3:8b",
            )

            return AgentResponse(
                success=True,
                data={
                    "analysis_type": analysis_type,
                    "analysis": response.content,
                },
            )
        except Exception as e:
            logger.exception("Analysis failed")
            return AgentResponse(success=False, error=str(e))
