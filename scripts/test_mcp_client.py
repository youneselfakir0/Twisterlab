import asyncio
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
import json

async def run():
    print("Initiating connection...")
    server_params = {
        "command": "ssh",
        "args": [
            "twister@192.168.0.30",
            "PYTHONPATH=/home/twister/twisterlab-mcp/src",
            "python3",
            "-m",
            "twisterlab.agents.mcp.server"
        ]
    }
    
    async with stdio_client(server_params["command"], server_params["args"]) as (read, write):
        async with ClientSession(read, write) as session:
            print("Connected! Initializing session...")
            await session.initialize()
            print("Session initialized! Fetching tools...")
            
            result = await session.list_tools()
            print(f"\nFound {len(result.tools)} tools:")
            for tool in result.tools:
                print(f" - {tool.name}")

if __name__ == "__main__":
    asyncio.run(run())
