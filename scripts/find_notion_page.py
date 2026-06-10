import asyncio
import os
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

async def find_trading_page():
    agent = RealNotionAgent()
    print(f"Searching for 'Trading Intelligence'...")
    res = await agent.handle_search(query="Trading Intelligence")
    if res.success:
        results = res.data.get("results", [])
        if results:
            for p in results:
                print(f"FOUND: {p['title']} (ID: {p['id']}) - URL: {p['url']}")
        else:
            print("No page found with that name.")
    else:
        print(f"Search failed: {res.error}")

if __name__ == "__main__":
    asyncio.run(find_trading_page())
