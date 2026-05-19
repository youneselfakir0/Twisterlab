"""
RealMaestroAgent - The Orchestrator Brain

Modernized v3.8.2 Refinement: Capability-Driven Discovery
Decoupled planning from specific agent names.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

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
try:
    from twisterlab.agents.prompts.loader import PromptLoader
except ImportError:
    PromptLoader = None


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
    INTELLIGENCE = "intelligence"
    TRADING = "trading"
    UNKNOWN = "unknown"


@dataclass
class OrchestratedTask:
    id: str
    description: str
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.UNKNOWN
    # List of agent IDs or capability requirements involved
    requirements_involved: List[str] = field(default_factory=list)
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

    async def handle_orchestrate(
        self, 
        task: str, 
        context: Optional[Dict[str, Any]] = None, 
        dry_run: bool = False,
        lookup_fn: Optional[Callable[[str], Any]] = None
    ) -> AgentResponse:
        """Main orchestration loop: Analyze -> Resolve -> Execute -> Synthesize."""
        logger.info(f"Maestro orchestrating: {task[:100]}...")
        
        try:
            from twisterlab.monitoring_utils import mission_timer
        except ImportError:
            mission_timer = None

        analysis = await self._analyze_task(task, context)
        category = analysis["category"]
        priority = analysis["priority"]
        
        timer_ctx = None
        if mission_timer:
            timer_ctx = mission_timer(category.value, priority.value)
            timer_ctx.__enter__()

        try:
            # 1. Intent Mapping
            requirements = analysis["suggested_requirements"]
            
            orchestrated = OrchestratedTask(
                id=f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                description=task,
                category=category,
                priority=priority,
                requirements_involved=requirements
            )
            
            plan = await self._create_plan(task, analysis, context)
            orchestrated.requirements_involved = plan["requirements"]
            orchestrated.steps = plan["steps"]
            
            if dry_run:
                return AgentResponse(success=True, data={
                    "mode": "dry_run",
                    "task_id": orchestrated.id,
                    "analysis": {"category": orchestrated.category.value, "priority": orchestrated.priority.value},
                    "plan": plan,
                })
            
            results = await self._execute_plan(plan, task, context, lookup_fn=lookup_fn)
            orchestrated.results = results
            orchestrated.status = "completed"
            orchestrated.completed_at = datetime.now(timezone.utc).isoformat()
            
            synthesis = await self._synthesize_results(task, results, analysis)
            
            return AgentResponse(success=True, data={
                "task_id": orchestrated.id,
                "status": "completed",
                "analysis": {"category": orchestrated.category.value, "priority": orchestrated.priority.value},
                "requirements_used": orchestrated.requirements_involved,
                "steps_executed": len(orchestrated.steps),
                "results": results,
                "synthesis": synthesis,
            })
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return AgentResponse(success=False, error=str(e))
        finally:
            if timer_ctx:
                timer_ctx.__exit__(None, None, None)

    async def handle_analyze_task(self, task: str) -> AgentResponse:
        analysis = await self._analyze_task(task, None)
        return AgentResponse(success=True, data={
            "category": analysis["category"].value,
            "priority": analysis["priority"].value,
            "suggested_requirements": analysis["suggested_requirements"],
            "keywords": analysis["keywords"],
        })

    def _robust_json_parse(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text using regex and parse it safely."""
        import json
        import re
        
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Try extracting JSON block
        try:
            # Look for everything between the first { and the last }
            match = re.search(r"(\{.*\})", text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except (json.JSONDecodeError, AttributeError):
            pass
            
        # Last resort: try to clean common LLM artifacts (markdown backticks)
        try:
            clean_text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_text)
        except json.JSONDecodeError:
            return {}

    async def _analyze_task(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if self._use_llm and httpx:
            llm_analysis = await self._llm_analyze(task, context)
            if llm_analysis:
                return llm_analysis
        return self._rule_based_analyze(task, context)

    async def _llm_analyze(self, task: str, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        try:
            if not PromptLoader:
                logger.warning("PromptLoader missing, cannot perform LLM analysis.")
                return None
                
            prompt = PromptLoader.get("maestro_analysis", task=task)

            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._ollama_url}/api/generate",
                    json={"model": self._ollama_model, "prompt": prompt, "stream": False}
                )
                if response.status_code == 200:
                    result = response.json()
                    analysis_raw = result.get("response", "{}")
                    analysis = self._robust_json_parse(analysis_raw)

                    if self._validate_analysis(analysis):
                        return self._map_analysis_to_enums(analysis)
                    
                    # --- REPAIR ATTEMPT (Phase 4.1) ---
                    logger.warning(f"initial_validation_failed for {self.name}_analysis")
                    logger.info("repair_attempt_started: Re-invoking LLM with corrective hint")
                    
                    repair_prompt = f"{prompt}\n\n[REPAIR HINT]: Your previous response was invalid JSON or missing required keys. Response MUST be a JSON object with 'category', 'priority', and 'suggested_requirements'. JSON STRICT ONLY."
                    
                    response = await client.post(
                        f"{self._ollama_url}/api/generate",
                        json={"model": self._ollama_model, "prompt": repair_prompt, "stream": False, "format": "json"}
                    )
                    
                    if response.status_code == 200:
                        repair_res = response.json()
                        analysis_repaired = self._robust_json_parse(repair_res.get("response", "{}"))
                        
                        if self._validate_analysis(analysis_repaired):
                            logger.info("repair_succeeded: LLM corrected the output schema")
                            return self._map_analysis_to_enums(analysis_repaired)
                        else:
                            logger.warning("repair_failed_fallback: Second attempt also failed validation")
                    else:
                        logger.warning(f"repair_failed_fallback: LLM error {response.status_code}")
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
        return None

    def _map_analysis_to_enums(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw JSON strings to TaskCategory and TaskPriority enums."""
        return {
            "category": TaskCategory(analysis.get("category", "unknown")),
            "priority": TaskPriority(analysis.get("priority", "medium")),
            "suggested_requirements": analysis.get("suggested_requirements", []),
            "keywords": analysis.get("keywords", []),
            "source": "llm",
        }

    def _validate_analysis(self, data: Dict[str, Any]) -> bool:
        """Validate the LLM analysis JSON against the expected schema."""
        required_keys = ["category", "priority", "suggested_requirements"]
        if not all(key in data for key in required_keys):
            return False
        
        # Validate allowed enums for category
        allowed_categories = [c.value for c in TaskCategory]
        if data["category"] not in allowed_categories:
            return False
        
        # Validate allowed enums for priority
        allowed_priorities = [p.value for p in TaskPriority]
        if data["priority"] not in allowed_priorities:
            return False
            
        return True

    def _rule_based_analyze(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        import re
        task_lower = task.lower()
        category = TaskCategory.UNKNOWN
        keywords = []
        suggested_requirements = ["analyze_sentiment", "classify_ticket"]
        
        def has_kw(kws):
            return any(re.search(rf"\b{re.escape(kw)}\b", task_lower) for kw in kws)

        # INTELLIGENCE tasks (Moved up for priority)
        if has_kw(["veille", "news", "intelligence", "market", "competitor", "watch", "rss"]):
            category = TaskCategory.INTELLIGENCE
            keywords = ["intelligence", "watch"]
            suggested_requirements.extend(["browse", "summarize", "translate", "create_page", "n8n_trigger_webhook", "archive_result"])

        # TRADING tasks
        elif has_kw(["bitcoin", "btc", "eth", "ethereum", "sol", "crypto", "trading", "scalp", "market", "analysis", "kucoin"]):
            category = TaskCategory.TRADING
            keywords = ["crypto", "trading"]
            suggested_requirements.extend(["analyze_market", "summarize", "translate", "create_page"])

        # DATABASE tasks
        elif has_kw(["database", "sql", "postgres", "mysql", "query", "db", "table", "connection pool"]):
            category = TaskCategory.DATABASE
            keywords = ["database", "sql"]
            suggested_requirements.extend(["db_health", "create_backup"])
        
        # NETWORK tasks
        elif has_kw(["network", "connection", "timeout", "dns", "ping", "latency"]):
            category = TaskCategory.NETWORK
            keywords = ["network", "connectivity"]
            suggested_requirements.extend(["monitor_system_health", "browse"])
        
        # SECURITY tasks
        elif has_kw(["security", "breach", "hack", "vulnerability", "attack", "intrusion"]):
            category = TaskCategory.SECURITY
            keywords = ["security", "threat"]
            suggested_requirements.extend(["create_backup", "security_scan"])
        
        # MONITORING/SYSTEM tasks
        elif has_kw(["cpu", "memory", "disk", "uptime", "top", "ps", "df", "du", "system status", "metrics", "monitoring"]):
            category = TaskCategory.MONITORING
            keywords = ["monitoring", "system"]
            suggested_requirements.extend(["monitor_system_health", "execute_command"])
        
        # INFRASTRUCTURE tasks
        elif has_kw(["server", "crash", "restart", "deploy", "kubernetes", "pod", "container"]):
            category = TaskCategory.INFRASTRUCTURE
            keywords = ["infrastructure", "server"]
            suggested_requirements.extend(["monitor_system_health", "execute_command"])
        
        # APPLICATION tasks
        elif has_kw(["app", "application", "error", "bug", "500", "404", "api", "endpoint"]):
            category = TaskCategory.APPLICATION
            keywords = ["application", "error"]
            suggested_requirements.extend(["browse", "monitor_system_health"])
        
        # INTELLIGENCE tasks
        elif any(kw in task_lower for kw in ["veille", "news", "intelligence", "market", "competitor", "watch", "rss", "browse"]):
            category = TaskCategory.INTELLIGENCE
            keywords = ["intelligence", "watch"]
            suggested_requirements.extend(["browse", "summarize", "translate", "create_page", "n8n_trigger_webhook", "archive_result"])
        
        # Priority detection
        priority = TaskPriority.MEDIUM
        if any(kw in task_lower for kw in ["urgent", "critical", "down", "crash", "emergency", "outage", "!!!"]):
            priority = TaskPriority.CRITICAL
        elif any(kw in task_lower for kw in ["important", "high", "production", "asap"]):
            priority = TaskPriority.HIGH
        elif any(kw in task_lower for kw in ["minor", "low", "when possible", "nice to have"]):
            priority = TaskPriority.LOW
        
        return {"category": category, "priority": priority, "suggested_requirements": list(set(suggested_requirements)), "keywords": keywords, "source": "rules"}

    async def _create_plan(self, task: str, analysis: Dict[str, Any], context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        category = analysis["category"]
        steps = [
            {"order": 1, "requirement": "analyze_sentiment", "params": {"text": task}, "purpose": "Determine urgency"},
            {"order": 2, "requirement": "classify_ticket", "params": {"ticket_text": task}, "purpose": "Categorize issue"},
        ]
        
        # Add category-specific steps using functional REQUIREMENTS
        if category == TaskCategory.DATABASE:
            steps.append({"order": 3, "requirement": "db_health", "params": {}, "purpose": "Check database health"})
            steps.append({"order": 4, "requirement": "create_backup", "params": {"service_name": "database"}, "purpose": "Create safety backup"})
        
        elif category == TaskCategory.MONITORING:
            steps.append({"order": 3, "requirement": "monitor_system_health", "params": {}, "purpose": "Collect system metrics"})
            steps.append({"order": 4, "requirement": "execute_command", "params": {"command": "uptime"}, "purpose": "Check system uptime"})
        
        elif category == TaskCategory.INFRASTRUCTURE:
            steps.append({"order": 3, "requirement": "monitor_system_health", "params": {}, "purpose": "Collect metrics"})
            steps.append({"order": 4, "requirement": "execute_command", "params": {"command": "df -h"}, "purpose": "Check disk usage"})
        
        elif category == TaskCategory.APPLICATION:
            steps.append({"order": 3, "requirement": "browse", "params": {"url": "http://localhost:8000/health"}, "purpose": "Check app health"})
        
        elif category == TaskCategory.SECURITY:
            steps.append({"order": 3, "requirement": "create_backup", "params": {"service_name": "security-snapshot"}, "purpose": "Emergency backup"})
            steps.append({"order": 4, "requirement": "security_scan", "params": {"code": "# Security incident check"}, "purpose": "Security scan"})
        
        elif category == TaskCategory.NETWORK:
            steps.append({"order": 3, "requirement": "monitor_system_health", "params": {}, "purpose": "Check network metrics"})
        
        elif category == TaskCategory.INTELLIGENCE:
            # THE SUPER MISSION PLAN - REFINED v3.8.2 (Capability Driven)
            steps.append({"order": 3, "requirement": "browse", "params": {"url": "https://news.google.com"}, "purpose": "Acquire market intelligence"})
            steps.append({"order": 4, "requirement": "summarize", "params": {"text": "{{step_3_result}}"}, "purpose": "Condense intelligence"})
            steps.append({"order": 5, "requirement": "translate", "params": {"text": "{{step_4_result}}", "target_language": "french"}, "purpose": "Localize report"})
            steps.append({"order": 6, "requirement": "create_page", "params": {"title": "Rapport Intelligence Atlas (Rich)", "content": "{{step_5_result}}"}, "purpose": "Documentation"})
            steps.append({"order": 7, "requirement": "n8n_trigger_webhook", "params": {"webhook_path": "twister-intelligence"}, "purpose": "Notify stakeholders"})
            steps.append({"order": 8, "requirement": "archive_result", "params": {"mission_id": "ATLAS_INTEL_V2", "data": {"type": "SuperMission_Chained", "report": "{{step_5_result}}"}}, "purpose": "Persistent storage"})

        elif category == TaskCategory.TRADING:
            # THE TRADING MISSION PLAN - Phase 5-A (Market Analysis)
            # Default to BTC-USDT if not specified in task, though ideally we extract it.
            # For now, let's assume 'analyze_market' will use the task string if we passed it correctly, 
            # or Maestro can be smart.
            import re
            symbol_match = re.search(r'([A-Z0-9]+-[A-Z0-9]+)', task.upper())
            symbol = symbol_match.group(1) if symbol_match else "BTC-USDT"
            
            steps.append({"order": 3, "requirement": "analyze_market", "params": {"symbol": symbol, "timeframe": "1hour"}, "purpose": "Fetch crypto market intelligence"})
            steps.append({"order": 4, "requirement": "summarize", "params": {"text": "{{step_3_result.summary}}"}, "purpose": "Structure analysis report"})
            steps.append({"order": 5, "requirement": "translate", "params": {"text": "{{step_4_result}}", "target_language": "french"}, "purpose": "Localize findings for dashboard"})
            steps.append({"order": 6, "requirement": "create_page", "params": {"title": f"Rapport Trading {symbol}", "content": "{{step_5_result}}"}, "purpose": "Publish report to workspace"})
        
        # Always end with resolution
        steps.append({"order": len(steps) + 1, "requirement": "resolve_ticket", "params": {"ticket_id": "TKT-AUTO", "resolution_note": f"Auto-resolved by Maestro ({category.value})"}, "purpose": "Mark resolved"})
        
        return {"requirements": list(set(s["requirement"] for s in steps)), "steps": steps, "estimated_duration_sec": len(steps) * 5}

    async def _execute_plan(
        self, 
        plan: Dict[str, Any], 
        task: str, 
        context: Optional[Dict[str, Any]],
        lookup_fn: Optional[Callable[[str], Any]] = None
    ) -> List[Dict[str, Any]]:
        results = {}  # Store results by step number for chaining
        execution_log = []
        
        for step in plan["steps"]:
            step_num = step["order"]
            requirement = step["requirement"]
            step_result = {"step": step_num, "requirement": requirement, "status": "pending"}
            
            try:
                # 1. RESOLVE REQUIREMENT TO ADAPTER
                # If lookup_fn is provided, it handles the agent resolution and adapter wrapping.
                # Crucial: the lookup_fn now supports capability-to-agent resolution.
                adapter = self._resolve_requirement_to_adapter(requirement, lookup_fn=lookup_fn)
                
                if not adapter:
                    step_result["status"] = "skipped"
                    step_result["reason"] = f"No agent found for requirement: {requirement}"
                else:
                    step_result["agent"] = adapter.agent_name # Record who actually did it

                    # 2. DYNAMIC PARAMETER SUBSTITUTION
                    processed_params = {}
                    for k, v in step.get("params", {}).items():
                        if isinstance(v, str) and "{{" in v and "}}" in v:
                            import re
                            matches = re.findall(r"\{\{step_(\d+)_result\.?(\w+)?\}\}", v)
                            for match_num, match_key in matches:
                                prev_res = results.get(int(match_num))
                                if prev_res:
                                    val = ""
                                    if match_key:
                                        val = prev_res.get(match_key, "")
                                    else:
                                        val = (
                                            prev_res.get("summary") or 
                                            prev_res.get("content") or 
                                            prev_res.get("content_preview") or 
                                            prev_res.get("translated_text") or 
                                            prev_res.get("text") or 
                                            str(prev_res)
                                        )
                                    v = v.replace(f"{{{{step_{match_num}_result" + (f".{match_key}" if match_key else "") + "}}}}", str(val))
                            processed_params[k] = v
                        else:
                            processed_params[k] = v

                    if processed_params:
                        logger.info(f"🚀 [maestro] Step {step_num} ({requirement}) Dynamic Params: {list(processed_params.keys())}")

                    # 3. EXECUTE THROUGH ADAPTER (WITH SELF-HEALING RETRIES)
                    max_retries = 2
                    attempt = 0
                    result = None
                    
                    while attempt <= max_retries:
                        try:
                            result = await adapter.call(requirement, **processed_params)
                            if result.success:
                                break
                            
                            # Success is False, attempt self-healing
                            error_msg = result.error or "Unknown failure"
                            heal_action = await self._attempt_self_healing(requirement, error_msg, processed_params, lookup_fn)
                            if not heal_action:
                                break  # No healing action matched, abort retries
                                
                            attempt += 1
                            logger.info(f"🔄 [maestro] Retrying step {step_num} ({requirement}) - Attempt {attempt}/{max_retries}...")
                        except Exception as step_ex:
                            error_msg = str(step_ex)
                            heal_action = await self._attempt_self_healing(requirement, error_msg, processed_params, lookup_fn)
                            if not heal_action:
                                raise step_ex
                                
                            attempt += 1
                            logger.info(f"🔄 [maestro] Retrying step {step_num} ({requirement}) after exception - Attempt {attempt}/{max_retries}...")
                    
                    # If execution finished with no result, build a default failed state
                    if not result:
                        from twisterlab.agents.base.response import AgentResponse
                        result = AgentResponse(success=False, error="Self-healing retries exhausted")

                    # 4. CANONICAL ENVELOPE TRUST
                    step_result["status"] = "success" if result.success else "failed"
                    step_result["data"] = result.data
                    if result.success:
                        results[step_num] = result.data
                    if result.error:
                        step_result["error"] = result.error
                        
            except Exception as e:
                logger.error(f"Maestro: step {step_num} exception: {e}")
                step_result["status"] = "error"
                step_result["error"] = str(e)
            
            execution_log.append(step_result)
        return execution_log

    async def _attempt_self_healing(
        self, 
        requirement: str, 
        error_msg: str, 
        processed_params: Dict[str, Any],
        lookup_fn: Optional[Callable[[str], Any]] = None
    ) -> Optional[str]:
        """
        Intelligent self-healing agent router.
        Diagnoses failures in real-time and coordinates with resolver/sync agents to heal.
        """
        logger.warning(f"🔧 [SELF-HEALING ACTIVE] Diagnosing failure for capability '{requirement}': {error_msg}")
        
        # 1. Database Connection pool issues or SQL errors
        if any(kw in error_msg.lower() for kw in ["database", "sql", "connection pool", "operationalerror", "psycopg2"]):
            logger.info("🔧 [SELF-HEALING] Detected database connectivity error. Dispatching 'db_health' diagnostics...")
            db_adapter = self._resolve_requirement_to_adapter("db_health", lookup_fn)
            if db_adapter:
                health_check = await db_adapter.call("db_health")
                logger.info(f"  Diagnostics check status: {health_check.success} | data: {health_check.data}")
            
            # Perform short delay and return retry signal
            import asyncio
            await asyncio.sleep(2.0)
            return "retry"

        # 2. Redis / Cache validation failures
        elif any(kw in error_msg.lower() for kw in ["redis", "cache", "keyerror", "connectionerror"]):
            logger.info("🔧 [SELF-HEALING] Detected Redis/Cache degradation. PURGING stale synchronization keys...")
            cache_del_adapter = self._resolve_requirement_to_adapter("cache_delete", lookup_fn)
            if cache_del_adapter:
                # Purge potential lock states
                await cache_del_adapter.call("cache_delete", key="lock:maestro:*")
                await cache_del_adapter.call("cache_delete", key="lock:trading:*")
                logger.info("  Purged transient cache locks. Retrying execution.")
            
            import asyncio
            await asyncio.sleep(1.0)
            return "retry"

        # 3. LLM Gateway / Ollama Timeouts or bad formatting
        elif any(kw in error_msg.lower() for kw in ["ollama", "timeout", "bad gateway", "jsondecodeerror", "validation"]):
            logger.info("🔧 [SELF-HEALING] Detected Ollama/LLM gateway failure. Switching to secondary backup model configuration...")
            # Modify parameter configuration to use a lighter schema or fallback model
            if "model" in processed_params:
                processed_params["model"] = "llama3.2:1b"  # fallback safe model
            
            # Format fallback prompt repair
            if "prompt" in processed_params:
                processed_params["prompt"] = f"{processed_params['prompt']}\n\n[SELF-HEALING SAFE FORMAT ONLY]"
            
            import asyncio
            await asyncio.sleep(1.5)
            return "retry"

        # 4. General API & Network Outage
        elif any(kw in error_msg.lower() for kw in ["network", "http", "http-status", "404", "500", "status_code"]):
            logger.info("🔧 [SELF-HEALING] Detected external API/network outage. Activating fallback mode...")
            # We can log the event to our resolver agent to mark a support ticket for post-incident review
            resolver_adapter = self._resolve_requirement_to_adapter("resolve_ticket", lookup_fn)
            if resolver_adapter:
                await resolver_adapter.call(
                    "resolve_ticket", 
                    ticket_id="TKT-HEAL", 
                    resolution_note=f"[SELF-HEALING LOG] Auto-recovered agent failure for '{requirement}': {error_msg}"
                )
            
            import asyncio
            await asyncio.sleep(3.0)
            return "retry"

        return None

    def _resolve_requirement_to_adapter(self, requirement: str, lookup_fn: Optional[Callable[[str], Any]] = None):
        """
        Resolves a functional requirement to an AgentAdapter.
        Uses discovery sequence: 
        1. Injectable lookup_fn (Phase 2 service logic)
        2. Local registry discovery
        """
        if lookup_fn:
            # We first try to resolve the requirement to a specific agent name via the registry
            if self.agent_registry and hasattr(self.agent_registry, "find_agent_by_capability"):
                agent_name = self.agent_registry.find_agent_by_capability(requirement)
                if agent_name:
                    return lookup_fn(agent_name)
            
            # Fallback: pass requirement directly to lookup_fn
            return lookup_fn(requirement)
            
        # Hard fallback to registry (less secure but functional for testing)
        if not self.agent_registry:
            return None
            
        agent_name = requirement
        if hasattr(self.agent_registry, "find_agent_by_capability"):
            agent_name = self.agent_registry.find_agent_by_capability(requirement) or requirement
            
        agent_instance = self.agent_registry.get_agent(agent_name)
        if not agent_instance:
            return None
            
        from twisterlab.agents.base.adapter import AgentAdapter
        return AgentAdapter(agent_instance)

    async def _synthesize_results(self, task: str, results: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize logs into a structured intelligence report via LLM."""
        if not self._use_llm or not httpx or not PromptLoader:
            return self._rule_based_synthesis(results)

        try:
            prompt = PromptLoader.get("maestro_synthesis")
            full_prompt = f"{prompt}\n\nORIGINAL TASK: {task}\n\nAGENT RESULTS:\n{results}\n\nSynthesized Intelligence:"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._ollama_url}/api/generate",
                    json={"model": self._ollama_model, "prompt": full_prompt, "stream": False}
                )
                if response.status_code == 200:
                    result = response.json()
                    synthesis_raw = result.get("response", "{}")
                    synthesis = self._robust_json_parse(synthesis_raw)

                    if self._validate_synthesis(synthesis):
                        return synthesis
                    
                    # --- REPAIR ATTEMPT (Phase 4.1) ---
                    logger.warning(f"initial_validation_failed for {self.name}_synthesis")
                    logger.info("repair_attempt_started: Re-invoking LLM with corrective hint")
                    
                    repair_prompt = f"{full_prompt}\n\n[REPAIR HINT]: Your previous response was invalid JSON or missing keys. Response MUST be JSON with 'summary', 'findings', 'success_rate', and 'requires_human'. JSON STRICT ONLY."
                    
                    response = await client.post(
                        f"{self._ollama_url}/api/generate",
                        json={"model": self._ollama_model, "prompt": repair_prompt, "stream": False, "format": "json"}
                    )
                    
                    if response.status_code == 200:
                        repair_res = response.json()
                        synthesis_repaired = self._robust_json_parse(repair_res.get("response", "{}"))
                        
                        if self._validate_synthesis(synthesis_repaired):
                            logger.info("repair_succeeded: LLM corrected the synthesis schema")
                            return synthesis_repaired
                        else:
                            logger.warning("repair_failed_fallback: Second attempt failed validation")
                    else:
                        logger.warning(f"repair_failed_fallback: LLM error {response.status_code}")
        except Exception as e:
            logger.warning(f"LLM synthesis failed: {e}")
        
        return self._rule_based_synthesis(results)

    def _validate_synthesis(self, data: Dict[str, Any]) -> bool:
        """Validate the LLM synthesis JSON against the expected schema."""
        required_keys = ["summary", "findings", "success_rate", "requires_human"]
        if not all(key in data for key in required_keys):
            return False
            
        if not isinstance(data["findings"], list):
            return False
            
        if not isinstance(data["success_rate"], (int, float)):
            return False
            
        return True

    def _rule_based_synthesis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        successful_steps = [r for r in results if r["status"] == "success"]
        findings = []
        for r in successful_steps:
            req = r.get("requirement")
            if req == "analyze_sentiment" and r.get("data"):
                findings.append(f"Sentiment: {r['data'].get('sentiment', 'unknown')}")
            elif req == "classify_ticket" and r.get("data"):
                findings.append(f"Category: {r['data'].get('category', 'unknown')}")
        
        return {
            "summary": f"Processed task with {len(successful_steps)}/{len(results)} successful steps (Rule-based fallback)",
            "findings": findings,
            "success_rate": len(successful_steps) / len(results) if results else 0,
            "requires_human": len(results) - len(successful_steps) > 0,
        }



__all__ = ["RealMaestroAgent", "TaskPriority", "TaskCategory", "OrchestratedTask"]
