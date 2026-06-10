import asyncio
import httpx
import json

async def main():
    base_url = "http://192.168.0.30:30000"
    print(f"Connecting to SSE endpoint at {base_url}/api/v1/mcp/sse...")
    
    client = httpx.AsyncClient(timeout=60.0)
    
    # Open the SSE connection
    async with client.stream("GET", f"{base_url}/api/v1/mcp/sse") as response:
        if response.status_code != 200:
            print(f"Failed to connect to SSE: {response.status_code}")
            return
            
        print("Connected to SSE! Waiting for the 'endpoint' event containing session_id...")
        
        # Get the async line iterator
        lines_iterator = response.aiter_lines()
        
        # Read lines to get session_id
        session_id = None
        async for line in lines_iterator:
            print(f"SSE Raw Line: {line}")
            if line.startswith("data:"):
                url_data = line[5:].strip()
                if "session_id=" in url_data:
                    session_id = url_data.split("session_id=")[1]
                    print(f"[OK] Found Session ID: {session_id}")
                    break
        
        if not session_id:
            print("Could not retrieve session_id from SSE stream.")
            return
            
        # Initialize JSON-RPC call
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {
                    "name": "handshake-tester",
                    "version": "1.0.0"
                }
            }
        }
        
        # Send initialize POST
        messages_url = f"{base_url}/api/v1/mcp/messages?session_id={session_id}"
        print(f"Sending 'initialize' request to: {messages_url}")
        post_response = await client.post(messages_url, json=init_message)
        print(f"Initialize POST response status: {post_response.status_code}")
        
        # Listen on SSE for the initialize response
        async for line in lines_iterator:
            print(f"SSE Raw Line: {line}")
            if line.startswith("data:"):
                data_content = line[5:].strip()
                try:
                    payload = json.loads(data_content)
                    if payload.get("id") == 1:
                        print(f"[OK] Received Initialize Response: {json.dumps(payload, indent=2)}")
                        break
                except json.JSONDecodeError:
                    pass
                    
        # Send initialized notification
        init_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        print("Sending 'notifications/initialized' notification...")
        post_response = await client.post(messages_url, json=init_notification)
        print(f"Notification POST status: {post_response.status_code}")
        
        # Request tools list
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        print("Requesting tools list...")
        post_response = await client.post(messages_url, json=tools_request)
        print(f"Tools List POST status: {post_response.status_code}")
        
        # Listen for tools list response
        async for line in lines_iterator:
            print(f"SSE Raw Line: {line}")
            if line.startswith("data:"):
                data_content = line[5:].strip()
                try:
                    payload = json.loads(data_content)
                    if payload.get("id") == 2:
                        print(f"[OK] Received Tools List: {json.dumps(payload, indent=2)}")
                        break
                except json.JSONDecodeError:
                    pass
                    
        # Call monitor_system_health tool
        tool_call = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "monitor_system_health",
                "arguments": {
                    "detailed": True
                }
            }
        }
        print("Calling 'monitor_system_health' tool...")
        post_response = await client.post(messages_url, json=tool_call)
        print(f"Tool Call POST status: {post_response.status_code}")
        
        # Listen for tool call response
        async for line in lines_iterator:
            print(f"SSE Raw Line: {line}")
            if line.startswith("data:"):
                data_content = line[5:].strip()
                try:
                    payload = json.loads(data_content)
                    if payload.get("id") == 3:
                        print(f"[OK] Received Tool Call Response: {json.dumps(payload, indent=2)}")
                        break
                except json.JSONDecodeError:
                    pass

    await client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
