import asyncio
import os
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

async def search_databases():
    agent = RealNotionAgent()
    print(f"Searching for ANY database...")
    res = await agent._notion_request("POST", "/search", {
        "query": "",
        "filter": {"value": "database", "property": "object"}
    })
    
    results = res.get("results", [])
    if results:
        for p in results:
            title = agent._extract_title(p)
            print(f"DATABASE: {title} (ID: {p['id']})")
    else:
        print("No databases found.")

if __name__ == "__main__":
    asyncio.run(search_databases())
