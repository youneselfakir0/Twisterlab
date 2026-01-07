import os


def create_agent_scaffold(agent_name, llm_backend):
    # Define the scaffold directory
    scaffold_dir = os.path.join("scaffold", agent_name)

    # Create the scaffold directory
    os.makedirs(scaffold_dir, exist_ok=True)

    # Create agent.py
    agent_content = f"""from twisterlab.agents.core.base import TwisterAgent, AgentCapability, AgentResponse

class {agent_name}(TwisterAgent):
    @property
    def name(self) -> str:
        return "{agent_name.lower()}"
    
    @property
    def description(self) -> str:
        return "{agent_name} agent"
    
    def get_capabilities(self) -> list[AgentCapability]:
        return []
    
    async def run(self, task: str, context: dict = None) -> AgentResponse:
        return AgentResponse(success=True, data={{"message": "Hello from {agent_name}"}})
"""
    with open(os.path.join(scaffold_dir, "agent.py"), "w") as f:
        f.write(agent_content)

    # Create test_agent.py
    test_content = f"""import pytest
from .agent import {agent_name}

@pytest.mark.asyncio
@pytest.mark.unit
async def test_{agent_name.lower()}_initialization():
    agent = {agent_name}()
    assert agent is not None
    assert agent.name == "{agent_name.lower()}"
"""
    with open(os.path.join(scaffold_dir, "test_agent.py"), "w") as f:
        f.write(test_content)

    print(f"Scaffold for {agent_name} created successfully at {scaffold_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a new agent scaffold.")
    parser.add_argument("--name", required=True, help="Name of the agent")
    parser.add_argument("--llm", default="llama-3.2", help="LLM backend to use")

    args = parser.parse_args()
    create_agent_scaffold(args.name, args.llm)
