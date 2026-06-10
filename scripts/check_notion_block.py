import asyncio
import os
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

async def check_archived_block():
    agent = RealNotionAgent()
    block_id = "3431f21b3b068087845cd838474d5464"
    print(f"Checking block {block_id}...")
    try:
        res = await agent._notion_request("GET", f"/blocks/{block_id}", None)
        print(f"BLOCK: {res.get('type')} - Archived: {res.get('archived')}")
        parent = res.get("parent", {})
        print(f"PARENT: {parent}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_archived_block())
