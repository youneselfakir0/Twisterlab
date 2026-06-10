import asyncio
import os
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

async def test_notion():
    agent = RealNotionAgent()
    print(f"Testing Notion connection...")
    res = await agent.handle_create_page(
        title="[DEBUG] Connection Test",
        content="Testing connection from TwisterLab API pod."
    )
    if res.success:
        print(f"SUCCESS: Page created! URL: {res.data.get('url')}")
    else:
        print(f"FAILED: {res.error}")

if __name__ == "__main__":
    asyncio.run(test_notion())
