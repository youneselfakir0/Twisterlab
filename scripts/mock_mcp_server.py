import sys
import json
import time

def send_response(resp):
    line = json.dumps(resp) + "\n"
    sys.stdout.buffer.write(line.encode('utf-8'))
    sys.stdout.buffer.flush()

for line in sys.stdin:
    if not line.strip():
        continue
    try:
        req = json.loads(line)
        method = req.get("method")
        req_id = req.get("id")
        
        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "twisterlab", "version": "2.0.0"},
                    "capabilities": {"tools": {"listChanged": True}}
                }
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            # Just send a massive identical tool list to test limits!
            with open("C:/Users/Administrator/Documents/twisterlab/tools_dump.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": data["result"]
            })
    except Exception as e:
        with open("C:/Users/Administrator/Documents/twisterlab/mock_error.txt", "a") as f:
            f.write(f"Error: {e}\n")
