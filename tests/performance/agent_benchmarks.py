import asyncio
import time
import logging
from twisterlab.agents.mcp.router import get_tool_router
from twisterlab.agents.core.base import TwisterAgent, AgentCapability, AgentResponse, CapabilityType
from twisterlab.services import ServiceRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "mock"

    @property
    def description(self) -> str:
        return "Mock Agent for testing"

    def get_capabilities(self):
        return [
            AgentCapability(
                name="noop",
                description="Does nothing",
                handler="handle_noop",
                capability_type=CapabilityType.QUERY
            )
        ]

    async def handle_noop(self, **kwargs) -> AgentResponse:
        return AgentResponse(success=True, data="done")

async def run_benchmark():
    print("Starting Router Performance Benchmark...")
    from twisterlab.agents.mcp.router import get_agent_registry
    registry = get_agent_registry()
    registry.register(MockAgent)
    
    router = get_tool_router()
    
    # Pre-warm (cache building)
    print("Pre-warming router...")
    tools = router.list_tools()
    print(f"Router discovered {len(tools)} tools.")
    
    # Latency test
    n = 1000
    print(f"Running {n} tool discovery calls (cached)...")
    start = time.time()
    for _ in range(n):
        router.list_tools()
    duration = time.time() - start
    print(f"Average Discovery Latency: {(duration/n)*1000:.4f}ms")

    # Execution test (simulated)
    stats = router.get_stats()
    print(f"Router Stats: {stats}")

if __name__ == "__main__":
    try:
        asyncio.run(run_benchmark())
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
