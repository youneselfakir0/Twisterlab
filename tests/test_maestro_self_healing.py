import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent, TaskCategory, TaskPriority
from twisterlab.agents.core.base import AgentResponse

@pytest.mark.asyncio
async def test_maestro_self_healing_database_retry():
    """Verify that Maestro catches database errors and attempts self-healing with a retry."""
    maestro = RealMaestroAgent()
    maestro._use_llm = False
    
    mock_db_health_adapter = AsyncMock()
    mock_db_health_adapter.agent_name = "DatabaseAgent"
    mock_db_health_adapter.call.return_value = AgentResponse(success=True, data={"status": "reconnected"})
    
    mock_archive_adapter = AsyncMock()
    mock_archive_adapter.agent_name = "ArchiveAgent"
    mock_archive_adapter.call.return_value = AgentResponse(success=True)

    mock_failed_adapter = AsyncMock()
    mock_failed_adapter.agent_name = "QueryAgent"
    mock_failed_adapter.call.side_effect = [
        AgentResponse(success=False, error="psycopg2.OperationalError: connection pool exhausted"),
        AgentResponse(success=True, data={"rows": [1, 2, 3]})
    ]
    
    def mock_lookup(req_name, *args, **kwargs):
        if req_name == "db_health":
            return mock_db_health_adapter
        elif req_name == "archive_mission":
            return mock_archive_adapter
        return mock_failed_adapter

    maestro._resolve_requirement_to_adapter = MagicMock(side_effect=mock_lookup)
    
    plan = {
        "steps": [
            {"order": 1, "requirement": "execute_query", "params": {"sql": "SELECT 1"}, "purpose": "Test DB"}
        ]
    }
    
    execution_log = await maestro._execute_plan(plan, "test task", {}, lookup_fn=mock_lookup)
    
    assert execution_log[0]["status"] == "success"
    assert execution_log[0]["data"] == {"rows": [1, 2, 3]}
    assert maestro._healing_history["execute_query"]["success"] == 1
    print("[OK] test_maestro_self_healing_database_retry passed perfectly!")

@pytest.mark.asyncio
async def test_maestro_self_healing_redis_retry():
    """Verify that Maestro catches cache errors and attempts purging transient locks."""
    maestro = RealMaestroAgent()
    maestro._use_llm = False
    
    mock_cache_del_adapter = AsyncMock()
    mock_cache_del_adapter.agent_name = "CacheAgent"
    mock_cache_del_adapter.call.return_value = AgentResponse(success=True, data={"purged": 1})
    
    mock_archive_adapter = AsyncMock()
    mock_archive_adapter.agent_name = "ArchiveAgent"
    mock_archive_adapter.call.return_value = AgentResponse(success=True)

    def mock_lookup(req_name, *args, **kwargs):
        if req_name == "cache_delete":
            return mock_cache_del_adapter
        if req_name == "archive_mission":
            return mock_archive_adapter
        return None

    maestro._resolve_requirement_to_adapter = MagicMock(side_effect=mock_lookup)
    
    heal_action = await maestro._attempt_self_healing(
        requirement="get_state",
        error_msg="Redis connectionerror: connection closed by peer",
        processed_params={},
        lookup_fn=mock_lookup
    )
    
    assert heal_action == "retry"
    mock_cache_del_adapter.call.assert_any_call("cache_delete", key="lock:maestro:*")
    print("[OK] test_maestro_self_healing_redis_retry passed perfectly!")

@pytest.mark.asyncio
async def test_maestro_circuit_breaker():
    """Verify that Maestro quarantines a capability after 5 consecutive failures."""
    maestro = RealMaestroAgent()
    maestro._use_llm = False
    
    mock_failed_adapter = AsyncMock()
    mock_failed_adapter.agent_name = "FailingAgent"
    mock_failed_adapter.call.return_value = AgentResponse(success=False, error="Some persistent failure")

    mock_archive_adapter = AsyncMock()
    mock_archive_adapter.agent_name = "ArchiveAgent"
    mock_archive_adapter.call.return_value = AgentResponse(success=True)

    def mock_lookup(req_name, *args, **kwargs):
        if req_name == "archive_mission":
            return mock_archive_adapter
        return mock_failed_adapter

    maestro._resolve_requirement_to_adapter = MagicMock(side_effect=mock_lookup)
    
    plan = {
        "steps": [
            {"order": 1, "requirement": "unstable_tool", "params": {}, "purpose": "Check breaker"}
        ]
    }
    
    # Run 5 failures to trigger the circuit breaker
    for i in range(5):
        await maestro._execute_plan(plan, "test breaker", {}, lookup_fn=mock_lookup)
        
    assert maestro._failure_counts["unstable_tool"] == 5
    assert "unstable_tool" in maestro._quarantined_until
    
    # The 6th execution should fail immediately via the Circuit Breaker
    execution_log = await maestro._execute_plan(plan, "test breaker", {}, lookup_fn=mock_lookup)
    
    assert execution_log[0]["status"] == "error"
    assert "is quarantined due to repeated failures" in execution_log[0]["error"]
    print("[OK] test_maestro_circuit_breaker passed perfectly!")

@pytest.mark.asyncio
async def test_maestro_adaptive_retry():
    """Verify that Maestro dynamically reduces retry limits if healing history has low success rate."""
    maestro = RealMaestroAgent()
    maestro._use_llm = False
    
    # Inject a history of 5 failures and 0 successes for 'unstable_tool'
    maestro._healing_history["unstable_tool"] = {"success": 0, "fail": 5}
    
    # This should reduce max retries from 2 to 1
    max_retries = maestro._get_max_retries("unstable_tool")
    assert max_retries == 1
    
    # With a high success rate, it should stay 2
    maestro._healing_history["good_tool"] = {"success": 5, "fail": 0}
    max_retries_good = maestro._get_max_retries("good_tool")
    assert max_retries_good == 2
    print("[OK] test_maestro_adaptive_retry passed perfectly!")

@pytest.mark.asyncio
async def test_maestro_healing_audit_trail():
    """Verify that Maestro automatically archives healing events to the ArchiveAgent."""
    maestro = RealMaestroAgent()
    maestro._use_llm = False
    
    mock_archive_adapter = AsyncMock()
    mock_archive_adapter.agent_name = "ArchiveAgent"
    mock_archive_adapter.call.return_value = AgentResponse(success=True)
    
    def mock_lookup(req_name, *args, **kwargs):
        if req_name == "archive_mission":
            return mock_archive_adapter
        return None
        
    maestro._resolve_requirement_to_adapter = MagicMock(side_effect=mock_lookup)
    
    await maestro._archive_healing_event(
        requirement="execute_query",
        category="sql",
        error_msg="OperationalError",
        success=True,
        lookup_fn=mock_lookup
    )
    
    # Verify the archive_mission capability was called with the audit trail data
    mock_archive_adapter.call.assert_called_once()
    call_args = mock_archive_adapter.call.call_args[1]
    assert call_args["data"]["requirement"] == "execute_query"
    assert call_args["data"]["category"] == "sql"
    assert call_args["data"]["success"] is True
    print("[OK] test_maestro_healing_audit_trail passed perfectly!")

if __name__ == "__main__":
    asyncio.run(test_maestro_self_healing_database_retry())
    asyncio.run(test_maestro_self_healing_redis_retry())
    asyncio.run(test_maestro_circuit_breaker())
    asyncio.run(test_maestro_adaptive_retry())
    asyncio.run(test_maestro_healing_audit_trail())
