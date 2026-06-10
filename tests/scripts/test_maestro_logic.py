
import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from twisterlab.agents.core.maestro_agent import MaestroAgent

async def test_maestro():
    logging.basicConfig(level=logging.INFO)
    
    # Mock registry
    class MockRegistry:
        def get_llm(self):
            class MockLLM:
                async def chat(self, messages, model):
                    class MockResponse:
                        def __init__(self):
                            self.content = "Analysis result: The system appears secure but ensure that DesktopCommander remains in safe mode and DNS is optimized."
                            self.total_tokens = 42
                    return MockResponse()
            return MockLLM()

    registry = MockRegistry()
    
    # Initialize MaestroAgent with mock registry
    # In base.py: def __init__(self, registry: Optional[ServiceRegistry] = None):
    maestro = MaestroAgent(registry=registry)

    print("--- Testing Orchestration ---")
    response_orch = await maestro.handle_orchestrate("Check the status of my infrastructure")
    print(f"Command: {response_orch.data['command']}")
    print(f"Action: {response_orch.data['action']}")
    print(f"Message: {response_orch.data['message']}")

    print("\n--- Testing Security Analysis ---")
    response_analyze = await maestro.handle_analyze(
        content="IP: 192.168.0.20, DNS: 8.8.8.8, Port 53: Timeout",
        analysis_type="security"
    )
    print(f"Type: {response_analyze.data['analysis_type']}")
    print(f"Analysis: {response_analyze.data['analysis']}")

if __name__ == "__main__":
    asyncio.run(test_maestro())
