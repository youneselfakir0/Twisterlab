from __future__ import annotations
import json
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import select, or_, text, update

from twisterlab.database.session import AsyncSessionLocal
from twisterlab.database.models.learning import Skill, AgentMemory, ScheduledTask, UserProfile
from twisterlab.services.registry import get_service_registry

logger = logging.getLogger(__name__)

# =========================================================================
# CRON PARSER AND CALCULATION UTILITIES
# =========================================================================

def parse_cron_field(field: str, val: int, min_val: int, max_val: int) -> bool:
    """Check if a value matches a cron field pattern."""
    if field == "*":
        return True
    if field.startswith("*/"):
        try:
            step = int(field[2:])
            return val % step == 0
        except ValueError:
            return False
    if "," in field:
        parts = field.split(",")
        try:
            return str(val) in parts or val in [int(p) for p in parts if p.isdigit()]
        except Exception:
            return False
    if "-" in field:
        try:
            start, end = map(int, field.split("-"))
            return start <= val <= end
        except ValueError:
            return False
    if field.isdigit():
        return val == int(field)
    return False

def matches_cron(cron: str, dt: datetime) -> bool:
    """Check if the datetime matches the cron expression."""
    fields = cron.split()
    if len(fields) < 5:
        return False
    min_ok = parse_cron_field(fields[0], dt.minute, 0, 59)
    hour_ok = parse_cron_field(fields[1], dt.hour, 0, 23)
    day_ok = parse_cron_field(fields[2], dt.day, 1, 31)
    month_ok = parse_cron_field(fields[3], dt.month, 1, 12)
    
    # weekday: 0 is Monday ... 6 is Sunday in python. Cron 0 or 7 is Sunday.
    weekday = dt.weekday()
    cron_weekday = (weekday + 1) % 7
    weekday_ok = parse_cron_field(fields[4], cron_weekday, 0, 6)
    
    return min_ok and hour_ok and day_ok and month_ok and weekday_ok

def calculate_next_run(cron: str, start_dt: datetime) -> datetime:
    """Calculate the next execution datetime based on a cron expression."""
    # Zero out seconds and microseconds to evaluate on a minute basis
    dt = start_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    # Search limit: ~70 days
    for _ in range(100000):
        if matches_cron(cron, dt):
            return dt
        dt += timedelta(minutes=1)
    # Fallback to tomorrow
    return start_dt.replace(second=0, microsecond=0) + timedelta(days=1)


# =========================================================================
# MEMORY SERVICE (Persistent Memory with FTS & LLM Summaries)
# =========================================================================

class MemoryService:
    @staticmethod
    async def save_memory(
        task_description: str,
        execution_results: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> AgentMemory:
        """Summarize the execution results via LLM and save to the persistent database."""
        logger.info(f"💾 Saving memory for task: {task_description[:50]}...")
        
        # 1. Ask LLM to summarize what was done, what succeeded, what failed, and what was learned
        llm = get_service_registry().get_llm()
        
        successful_steps = [r for r in execution_results if r.get("status") == "success"]
        failed_steps = [r for r in execution_results if r.get("status") in ["failed", "error"]]
        
        prompt = f"""Synthesize this executed multi-agent workflow into a concise, cross-session memory summary.
Original Task: {task_description}
Successful Steps: {json.dumps(successful_steps, indent=2, default=str)}
Failed Steps: {json.dumps(failed_steps, indent=2, default=str)}

Respond with a concise, factual summary (maximum 3 sentences) describing:
1. The problem encountered.
2. The exact resolution or findings.
3. Lessons learned or recommendations for future similar tasks.
Do not mention step numbers or intermediate json formatting in the final output. Write only the summary.
"""
        try:
            summary = await llm.generate(prompt)
        except Exception as e:
            logger.warning(f"LLM memory summarization failed: {e}. Using fallback summary.")
            summary = f"Executed {len(execution_results)} steps for task. Succeeded: {len(successful_steps)}, Failed: {len(failed_steps)}."

        # 2. Persist in database
        async with AsyncSessionLocal() as db:
            memory = AgentMemory(
                session_id=session_id or f"session_{datetime.now().strftime('%Y%m%d')}",
                task_description=task_description,
                summary=summary,
                details={
                    "steps": execution_results,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            db.add(memory)
            await db.commit()
            await db.refresh(memory)
            logger.info(f"💾 Memory saved successfully with ID: {memory.id}")
            return memory

    @staticmethod
    async def search_memories(query: str, limit: int = 5) -> List[AgentMemory]:
        """Perform Full-Text Search or LIKE fallback across persistent agent memories."""
        logger.info(f"🔍 Searching memories for: '{query}'")
        async with AsyncSessionLocal() as db:
            bind = db.bind
            # Check database dialect to see if we can use Postgres FTS
            is_postgres = bind.dialect.name == "postgresql"
            
            if is_postgres:
                # Use PostgreSQL Full Text Search
                stmt = select(AgentMemory).where(
                    or_(
                        text("to_tsvector('english', task_description) @@ plainto_tsquery('english', :query)"),
                        text("to_tsvector('english', summary) @@ plainto_tsquery('english', :query)"),
                        AgentMemory.task_description.ilike(f"%{query}%"),
                        AgentMemory.summary.ilike(f"%{query}%")
                    )
                ).params(query=query).order_by(AgentMemory.created_at.desc()).limit(limit)
            else:
                # Use SQLite / generic LIKE fallback
                stmt = select(AgentMemory).where(
                    or_(
                        AgentMemory.task_description.ilike(f"%{query}%"),
                        AgentMemory.summary.ilike(f"%{query}%")
                    )
                ).order_by(AgentMemory.created_at.desc()).limit(limit)
                
            result = await db.execute(stmt)
            return list(result.scalars().all())


# =========================================================================
# LEARNING SERVICE (Closed-loop learning & Skill Auto-generation)
# =========================================================================

class LearningService:
    @staticmethod
    async def find_matching_skill(task: str) -> Optional[Skill]:
        """Find a reusable skill that matches the user's task request."""
        logger.info(f"🧠 Checking for reusable skills for: '{task[:50]}'")
        async with AsyncSessionLocal() as db:
            # Load all skills to evaluate keywords (or perform simple SQL match)
            stmt = select(Skill)
            result = await db.execute(stmt)
            skills = result.scalars().all()
            
            task_lower = task.lower()
            best_match: Optional[Skill] = None
            max_keyword_matches = 0
            
            for skill in skills:
                keywords = [kw.strip().lower() for kw in (skill.trigger_keywords or "").split(",") if kw.strip()]
                matches = sum(1 for kw in keywords if kw in task_lower)
                
                # Check for direct description overlap or keyword matches
                if matches > max_keyword_matches:
                    max_keyword_matches = matches
                    best_match = skill
                    
            if best_match and max_keyword_matches > 0:
                logger.info(f"🎯 Found matching skill: '{best_match.name}' (ID: {best_match.id}) with {max_keyword_matches} keyword matches.")
                return best_match
                
        return None

    @staticmethod
    async def extract_and_save_skill(
        task_description: str,
        execution_results: List[Dict[str, Any]]
    ) -> Optional[Skill]:
        """Analyze a successful complex orchestration and auto-generate a reusable Skill."""
        successful_steps = [r for r in execution_results if r.get("status") == "success"]
        # Only extract skills for successful runs with 2 or more steps
        if len(successful_steps) < 2:
            return None

        logger.info("🧠 Learning Loop: Analyzing successful execution to extract reusable skill...")
        
        llm = get_service_registry().get_llm()
        prompt = f"""You are the TwisterLab Auto-Learning Agent.
Analyze this successfully completed multi-agent orchestration task and extract a general, reusable 'Skill' workflow.

Original Task: {task_description}
Executed Steps: {json.dumps(successful_steps, indent=2, default=str)}

Respond with a valid JSON structure ONLY containing:
{{
  "id": "a unique snake_case string, e.g., 'database_vacuum_optimize'",
  "name": "A concise human-readable name, e.g., 'Database Optimization Workflow'",
  "description": "What this skill does and when it should be triggered",
  "trigger_keywords": ["comma", "separated", "keywords", "relevant", "to", "triggering"],
  "steps": [
    {{
      "order": 1,
      "agent": "agent-name",
      "capability": "capability-name",
      "params": {{ "param_key": "param_value_or_curly_braces_parameter" }},
      "purpose": "Step purpose"
    }}
  ]
}}
Ensure the steps are clean and generalized. Write only the raw JSON. No markdown backticks, no explanations.
"""
        try:
            llm_response = await llm.generate(prompt)
            # Strip markdown code blocks if any
            clean_json = re.sub(r"```[a-zA-Z]*", "", llm_response).strip()
            skill_data = json.loads(clean_json)
            
            # Check fields
            skill_id = skill_data.get("id", f"skill_{int(datetime.now().timestamp())}")
            name = skill_data.get("name", "Auto-generated Skill")
            description = skill_data.get("description", "Reusable skill workflow")
            keywords_list = skill_data.get("trigger_keywords", [])
            trigger_keywords = ",".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)
            steps = skill_data.get("steps", [])

            async with AsyncSessionLocal() as db:
                # Check if skill already exists
                stmt = select(Skill).where(Skill.id == skill_id)
                res = await db.execute(stmt)
                existing = res.scalar_one_or_none()

                if existing:
                    # Update existing skill usage stats and refresh steps
                    existing.steps = steps
                    existing.trigger_keywords = trigger_keywords
                    existing.usage_count += 1
                    existing.success_count += 1
                    logger.info(f"🔄 Updated existing skill: {skill_id}")
                    await db.commit()
                    return existing
                else:
                    new_skill = Skill(
                        id=skill_id,
                        name=name,
                        description=description,
                        trigger_keywords=trigger_keywords,
                        steps=steps,
                        usage_count=1,
                        success_count=1
                    )
                    db.add(new_skill)
                    logger.info(f"✨ Created new auto-generated skill: {skill_id} ({name})")
                    await db.commit()
                    return new_skill

        except Exception as e:
            logger.error(f"❌ Failed to extract auto-generated skill: {e}")
            return None


# =========================================================================
# USER PROFILE SERVICE (Self-refining User Preferences)
# =========================================================================

class UserProfileService:
    @staticmethod
    async def get_preferences() -> Dict[str, Any]:
        """Fetch user preferences, initializing with defaults if missing."""
        async with AsyncSessionLocal() as db:
            stmt = select(UserProfile).where(UserProfile.id == "default")
            result = await db.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if not profile:
                default_prefs = {
                    "verbosity": "detailed",
                    "auto_approve": ["network", "monitoring"],
                    "preferred_agents": {
                        "database": "real-desktop-commander",
                        "network": "monitoring"
                    },
                    "rules": []
                }
                profile = UserProfile(id="default", preferences=default_prefs)
                db.add(profile)
                await db.commit()
                return default_prefs
                
            return profile.preferences

    @staticmethod
    async def refine_profile_from_interaction(
        user_message: str,
        agent_response: str
    ) -> Dict[str, Any]:
        """Analyze user feedback / messages to extract and update user preferences."""
        current_prefs = await UserProfileService.get_preferences()
        
        # Check if the message contains feedback or preferences
        feedback_keywords = [
            "prefer", "always", "never", "should", "don't", "dont", 
            "make sure to", "stop", "use", "verbos", "concise", "brief", 
            "short", "long", "detail", "only", "reply", "response", "style"
        ]
        if not any(kw in user_message.lower() for kw in feedback_keywords):
            return current_prefs

        logger.info("👤 Refining user preferences model based on interaction...")
        llm = get_service_registry().get_llm()
        
        prompt = f"""You are the User Modeling Agent. 
Analyze this user interaction to detect if they expressed any preferences, rules, or constraints for how the AI agents should operate.

Current User Preferences: {json.dumps(current_prefs, indent=2)}
User Message: {user_message}
Agent Response: {agent_response}

Your task is to return the updated User Preferences JSON object.
Modify/add preferences such as:
- "verbosity": "detailed" or "concise"
- "auto_approve": list of categories allowed for auto-execution
- "preferred_agents": map of category to agent_name
- "rules": list of custom strings outlining what the user wants/dislikes.

Respond with valid JSON only. Do not add explanations or code blocks.
"""
        try:
            llm_response = await llm.generate(prompt)
            clean_json = re.sub(r"```[a-zA-Z]*", "", llm_response).strip()
            updated_prefs = json.loads(clean_json)
            
            if isinstance(updated_prefs, dict):
                async with AsyncSessionLocal() as db:
                    await db.execute(
                        update(UserProfile)
                        .where(UserProfile.id == "default")
                        .values(preferences=updated_prefs, updated_at=datetime.now(timezone.utc))
                    )
                    await db.commit()
                logger.info("👤 User preferences model refined and persisted.")
                return updated_prefs
        except Exception as e:
            logger.warning(f"Failed to refine user profile: {e}")
            
        return current_prefs


# =========================================================================
# SCHEDULER SERVICE (Natural Language Task Scheduler)
# =========================================================================

class SchedulerService:
    @staticmethod
    async def parse_and_schedule(natural_language: str) -> Optional[ScheduledTask]:
        """Use LLM to translate natural language request into a cron schedule and task payload."""
        logger.info(f"⏰ Parsing scheduling request: '{natural_language}'")
        llm = get_service_registry().get_llm()
        
        prompt = f"""Translate this natural language task schedule request into a cron expression and a task query.
Request: "{natural_language}"

Your response must be a JSON object conforming exactly to this structure:
{{
  "description": "Short description of the scheduled task",
  "cron_expression": "standard 5-field cron expression, e.g. '*/5 * * * *'",
  "task_payload": "Maestro orchestrator task command, e.g. 'Verify system disk usage on edgeserver'"
}}

Rules for Cron Translation:
- "every 5 minutes" -> "*/5 * * * *"
- "every day at midnight" -> "0 0 * * *"
- "every Monday at 8 AM" -> "0 8 * * 1"
- "every hour" -> "0 * * * *"

Write only raw JSON, no markdown backticks, no explanations.
"""
        try:
            llm_response = await llm.generate(prompt)
            clean_json = re.sub(r"```[a-zA-Z]*", "", llm_response).strip()
            parsed = json.loads(clean_json)
            
            cron_expr = parsed.get("cron_expression", "0 * * * *")
            payload = parsed.get("task_payload", natural_language)
            desc = parsed.get("description", f"Scheduled: {natural_language}")
            
            # Basic validation of cron expression (must have 5 fields)
            if len(cron_expr.split()) < 5:
                cron_expr = "0 * * * *" # Fallback hourly
                
            task_id = f"sched_{int(datetime.now().timestamp())}"
            next_run = calculate_next_run(cron_expr, datetime.now(timezone.utc))
            
            async with AsyncSessionLocal() as db:
                new_task = ScheduledTask(
                    id=task_id,
                    description=desc,
                    cron_expression=cron_expr,
                    task_payload=payload,
                    is_active=True,
                    next_run_at=next_run
                )
                db.add(new_task)
                await db.commit()
                logger.info(f"⏰ Scheduled task '{desc}' created. Next run at: {next_run.isoformat()}")
                return new_task
                
        except Exception as e:
            logger.error(f"❌ Failed to parse and schedule task: {e}")
            return None

    @staticmethod
    async def get_active_tasks() -> List[ScheduledTask]:
        """Fetch all currently active scheduled tasks."""
        async with AsyncSessionLocal() as db:
            stmt = select(ScheduledTask).where(ScheduledTask.is_active == True)
            result = await db.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def trigger_task(task_id: str) -> None:
        """Trigger execution of a scheduled task and update run times."""
        async with AsyncSessionLocal() as db:
            stmt = select(ScheduledTask).where(ScheduledTask.id == task_id)
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()
            
            if not task:
                return
                
            logger.info(f"⏰ Scheduler: Triggering task '{task.description}' ({task.id})...")
            
            # Execute in background via Maestro Orchestrator
            from twisterlab.agents.registry import get_agent_registry
            registry = get_agent_registry()
            maestro = registry.get_agent("maestro")
            
            if maestro:
                # Run orchestrate task asynchronously
                import asyncio
                asyncio.create_task(maestro.execute("orchestrate", task=task.task_payload))
            else:
                logger.error("❌ Scheduler error: Maestro agent not found in registry!")
                
            # Update cron state
            now = datetime.now(timezone.utc)
            task.last_run_at = now
            task.next_run_at = calculate_next_run(task.cron_expression, now)
            await db.commit()
            logger.info(f"⏰ Task '{task.description}' updated. Next run set to: {task.next_run_at.isoformat()}")


async def scheduler_runner_loop() -> None:
    """Background task running the scheduler checking every 60 seconds."""
    logger.info("⏰ Scheduler background runner loop started.")
    import asyncio
    while True:
        try:
            now = datetime.now(timezone.utc)
            # Fetch active tasks
            tasks = await SchedulerService.get_active_tasks()
            for task in tasks:
                if task.next_run_at and task.next_run_at <= now:
                    await SchedulerService.trigger_task(task.id)
        except Exception as e:
            logger.error(f"Error in scheduler runner loop: {e}", exc_info=True)
        # Sleep for 60 seconds
        await asyncio.sleep(60)

_scheduler_task: Optional[asyncio.Task] = None

def start_scheduler() -> None:
    """Start the scheduler background task."""
    global _scheduler_task
    import asyncio
    if _scheduler_task is None:
        _scheduler_task = asyncio.create_task(scheduler_runner_loop())
        logger.info("⏰ Background scheduler started.")

