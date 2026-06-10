import asyncio
import logging
import uuid
from typing import Any, Dict
from twisterlab.api.services.agent_service import get_agent_service
from twisterlab.api.services.classification_service import get_classification_service
from twisterlab.api.services.resolution_service import get_resolution_service
from twisterlab.api.services.monitoring_service import get_monitoring_service
from twisterlab.api.services.orchestration_service import get_orchestration_service
from twisterlab.api.schemas.common import AgentErrorCode

# Configure verification logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phase2RefinementVerification")

async def verify_refinement():
    logger.info("### STARTING PHASE 2 REFINEMENT VERIFICATION ###")
    
    # 1. Verify Discovery Method
    logger.info("--- Step 1: Registry Discovery Check ---")
    agent_service = get_agent_service()
    registry = agent_service.registry
    
    archive_key = registry.find_agent_by_capability("archive_result")
    browser_key = registry.find_agent_by_capability("browse")
    
    if archive_key == "archive" and browser_key == "browser":
        logger.info(f"✅ Registry Discovery: SUCCESS (Found {archive_key} for archive_result)")
    else:
        logger.error(f"❌ Registry Discovery: FAILED (Found {archive_key}, {browser_key})")

    # 2. Verify Maestro Decoupling (Planning)
    logger.info("--- Step 2: Maestro Planning Decoupling ---")
    orch_service = get_orchestration_service()
    res = await orch_service.orchestrate_mission(
        task="Check system health and archive results",
        context={"dry_run": True}
    )
    
    if res.success and "plan" in res.data:
        plan = res.data["plan"]
        steps = plan.get("steps", [])
        has_requirements = all("requirement" in s for s in steps)
        has_no_agent_hardcoding = all("agent" not in s for s in steps)
        
        if has_requirements and has_no_agent_hardcoding:
            logger.info("✅ Maestro Planning: DECOUPLED (Uses 'requirement' instead of 'agent')")
        else:
            logger.error("❌ Maestro Planning: STILL COUPLED")
            logger.debug(f"Plan structure: {steps}")
    else:
        logger.error(f"❌ Maestro Planning: FAILED ({res.error})")

    # 3. Verify Execution Resolver (Simulated)
    logger.info("--- Step 3: Capability Execution Loop ---")
    # We'll use a simple orchestration to see if it resolves 'analyze_sentiment' correctly
    res = await orch_service.orchestrate_mission(
        task="Test capability resolution",
        context={"dry_run": False} 
    )
    # Even if it fails downstream (e.g. LLM 404), we want to see the execution log for resolution
    if res.success and "results" in res.data:
        exec_log = res.data["results"]
        resolved_all = all("agent" in s for s in exec_log if s["status"] != "skipped")
        if resolved_all:
            logger.info("✅ Execution Loop: RESOLVER ACTIVE (Requirements resolved to Agents)")
        else:
            logger.error("❌ Execution Loop: RESOLVER FAILED")
    else:
         logger.warning(f"⚠️ Execution Loop: Partial success or mission failed ({res.error})")

    logger.info("### REFINEMENT VERIFICATION COMPLETE ###")

if __name__ == "__main__":
    asyncio.run(verify_refinement())
