import asyncio
import os
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

async def search_active_pages():
    agent = RealNotionAgent()
    print(f"Searching for ANY active page...")
    # broad search
    res = await agent._notion_request("POST", "/search", {
        "query": "",
        "filter": {"value": "page", "property": "object"},
        "sort": {"direction": "descending", "timestamp": "last_edited_time"}
    })
    
    results = res.get("results", [])
    if results:
        for p in results:
            title = agent._extract_title(p)
            archived = p.get("archived", False)
            print(f"PAGE: {title} (ID: {p['id']}) - Archived: {archived}")
    else:
        print("No pages found.")

if __name__ == "__main__":
    asyncio.run(search_active_pages())
