import asyncio
import os
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

async def find_intelligence_pages():
    agent = RealNotionAgent()
    print(f"Searching for 'Intelligence'...")
    # broad search
    res = await agent._notion_request("POST", "/search", {
        "query": "Intelligence",
        "filter": {"value": "page", "property": "object"}
    })
    
    results = res.get("results", [])
    if results:
        for p in results:
            title = agent._extract_title(p)
            print(f"PAGE: {title} (ID: {p['id']}) - Archived: {p.get('archived')}")
    else:
        print("No pages found.")

if __name__ == "__main__":
    asyncio.run(find_intelligence_pages())
