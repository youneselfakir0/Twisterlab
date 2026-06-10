import pytest
import asyncio
import logging
from twisterlab.api.services.orchestration_service import get_orchestration_service
from twisterlab.api.schemas.common import AgentErrorCode

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IntelligenceRegression")

@pytest.mark.asyncio
async def test_intelligence_mission_chain_regression():
    """
    Regression Test: Ensures that the complex 'Intelligence' chain works with 
    capability-driven discovery and produces full execution logs.
    """
    orch_service = get_orchestration_service()
    
    # Task that triggers the Intelligence category
    task = "Effectuer une veille technologique sur l'IA agentique et archiver le rapport."
    
    logger.info(f"Triggering Intelligence mission for: {task}")
    
    # Use dry_run=False to test the execution resolver (even if agents are mocked or fail)
    # We want to see the execution TRACE.
    res = await orch_service.orchestrate_mission(
        task=task,
        context={"dry_run": False}
    )
    
    # 1. Check Result Structure
    assert res.success is True, f"Mission orchestration failed: {res.error}"
    assert "results" in res.data, "Execution log (results) missing from response."
    
    exec_log = res.data["results"]
    logger.info(f"Execution Log contains {len(exec_log)} steps.")
    
    # 2. Check Observability Contract (Requirement + Agent)
    for step in exec_log:
        step_num = step.get("step")
        if step.get("status") == "skipped":
            continue
            
        assert "requirement" in step, f"Step {step_num} missing 'requirement' key."
        assert "agent" in step, f"Step {step_num} missing 'agent' key (Resolution trace failed)."
        
        logger.info(f"Step {step_num}: Requirement '{step['requirement']}' resolved to Agent '{step['agent']}'")

    # 3. Verify Planning Decoupling (Logic check)
    # The 'steps' in OrchestratedTask should NOT have changed the original requirements
    # but the execution log should reflect the resolution.
    
    requirements_used = res.data.get("requirements_used", [])
    assert "browse" in requirements_used
    assert "summarize" in requirements_used
    assert "archive_result" in requirements_used
    
    # 4. Check Synthesis
    synthesis = res.data.get("synthesis", {})
    assert "summary" in synthesis
    assert synthesis.get("success_rate", 0) > 0 # At least some steps should work in the mock/dev env

if __name__ == "__main__":
    asyncio.run(test_intelligence_mission_chain_regression())
