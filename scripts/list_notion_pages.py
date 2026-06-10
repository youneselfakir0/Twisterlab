import asyncio
import os
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

async def list_all_pages():
    agent = RealNotionAgent()
    print(f"Listing all accessible Notion pages...")
    res = await agent.handle_search(query="", limit=50)
    if res.success:
        results = res.data.get("results", [])
        if results:
            for p in results:
                print(f"PAGE: {p['title']} (ID: {p['id']})")
        else:
            print("No pages found.")
    else:
        print(f"Search failed: {res.error}")

if __name__ == "__main__":
    asyncio.run(list_all_pages())
