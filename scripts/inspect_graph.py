import urllib.request
import json

URL = "http://127.0.0.1:9091"

def safe_get(endpoint):
    req = urllib.request.Request(f"{URL}{endpoint}")
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf-8'))

try:
    print("Fetching last queue item...")
    q_all = safe_get("/api/v1/queue/default/list_all")
    if not q_all:
        exit(1)
        
    last_item = q_all[-1]
    graph = last_item["session"]["graph"]
    
    for node_id, node in graph["nodes"].items():
        node_type = node.get("type", "")
        if "lora" in node_type.lower():
            print(f"LORA NODE FOUND: {node_id}")
            print(json.dumps(node, indent=2))
        elif node_type == "core_metadata":
            print("CORE METADATA:")
            print(json.dumps(node.get("loras", []), indent=2))
            
except Exception as e:
    print(f"Error: {e}")
