
import asyncio
import sys
import os
import json

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent

async def run_metrics():
    agent = RealMonitoringAgent()
    print(f"--- Running {agent.name} Agent ---")
    response = await agent.handle_collect_metrics()
    
    if response.success:
        print(json.dumps(response.data, indent=2))
    else:
        print(f"Error: {response.error}")

if __name__ == "__main__":
    asyncio.run(run_metrics())
