import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent, TaskCategory, TaskPriority
from twisterlab.agents.core.base import AgentResponse

@pytest.mark.asyncio
async def test_maestro_self_healing_database_retry():
    """Verify that Maestro catches database errors and attempts self-healing with a retry."""
    # 1. Initialize Maestro
    maestro = RealMaestroAgent()
    maestro._use_llm = False  # Use rule-based analysis
    
    # 2. Setup mock adapters
    mock_db_health_adapter = AsyncMock()
    mock_db_health_adapter.agent_name = "DatabaseAgent"
    # db_health mock returns success
    mock_db_health_adapter.call.return_value = AgentResponse(success=True, data={"status": "reconnected"})
    
    mock_failed_adapter = AsyncMock()
    mock_failed_adapter.agent_name = "QueryAgent"
    # First call fails with DB OperationalError, second call succeeds
    mock_failed_adapter.call.side_effect = [
        AgentResponse(success=False, error="psycopg2.OperationalError: connection pool exhausted"),
        AgentResponse(success=True, data={"rows": [1, 2, 3]})
    ]
    
    def mock_lookup(req_name, *args, **kwargs):
        if req_name == "db_health":
            return mock_db_health_adapter
        return mock_failed_adapter

    # 3. Inject mock behavior for registry lookup
    maestro._resolve_requirement_to_adapter = MagicMock(side_effect=mock_lookup)
    
    # 4. Invoke self-healing check
    heal_action = await maestro._attempt_self_healing(
        requirement="execute_query",
        error_msg="psycopg2.OperationalError: connection pool exhausted",
        processed_params={},
        lookup_fn=mock_lookup
    )
    
    # Assertions
    assert heal_action == "retry"
    mock_db_health_adapter.call.assert_called_with("db_health")
    
    # 5. Run full _execute_plan simulation
    plan = {
        "steps": [
            {"order": 1, "requirement": "execute_query", "params": {"sql": "SELECT 1"}, "purpose": "Test DB"}
        ]
    }
    
    execution_log = await maestro._execute_plan(plan, "test task", {}, lookup_fn=mock_lookup)
    
    # The step should succeed on retry!
    assert execution_log[0]["status"] == "success"
    assert execution_log[0]["data"] == {"rows": [1, 2, 3]}
    print("\n[OK] test_maestro_self_healing_database_retry passed perfectly!")

@pytest.mark.asyncio
async def test_maestro_self_healing_redis_retry():
    """Verify that Maestro catches cache errors and attempts purging transient locks."""
    maestro = RealMaestroAgent()
    maestro._use_llm = False
    
    mock_cache_del_adapter = AsyncMock()
    mock_cache_del_adapter.agent_name = "CacheAgent"
    mock_cache_del_adapter.call.return_value = AgentResponse(success=True, data={"purged": 1})
    
    def mock_lookup(req_name, *args, **kwargs):
        if req_name == "cache_delete":
            return mock_cache_del_adapter
        return None

    maestro._resolve_requirement_to_adapter = MagicMock(side_effect=mock_lookup)
    
    heal_action = await maestro._attempt_self_healing(
        requirement="get_state",
        error_msg="Redis connectionerror: connection closed by peer",
        processed_params={},
        lookup_fn=mock_lookup
    )
    
    assert heal_action == "retry"
    # Ensure it purged the locks
    mock_cache_del_adapter.call.assert_any_call("cache_delete", key="lock:maestro:*")
    print("[OK] test_maestro_self_healing_redis_retry passed perfectly!")

if __name__ == "__main__":
    asyncio.run(test_maestro_self_healing_database_retry())
    asyncio.run(test_maestro_self_healing_redis_retry())
