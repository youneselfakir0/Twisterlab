"""
RealMaestroAgent - The Orchestrator Brain

This is the central intelligence that:
1. Analyzes incoming tickets/tasks
2. Decides which agents to dispatch
3. Coordinates multi-agent workflows
4. Synthesizes results into actionable solutions

Supports both LLM-based decisions (Ollama/Claude) and rule-based fallback.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    httpx = None

from twisterlab.agents.core.base import (
    CoreAgent,
    AgentCapability,
    AgentResponse,
    CapabilityType,
    CapabilityParam,
    ParamType,
)

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCategory(Enum):
    DATABASE = "database"
    NETWORK = "network"
    APPLICATION = "application"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"
    UNKNOWN = "unknown"


@dataclass
class OrchestratedTask:
    id: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.UNKNOWN
    agents_involved: List[str] = field(default_factory=list)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    results: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None


class RealMaestroAgent(CoreAgent):
    """The Maestro Orchestrator - Central brain for multi-agent coordination."""

    def __init__(self, agent_registry=None) -> None:
        super().__init__()
        self._agent_registry = agent_registry
        self._ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self._use_llm = os.getenv("MAESTRO_USE_LLM", "true").lower() == "true"

    @property
    def name(self) -> str:
        return "maestro"

    @property
    def description(self) -> str:
        return "Orchestrates multi-agent workflows intelligently"

    @property
    def agent_registry(self):
        if self._agent_registry is None:
            try:
                from twisterlab.agents.registry import get_agent_registry
                self._agent_registry = get_agent_registry()
            except ImportError:
                logger.warning("Could not import agent registry")
        return self._agent_registry

    @agent_registry.setter
    def agent_registry(self, value):
        self._agent_registry = value

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="orchestrate",
                description="Orchestrate a complete task workflow across multiple agents",
                handler="handle_orchestrate",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("task", ParamType.STRING, "The task or ticket to process", required=True),
                    CapabilityParam("context", ParamType.OBJECT, "Additional context", required=False),
                    CapabilityParam("dry_run", ParamType.BOOLEAN, "Plan only, don't execute", required=False, default=False),
                ],
            ),
            AgentCapability(
                name="analyze_task",
                description="Analyze a task to determine category and priority",
                handler="handle_analyze_task",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("task", ParamType.STRING, "The task description", required=True),
                ],
            ),
        ]

    async def handle_orchestrate(self, task: str, context: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> AgentResponse:
        logger.info(f"Maestro orchestrating: {task[:100]}...")
        
        orchestrated = OrchestratedTask(
            id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=task
        )
        
        try:
            analysis = await self._analyze_task(task, context)
            orchestrated.priority = analysis["priority"]
            orchestrated.category = analysis["category"]
            
            plan = await self._create_plan(task, analysis, context)
            orchestrated.agents_involved = plan["agents"]
            orchestrated.steps = plan["steps"]
            
            if dry_run:
                return AgentResponse(success=True, data={
                    "mode": "dry_run",
                    "task_id": orchestrated.id,
                    "analysis": {"category": orchestrated.category.value, "priority": orchestrated.priority.value},
                    "plan": plan,
                })
            
            results = await self._execute_plan(plan, task, context)
            orchestrated.results = results
            orchestrated.status = "completed"
            orchestrated.completed_at = datetime.now(timezone.utc).isoformat()
            
            synthesis = await self._synthesize_results(task, results, analysis)
            
            return AgentResponse(success=True, data={
                "task_id": orchestrated.id,
                "status": "completed",
                "analysis": {"category": orchestrated.category.value, "priority": orchestrated.priority.value},
                "agents_used": orchestrated.agents_involved,
                "steps_executed": len(orchestrated.steps),
                "results": results,
                "synthesis": synthesis,
            })
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return AgentResponse(success=False, error=str(e))

    async def handle_analyze_task(self, task: str) -> AgentResponse:
        analysis = await self._analyze_task(task, None)
        return AgentResponse(success=True, data={
            "category": analysis["category"].value,
            "priority": analysis["priority"].value,
            "suggested_agents": analysis["suggested_agents"],
            "keywords": analysis["keywords"],
        })

    async def _analyze_task(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if self._use_llm and httpx:
            llm_analysis = await self._llm_analyze(task, context)
            if llm_analysis:
                return llm_analysis
        return self._rule_based_analyze(task, context)

    async def _llm_analyze(self, task: str, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        try:
            prompt = f"""Analyze this support ticket and respond in JSON format only:
TICKET: {task}
Respond with: {{"category": "database|network|application|security|infrastructure|unknown", "priority": "critical|high|medium|low", "suggested_agents": [], "keywords": []}}"""
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._ollama_url}/api/generate",
                    json={"model": self._ollama_model, "prompt": prompt, "stream": False, "format": "json"}
                )
                if response.status_code == 200:
                    import json
                    result = response.json()
                    analysis = json.loads(result.get("response", "{}"))
                    return {
                        "category": TaskCategory(analysis.get("category", "unknown")),
                        "priority": TaskPriority(analysis.get("priority", "medium")),
                        "suggested_agents": analysis.get("suggested_agents", []),
                        "keywords": analysis.get("keywords", []),
                        "source": "llm",
                    }
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
        return None

    def _rule_based_analyze(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        task_lower = task.lower()
        category = TaskCategory.UNKNOWN
        keywords = []
        suggested_agents = ["classifier", "sentiment-analyzer"]
        
        if any(kw in task_lower for kw in ["database", "sql", "postgres", "mysql", "query", "db"]):
            category = TaskCategory.DATABASE
            keywords = ["database", "sql"]
            suggested_agents.extend(["monitoring", "real-desktop-commander"])
        elif any(kw in task_lower for kw in ["network", "connection", "timeout", "dns"]):
            category = TaskCategory.NETWORK
            keywords = ["network", "connectivity"]
            suggested_agents.extend(["monitoring", "browser"])
        elif any(kw in task_lower for kw in ["security", "breach", "hack", "vulnerability"]):
            category = TaskCategory.SECURITY
            keywords = ["security", "threat"]
            suggested_agents.extend(["backup", "monitoring"])
        elif any(kw in task_lower for kw in ["server", "cpu", "memory", "disk", "crash"]):
            category = TaskCategory.INFRASTRUCTURE
            keywords = ["infrastructure", "server"]
            suggested_agents.extend(["monitoring", "real-desktop-commander"])
        elif any(kw in task_lower for kw in ["app", "application", "error", "bug", "500", "404"]):
            category = TaskCategory.APPLICATION
            keywords = ["application", "error"]
            suggested_agents.extend(["browser", "monitoring"])
        
        priority = TaskPriority.MEDIUM
        if any(kw in task_lower for kw in ["urgent", "critical", "down", "crash", "emergency"]):
            priority = TaskPriority.CRITICAL
        elif any(kw in task_lower for kw in ["important", "high", "production"]):
            priority = TaskPriority.HIGH
        elif any(kw in task_lower for kw in ["minor", "low", "when possible"]):
            priority = TaskPriority.LOW
        
        return {"category": category, "priority": priority, "suggested_agents": list(set(suggested_agents)), "keywords": keywords, "source": "rules"}

    async def _create_plan(self, task: str, analysis: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        category = analysis["category"]
        steps = [
            {"order": 1, "agent": "sentiment-analyzer", "capability": "analyze_sentiment", "params": {"text": task}, "purpose": "Determine urgency"},
            {"order": 2, "agent": "classifier", "capability": "classify_ticket", "params": {"ticket_text": task}, "purpose": "Categorize issue"},
        ]
        
        if category == TaskCategory.DATABASE:
            steps.append({"order": 3, "agent": "real-desktop-commander", "capability": "execute_command", "params": {"device_id": "db-server", "command": "pg_stat_activity"}, "purpose": "Check database"})
        elif category == TaskCategory.APPLICATION:
            steps.append({"order": 3, "agent": "browser", "capability": "browse", "params": {"url": "http://localhost:8000/health"}, "purpose": "Check app health"})
        
        steps.append({"order": len(steps) + 1, "agent": "resolver", "capability": "resolve_ticket", "params": {"ticket_id": "TKT-AUTO", "resolution_note": "Auto-resolved by Maestro"}, "purpose": "Mark resolved"})
        
        return {"agents": list(set(s["agent"] for s in steps)), "steps": steps, "estimated_duration_sec": len(steps) * 5}

    async def _execute_plan(self, plan: Dict[str, Any], task: str, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for step in plan["steps"]:
            step_result = {"step": step["order"], "agent": step["agent"], "capability": step["capability"], "status": "pending"}
            try:
                agent = self._get_agent(step["agent"])
                if not agent:
                    step_result["status"] = "skipped"
                    step_result["reason"] = f"Agent {step['agent']} not available"
                else:
                    result = await agent.execute(step["capability"], **step["params"])
                    step_result["status"] = "success" if result.success else "failed"
                    step_result["data"] = result.data
                    if result.error:
                        step_result["error"] = result.error
            except Exception as e:
                step_result["status"] = "error"
                step_result["error"] = str(e)
            results.append(step_result)
        return results

    def _get_agent(self, agent_name: str):
        if not self.agent_registry:
            return None
        return self.agent_registry.get_agent(agent_name)

    async def _synthesize_results(self, task: str, results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        successful_steps = [r for r in results if r["status"] == "success"]
        findings = []
        for r in successful_steps:
            if r["agent"] == "sentiment-analyzer" and r.get("data"):
                findings.append(f"Sentiment: {r['data'].get('sentiment', 'unknown')}")
            elif r["agent"] == "classifier" and r.get("data"):
                findings.append(f"Category: {r['data'].get('category', 'unknown')}")
        
        return {
            "summary": f"Processed task with {len(successful_steps)}/{len(results)} successful steps",
            "findings": findings,
            "success_rate": len(successful_steps) / len(results) if results else 0,
            "requires_human": len(results) - len(successful_steps) > 0,
        }


__all__ = ["RealMaestroAgent", "TaskPriority", "TaskCategory", "OrchestratedTask"]
