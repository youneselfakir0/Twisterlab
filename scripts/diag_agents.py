
import sys
import os
# Ensure src is in python path
sys.path.append(os.path.join(os.getcwd(), "src"))

from twisterlab.agents.mcp.server import UnifiedMCPServer

async def diag():
    try:
        server = UnifiedMCPServer()
        print(f"Server initialized: {server.name}")
        agents = server._agent_registry.list_agents()
        print(f"Registered agents ({len(agents)}): {agents}")
        tools = server._tool_router.list_tools()
        print(f"Total tools: {len(tools)}")
        
        archive_agent = server._agent_registry.get_agent("archive")
        if archive_agent:
            print("Archive agent found in registry.")
            caps = archive_agent.list_capabilities()
            print(f"Archive capabilities: {[c.name for c in caps]}")
        else:
            print("Archive agent NOT found in registry.")
            
        archive_tools = [t['name'] for t in tools if 'archive' in t['name']]
        print(f"Archive tools found in router ({len(archive_tools)}): {archive_tools}")
    except Exception as e:
        print(f"Diag failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(diag())
