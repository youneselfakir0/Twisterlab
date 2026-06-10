"""
Contract Tests for Phase 1: AgentAdapter
Validates that our adapter can successfully normalize:
1. Object-style responses (success/data/error)
2. Dictionary-style responses (status/data)
3. Raw results
4. Exceptions
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path
sys.path.append(str(Path(__file__).parents[3]))

from twisterlab.agents.base.adapter import AgentAdapter
from twisterlab.api.schemas.common import UnifiedAgentResponse

class MockAgentObject:
    """Simulates a modern agent returning an object."""
    def __init__(self):
        self.name = "mock-obj"
    async def execute(self, tool_name, **kwargs):
        from dataclasses import dataclass
        @dataclass
        class Res:
            success: bool
            data: Any = None
            error: str = None
        return Res(success=True, data={"result": "obj_success"})

class MockAgentDict:
    """Simulates a legacy agent returning a dictionary."""
    def __init__(self):
        self.name = "mock-dict"
    async def handle_tool(self, **kwargs):
        return {"status": "success", "data": "dict_success", "metadata": {"source": "legacy"}}

class MockAgentFail:
    """Simulates an agent that throws an exception."""
    def __init__(self):
        self.name = "mock-fail"
    async def handle_tool(self, **kwargs):
        raise ValueError("Simulated Agent Crash")

async def test_normalization():
    print("--- Starting Phase 1 Contract Tests ---")
    
    # 1. Test Object Normalization
    obj_agent = AgentAdapter(MockAgentObject())
    res1 = await obj_agent.call("any_tool")
    print(f"Test 1 (Object) Result: {res1}")
    print(f"Test 1 (Object) success type: {type(res1.success)} value: {res1.success}")
    assert res1.success is True
    assert res1.data["result"] == "obj_success"

    # 2. Test Dict Normalization
    dict_agent = AgentAdapter(MockAgentDict())
    # This will trigger Style D (handle_tool fallback)
    res2 = await dict_agent.call("tool")
    print(f"Test 2 (Dict): Success={res2.success}, Data={res2.data}")
    assert res2.success is True
    assert res2.data == "dict_success"
    assert res2.metadata["source"] == "legacy"

    # 3. Test Failure Normalization
    fail_agent = AgentAdapter(MockAgentFail())
    res3 = await fail_agent.call("tool")
    print(f"Test 3 (Failure): Success={res3.success}, Error={res3.error}")
    assert res3.success is False
    assert "Simulated Agent Crash" in res3.error
    assert res3.error_code == "AGENT_FAILURE"

    print("\n[OK] All Phase 1 Contract Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_normalization())
