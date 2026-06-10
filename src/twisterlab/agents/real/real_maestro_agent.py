"""
RealMaestroAgent - The Orchestrator Brain 🧠

This is the central intelligence that:
1. Analyzes incoming tickets/tasks
2. Decides which agents to dispatch
3. Coordinates multi-agent workflows
4. Synthesizes results into actionable solutions

Supports both LLM-based decisions (Ollama/Claude) and rule-based fallback.
"""

from __future__ import annotations

import asyncio
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
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskCategory(Enum):
    """Task categories for routing."""
    DATABASE = "database"
    NETWORK = "network"
    APPLICATION = "application"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"
    UNKNOWN = "unknown"


@dataclass
class OrchestratedTask:
    """Represents a task being orchestrated."""
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
    """
    The Maestro Orchestrator - Central brain for multi-agent coordination.
    
    Workflow:
    1. Receive task → Analyze with LLM or rules
    2. Plan → Decide which agents and in what order
    3. Execute → Dispatch to agents, collect results
    4. Synthesize → Combine results into final solution
    5. Report → Return comprehensive response
    """

    def __init__(self, agent_registry=None) -> None:
        super().__init__()
        self._agent_registry = agent_registry
        from twisterlab.config.unified_settings import settings
        self._ollama_url = settings.infra.ollama_base_url
        self._ollama_model = settings.infra.ollama_model
        self._use_llm = os.getenv("MAESTRO_USE_LLM", "true").lower() == "true"
        self._mission_dir = "/app/archives/missions"
        
        # Ensure mission directory exists
        if not os.path.exists(self._mission_dir):
            try:
                os.makedirs(self._mission_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create mission dir {self._mission_dir}: {e}")
                # Fallback to local data dir if PVC not mounted correctly
                self._mission_dir = "data/missions"
                os.makedirs(self._mission_dir, exist_ok=True)

    @property
    def name(self) -> str:
        return "maestro"

    @property
    def description(self) -> str:
        return "Orchestrates multi-agent workflows intelligently using LLM or rule-based decisions"

    @property
    def agent_registry(self):
        """Lazy load agent registry to avoid circular imports."""
        if self._agent_registry is None:
            try:
                from twisterlab.agents.registry import get_agent_registry
                self._agent_registry = get_agent_registry()
            except ImportError:
                logger.warning("Could not import agent registry")
        return self._agent_registry

    @agent_registry.setter
    def agent_registry(self, value):
        """Allow setting agent registry."""
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
                    CapabilityParam("context", ParamType.OBJECT, "Additional context (client info, urgency, etc.)", required=False),
                    CapabilityParam("dry_run", ParamType.BOOLEAN, "Plan only, don't execute", required=False, default=False),
                ],
                tags=["orchestration", "multi-agent", "workflow"],
            ),
            AgentCapability(
                name="analyze_task",
                description="Analyze a task to determine category, priority, and required agents",
                handler="handle_analyze_task",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("task", ParamType.STRING, "The task description to analyze", required=True),
                ],
                tags=["analysis", "planning"],
            ),
            AgentCapability(
                name="list_available_agents",
                description="List all available agents and their capabilities",
                handler="handle_list_agents",
                capability_type=CapabilityType.QUERY,
                params=[],
                tags=["discovery"],
            ),
            AgentCapability(
                name="get_mission_history",
                description="List past mission reports and their status",
                handler="handle_get_history",
                capability_type=CapabilityType.QUERY,
                tags=["history", "audit"],
            ),
        ]

    # =========================================================================
    # MAIN ORCHESTRATION
    # =========================================================================

    async def handle_get_history(self) -> AgentResponse:
        """List past mission files from disk."""
        try:
            import json
            missions = []
            if os.path.exists(self._mission_dir):
                for filename in os.listdir(self._mission_dir):
                    if filename.endswith(".json"):
                        with open(os.path.join(self._mission_dir, filename), "r") as f:
                            data = json.load(f)
                            missions.append({
                                "id": data.get("task_id"),
                                "task": data.get("description", "Unknown"),
                                "status": data.get("status"),
                                "completed_at": data.get("completed_at"),
                                "summary": data.get("synthesis", {}).get("summary", "No summary")
                            })
            return AgentResponse(success=True, data={"missions": sorted(missions, key=lambda x: x.get('completed_at', ''), reverse=True)})
        except Exception as e:
            return AgentResponse(success=False, error=str(e))

    async def handle_orchestrate(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False
    ) -> AgentResponse:
        """
        Conversational orchestration entry point.
        
        1. Dialogue-first approach: Analyze the intent (chat vs task)
        2. Thought process: Explain what Maestro is thinking
        3. Action: Execute only if a clear tactical task is identified
        """
        logger.info(f"💬 Maestro processing input: {task[:100]}...")
        
        orchestrated = OrchestratedTask(
            id=f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description=task
        )
        
        try:
            # Step 0: Check if this is just chat or a task
            analysis = await self._analyze_task(task, context)
            thought = analysis.get("thought", "Analyzing your request...")
            
            # If the LLM thinks this is just a conversational interaction without immediate tactical needs
            if analysis.get("is_chat_only", False):
                return AgentResponse(
                    success=True,
                    data={
                        "mode": "chat",
                        "thought": thought,
                        "response": analysis.get("response", "I understand. How else can I assist with the fleet?"),
                        "analysis": analysis
                    }
                )

            # Step 1: Tactical Task identified
            orchestrated.priority = analysis["priority"]
            orchestrated.category = analysis["category"]
            logger.info(f"📊 Tactical Analysis: {analysis['category'].value} / {analysis['priority'].value}")
            
            # Step 2: Plan
            try:
                from twisterlab.services.learning import LearningService
            except ImportError:
                LearningService = None

            matching_skill = await LearningService.find_matching_skill(task) if LearningService else None
            if matching_skill:
                logger.info(f"🎯 Using auto-generated skill: {matching_skill.name}")
                plan = {
                    "agents": list(set(s["agent"] for s in matching_skill.steps)),
                    "steps": matching_skill.steps,
                }
            else:
                plan = await self._create_plan(task, analysis, context)
                
            orchestrated.agents_involved = plan["agents"]
            orchestrated.steps = plan["steps"]
            
            if dry_run:
                return AgentResponse(
                    success=True,
                    data={
                        "mode": "dry_run",
                        "thought": f"I have formulated a tactical plan for: {task}. I will deploy {len(plan['steps'])} agents.",
                        "plan": plan,
                        "analysis": analysis
                    }
                )
            
            # Step 3: Execute
            orchestrated.status = "executing"
            results = await self._execute_plan(plan, task, context)
            orchestrated.results = results
            
            # Step 4: Synthesize
            synthesis = await self._synthesize_results(task, results, analysis)
            
            # Step 5: Mandatory Notion Reporting
            notion_status = "skipped"
            notion_url = None
            try:
                notion_agent = self._get_agent("notion")
                if notion_agent:
                    logger.info(f"📝 Logging mission {orchestrated.id} to Notion...")
                    notion_resp = await notion_agent.execute(
                        "log_mission",
                        mission_id=orchestrated.id,
                        task=task,
                        status="completed",
                        findings=synthesis.get("findings", []),
                        resolution=synthesis.get("summary", ""),
                        agents_used=orchestrated.agents_involved
                    )
                    if notion_resp.success:
                        notion_status = "success"
                        notion_url = notion_resp.data.get("url")
                    else:
                        notion_status = "failed"
                else:
                    logger.warning("⚠️ Notion agent not available for reporting")
            except Exception as ne:
                logger.error(f"❌ Failed to log to Notion: {ne}")
                notion_status = f"error: {ne}"

            orchestrated.status = "completed"
            orchestrated.completed_at = datetime.now(timezone.utc).isoformat()
            
            # SAVE TRACE TO DISK
            try:
                import json
                mission_payload = {
                    "task_id": orchestrated.id,
                    "description": task,
                    "status": orchestrated.status,
                    "completed_at": orchestrated.completed_at,
                    "analysis": {
                        "category": orchestrated.category.value,
                        "priority": orchestrated.priority.value,
                    },
                    "agents_used": orchestrated.agents_involved,
                    "steps": orchestrated.steps,
                    "results": results,
                    "synthesis": synthesis,
                }
                with open(os.path.join(self._mission_dir, f"{orchestrated.id}.json"), "w") as f:
                    json.dump(mission_payload, f, indent=2, default=str)
                logger.info(f"💾 Mission trace saved: {orchestrated.id}.json")
            except Exception as fe:
                logger.error(f"Failed to save mission trace: {fe}")

            # Learning & Self-improvement triggers
            try:
                from twisterlab.services.learning import LearningService, MemoryService, UserProfileService
                # 1. Save memory summary of the run
                if MemoryService:
                    await MemoryService.save_memory(
                        task_description=task,
                        execution_results=results,
                        session_id=orchestrated.id
                    )
                
                # 2. Extract/refine reusable skill
                if LearningService:
                    await LearningService.extract_and_save_skill(
                        task_description=task,
                        execution_results=results
                    )
                
                # 3. Refine user preferences profile
                if UserProfileService:
                    await UserProfileService.refine_profile_from_interaction(
                        user_message=task,
                        agent_response=str(synthesis.get("summary", ""))
                    )
            except Exception as le:
                logger.error(f"⚠️ Learning loop/Memory update failed: {le}", exc_info=True)
            
            return AgentResponse(
                success=True,
                data={
                    "task_id": orchestrated.id,
                    "status": "completed",
                    "mode": "tactical",
                    "thought": thought,
                    "notion_report": notion_status,
                    "notion_url": notion_url,
                    "analysis": {
                        "category": orchestrated.category.value,
                        "priority": orchestrated.priority.value,
                    },
                    "agents_used": orchestrated.agents_involved,
                    "steps_executed": len(orchestrated.steps),
                    "results": results,
                    "synthesis": synthesis,
                    "duration_ms": self._calculate_duration(orchestrated),
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}", exc_info=True)
            orchestrated.status = "failed"
            # Even on failure, save memory
            try:
                from twisterlab.services.learning import MemoryService
                if MemoryService:
                    await MemoryService.save_memory(
                        task_description=task,
                        execution_results=orchestrated.results or [{"step": 0, "agent": "unknown", "capability": "unknown", "purpose": "orchestration failed", "status": "failed", "error": str(e)}],
                        session_id=orchestrated.id
                    )
            except Exception as me:
                logger.error(f"Failed to save failed run memory: {me}")
                
            return AgentResponse(
                success=False,
                error=str(e),
                data={"task_id": orchestrated.id, "partial_results": orchestrated.results}
            )

    async def handle_analyze_task(self, task: str) -> AgentResponse:
        """Analyze a task without executing."""
        analysis = await self._analyze_task(task, None)
        return AgentResponse(
            success=True,
            data={
                "category": analysis["category"].value,
                "priority": analysis["priority"].value,
                "suggested_agents": analysis["suggested_agents"],
                "keywords": analysis["keywords"],
            }
        )

    async def handle_list_agents(self) -> AgentResponse:
        """List all available agents."""
        if not self.agent_registry:
            return AgentResponse(success=False, error="Agent registry not available")
        
        agents = []
        for name, agent in self.agent_registry._agents.items():
            agents.append({
                "name": name,
                "description": getattr(agent, 'description', 'No description'),
                "capabilities": [c.name for c in agent.get_capabilities()] if hasattr(agent, 'get_capabilities') else []
            })
        
        return AgentResponse(success=True, data={"agents": agents, "count": len(agents)})

    # =========================================================================
    # ANALYSIS ENGINE
    # =========================================================================

    async def _analyze_task(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze task to determine category, priority, and required agents."""
        
        # Try LLM analysis first
        if self._use_llm and httpx:
            llm_analysis = await self._llm_analyze(task, context)
            if llm_analysis:
                return llm_analysis
        
        # Fallback to rule-based analysis
        return self._rule_based_analyze(task, context)

    async def _llm_analyze(self, task: str, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Use LLM (Ollama) to analyze the task or conversation."""
        try:
            prompt = f"""You are the TwisterLab Maestro Brain. 
Your goal is to converse with the user and decide if a tactical fleet operation is needed.

USER MESSAGE: {task}

Respond in JSON format only with these fields:
{{
    "is_chat_only": boolean, (true if this is just conversation, false if a tactical task is requested)
    "thought": "your internal reasoning about the user's intent",
    "response": "your direct reply to the user (if chat_only)",
    "category": "database|network|application|security|infrastructure|monitoring|unknown",
    "priority": "critical|high|medium|low",
    "suggested_agents": ["agent1", "agent2"],
    "keywords": ["keyword1", "keyword2"]
}}

Rules:
1. Be helpful and professional.
2. If the user asks a question about the fleet, answer it (is_chat_only: true).
3. If the user describes a problem to solve or an audit to run, set is_chat_only: false.
"""
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._ollama_url}/api/generate",
                    json={
                        "model": self._ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    import json
                    analysis = json.loads(result.get("response", "{}"))
                    
                    return {
                        "is_chat_only": analysis.get("is_chat_only", False),
                        "thought": analysis.get("thought", ""),
                        "response": analysis.get("response", ""),
                        "category": TaskCategory(analysis.get("category", "unknown")),
                        "priority": TaskPriority(analysis.get("priority", "medium")),
                        "suggested_agents": analysis.get("suggested_agents", []),
                        "keywords": analysis.get("keywords", []),
                        "source": "llm",
                    }
                    
        except Exception as e:
            logger.warning(f"LLM analysis failed, falling back to rules: {e}")
        
        return None

    def _rule_based_analyze(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule-based fallback analysis."""
        task_lower = task.lower()
        
        # Category detection
        category = TaskCategory.UNKNOWN
        keywords = []
        suggested_agents = ["classifier", "sentiment-analyzer"]
        
        if any(kw in task_lower for kw in ["database", "sql", "postgres", "mysql", "query", "slow query", "db"]):
            category = TaskCategory.DATABASE
            keywords = ["database", "sql"]
            suggested_agents.extend(["monitoring", "real-desktop-commander"])
            
        elif any(kw in task_lower for kw in ["network", "connection", "timeout", "dns", "ip", "firewall"]):
            category = TaskCategory.NETWORK
            keywords = ["network", "connectivity"]
            suggested_agents.extend(["monitoring", "browser"])
            
        elif any(kw in task_lower for kw in ["security", "breach", "hack", "unauthorized", "vulnerability"]):
            category = TaskCategory.SECURITY
            keywords = ["security", "threat"]
            suggested_agents.extend(["backup", "monitoring"])
            
        elif any(kw in task_lower for kw in ["server", "cpu", "memory", "disk", "crash", "restart"]):
            category = TaskCategory.INFRASTRUCTURE
            keywords = ["infrastructure", "server"]
            suggested_agents.extend(["monitoring", "real-desktop-commander"])
            
        elif any(kw in task_lower for kw in ["app", "application", "error", "bug", "crash", "500", "404"]):
            category = TaskCategory.APPLICATION
            keywords = ["application", "error"]
            suggested_agents.extend(["browser", "monitoring"])

        elif any(kw in task_lower for kw in ["audit", "monitoring", "metrics", "health", "status", "uptime", "inventory"]):
            category = TaskCategory.MONITORING
            keywords = ["monitoring", "audit", "health"]
            suggested_agents.extend(["monitoring", "real-desktop-commander"])

        # Priority detection
        priority = TaskPriority.MEDIUM
        
        if any(kw in task_lower for kw in ["urgent", "critical", "down", "crash", "emergency", "asap"]):
            priority = TaskPriority.CRITICAL
        elif any(kw in task_lower for kw in ["important", "high", "production", "client"]):
            priority = TaskPriority.HIGH
        elif any(kw in task_lower for kw in ["minor", "low", "when possible"]):
            priority = TaskPriority.LOW
        
        # Context‑based priority boost
        if context:
            if context.get("urgency") == "high":
                priority = TaskPriority.HIGH
            if context.get("is_production"):
                priority = TaskPriority.HIGH if priority == TaskPriority.MEDIUM else priority
        
        # Generate a rule-based thought
        thought_map = {
            TaskCategory.DATABASE: "I've detected a database-related issue. I will analyze the slow queries and server logs.",
            TaskCategory.NETWORK: "This looks like a connectivity problem. I'll check the network status and firewall configurations.",
            TaskCategory.SECURITY: "Security alert detected. I'm initiating an infrastructure audit and access log review.",
            TaskCategory.INFRASTRUCTURE: "Server instability detected. I will check the hardware metrics and service statuses.",
            TaskCategory.APPLICATION: "Application error reported. I'll inspect the health endpoints and recent deployment logs.",
            TaskCategory.MONITORING: "Monitoring request received. I'm collecting system health and performance metrics.",
            TaskCategory.UNKNOWN: f"I've received your request about: '{task[:30]}...'. I'll start by analyzing the intent and sentiment to categorize it."
        }
        
        return {
            "category": category,
            "priority": priority,
            "suggested_agents": list(set(suggested_agents)),
            "keywords": keywords,
            "thought": thought_map.get(category, thought_map[TaskCategory.UNKNOWN]),
            "source": "rules",
        }

    # =========================================================================
    # PLANNING ENGINE
    # =========================================================================

    async def _create_plan(
        self, 
        task: str, 
        analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create an execution plan based on analysis."""
        
        # 1. Fetch user preferences and search similar memories for RAG/RAP
        try:
            from twisterlab.services.learning import UserProfileService, MemoryService
            preferences = await UserProfileService.get_preferences()
            similar_memories = await MemoryService.search_memories(task, limit=3)
        except Exception as e:
            logger.warning(f"Could not load preferences/memories: {e}")
            preferences = {}
            similar_memories = []

        # 2. Try dynamic LLM planning first
        if self._use_llm:
            llm_plan = await self._llm_create_plan(task, analysis, context, preferences, similar_memories)
            if llm_plan:
                return llm_plan

        # 3. Fallback to rule-based planning
        category = analysis["category"]
        steps = []
        
        # Always start with sentiment analysis for priority confirmation
        steps.append({
            "order": 1,
            "agent": "sentiment-analyzer",
            "capability": "analyze_sentiment",
            "params": {"text": task},
            "purpose": "Determine urgency from text sentiment"
        })
        
        # Classification step
        steps.append({
            "order": 2,
            "agent": "classifier",
            "capability": "classify_ticket",
            "params": {"ticket_text": task},
            "purpose": "Categorize the issue type"
        })
        
        # Category-specific steps
        if category == TaskCategory.DATABASE:
            steps.extend([
                {
                    "order": 3,
                    "agent": "browser",
                    "capability": "browse",
                    "params": {"url": "https://www.postgresql.org/docs/current/routine-vacuuming.html"},
                    "purpose": "Research database optimization solutions"
                },
                {
                    "order": 4,
                    "agent": "real-desktop-commander",
                    "capability": "execute_command",
                    "params": {"device_id": "db-server", "command": "pg_stat_activity"},
                    "purpose": "Check database activity"
                },
            ])
            
        elif category == TaskCategory.NETWORK:
            steps.extend([
                {
                    "order": 3,
                    "agent": "monitoring",
                    "capability": "collect_metrics",
                    "params": {},
                    "purpose": "Collect network metrics"
                },
                {
                    "order": 4,
                    "agent": "real-desktop-commander",
                    "capability": "execute_command",
                    "params": {"device_id": "router", "command": "netstat -an"},
                    "purpose": "Check network connections"
                },
            ])
            
        elif category == TaskCategory.APPLICATION:
            steps.extend([
                {
                    "order": 3,
                    "agent": "browser",
                    "capability": "browse",
                    "params": {"url": context.get("app_url", "http://localhost:8000/health") if context else "http://localhost:8000/health"},
                    "purpose": "Check application health"
                },
                {
                    "order": 4,
                    "agent": "monitoring",
                    "capability": "collect_metrics",
                    "params": {},
                    "purpose": "Collect application metrics"
                },
            ])

        elif category == TaskCategory.MONITORING:
            steps.extend([
                {
                    "order": 3,
                    "agent": "monitoring",
                    "capability": "monitor_system_health",
                    "params": {},
                    "purpose": "Check global system health and service status"
                },
                {
                    "order": 4,
                    "agent": "monitoring",
                    "capability": "collect_metrics",
                    "params": {},
                    "purpose": "Collect detailed system performance metrics"
                },
            ])
        
        # Always end with resolution
        steps.append({
            "order": len(steps) + 1,
            "agent": "resolver",
            "capability": "resolve_ticket",
            "params": {"ticket_id": "TKT-AUTO", "resolution_note": "Auto-resolved by Maestro"},
            "purpose": "Mark ticket as resolved"
        })
        
        return {
            "agents": list(set(s["agent"] for s in steps)),
            "steps": steps,
            "estimated_duration_sec": len(steps) * 5,
            "parallel_possible": False,
        }

    async def _llm_create_plan(
        self,
        task: str,
        analysis: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        preferences: Dict[str, Any],
        similar_memories: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """Use LLM (Ollama) to create a plan dynamically, utilizing past memories and user preferences."""
        try:
            # List available agents
            agents_response = await self.handle_list_agents()
            agents_info = agents_response.data.get("agents", []) if agents_response.success else []
            
            # Format context, memories, preferences for LLM
            import json
            agents_str = json.dumps(agents_info, indent=2)
            memories_str = json.dumps([
                {"task": m.task_description, "summary": m.summary, "steps": m.details.get("steps") if isinstance(m.details, dict) else []}
                for m in similar_memories
            ], indent=2, default=str)
            prefs_str = json.dumps(preferences, indent=2)
            
            prompt = f"""You are the TwisterLab Maestro Planner.
Your job is to generate a multi-agent execution plan (a series of steps) to solve the support ticket.

TASK: {task}
CATEGORY: {analysis['category'].value}
PRIORITY: {analysis['priority'].value}

USER PREFERENCES TO RESPECT:
{prefs_str}

RELEVANT PAST MEMORIES FOR RAG/GUIDANCE:
{memories_str}

AVAILABLE AGENTS AND CAPABILITIES:
{agents_str}

You must respond with a JSON object conforming exactly to this structure (no markdown, no other text):
{{
  "agents": ["agent-name-1", "agent-name-2"],
  "steps": [
    {{
      "order": 1,
      "agent": "agent-name",
      "capability": "capability-name",
      "params": {{ "param_key": "param_value" }},
      "purpose": "What this step does and why it is needed"
    }}
  ]
}}

Rules:
1. Always start with 'sentiment-analyzer' and its 'analyze_sentiment' capability.
2. Respect user preferences if any are specified (e.g. preferred agents or rules).
3. Generate only valid, execution-ready JSON. Do not include markdown code block backticks.
"""
            from twisterlab.services.registry import get_service_registry
            llm = get_service_registry().get_llm()
            llm_response = await llm.generate(prompt)
            
            # Clean response and load JSON
            import re
            clean_json = re.sub(r"```[a-zA-Z]*", "", llm_response).strip()
            plan_data = json.loads(clean_json)
            
            if "steps" in plan_data:
                # Ensure agents list is present and correct
                plan_data["agents"] = list(set(s["agent"] for s in plan_data["steps"]))
                plan_data["estimated_duration_sec"] = len(plan_data["steps"]) * 5
                plan_data["parallel_possible"] = False
                logger.info(f"📋 Dynamic LLM Plan created with {len(plan_data['steps'])} steps.")
                return plan_data
                
        except Exception as e:
            logger.warning(f"LLM planning failed: {e}. Falling back to rule-based planning.")
        return None

    # =========================================================================
    # EXECUTION ENGINE
    # =========================================================================

    async def _execute_plan(
        self, 
        plan: Dict[str, Any], 
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute the plan by dispatching to agents."""
        results = []
        
        for step in plan["steps"]:
            step_result = {
                "step": step["order"],
                "agent": step["agent"],
                "capability": step["capability"],
                "purpose": step["purpose"],
                "status": "pending",
            }
            
            try:
                agent = self._get_agent(step["agent"])
                if not agent:
                    step_result["status"] = "skipped"
                    step_result["reason"] = f"Agent {step['agent']} not available"
                    results.append(step_result)
                    continue
                
                # Execute the capability
                logger.info(f"  → Step {step['order']}: {step['agent']}.{step['capability']}")
                
                result = await agent.execute(step["capability"], **step["params"])
                
                step_result["status"] = "success" if result.success else "failed"
                step_result["data"] = result.data
                if result.error:
                    step_result["error"] = result.error
                    
            except Exception as e:
                step_result["status"] = "error"
                step_result["error"] = str(e)
                logger.error(f"Step {step['order']} failed: {e}")
            
            results.append(step_result)
        
        return results

    def _get_agent(self, agent_name: str):
        """Get agent from registry."""
        if not self.agent_registry:
            return None
        
        return self.agent_registry.get_agent(agent_name)

    # =========================================================================
    # SYNTHESIS ENGINE
    # =========================================================================

    async def _synthesize_results(
        self, 
        task: str, 
        results: List[Dict[str, Any]],
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize results into actionable summary."""
        
        successful_steps = [r for r in results if r["status"] == "success"]
        failed_steps = [r for r in results if r["status"] in ["failed", "error"]]
        
        # Extract key findings
        findings = []
        for result in successful_steps:
            if result["agent"] == "sentiment-analyzer" and result.get("data"):
                findings.append(f"Sentiment: {result['data'].get('sentiment', 'unknown')}")
            elif result["agent"] == "classifier" and result.get("data"):
                findings.append(f"Category: {result['data'].get('category', 'unknown')}")
        
        synthesis = {
            "summary": f"Processed '{task[:50]}...' with {len(successful_steps)}/{len(results)} successful steps",
            "findings": findings,
            "success_rate": len(successful_steps) / len(results) if results else 0,
            "recommendation": self._generate_recommendation(analysis, results),
            "requires_human": len(failed_steps) > 0,
        }
        
        return synthesis

    def _generate_recommendation(
        self, 
        analysis: Dict[str, Any], 
        results: List[Dict[str, Any]]
    ) -> str:
        """Generate a recommendation based on results."""
        
        category = analysis["category"]
        priority = analysis["priority"]
        
        if priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
            prefix = "⚠️ HIGH PRIORITY: "
        else:
            prefix = ""
        
        recommendations = {
            TaskCategory.DATABASE: f"{prefix}Check slow queries, run VACUUM ANALYZE, verify indexes.",
            TaskCategory.NETWORK: f"{prefix}Verify firewall rules, check DNS, test connectivity.",
            TaskCategory.SECURITY: f"{prefix}Review access logs, check for unauthorized access, enable 2FA.",
            TaskCategory.INFRASTRUCTURE: f"{prefix}Monitor resources, check disk space, restart services if needed.",
            TaskCategory.APPLICATION: f"{prefix}Check logs, verify dependencies, test endpoints.",
            TaskCategory.UNKNOWN: f"{prefix}Gather more information, escalate if needed.",
        }
        
        return recommendations.get(category, "Continue investigation.")

    def _calculate_duration(self, task: OrchestratedTask) -> int:
        """Calculate task duration in milliseconds."""
        if not task.completed_at:
            return 0
        try:
            start = datetime.fromisoformat(task.created_at)
            end = datetime.fromisoformat(task.completed_at)
            return int((end - start).total_seconds() * 1000)
        except Exception:
            return 0


__all__ = ["RealMaestroAgent", "TaskPriority", "TaskCategory", "OrchestratedTask"]
