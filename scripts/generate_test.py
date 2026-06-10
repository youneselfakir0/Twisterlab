import urllib.request
import urllib.parse
import json
import random
import time

URL = "http://127.0.0.1:9091"

def safe_get(endpoint):
    req = urllib.request.Request(f"{URL}{endpoint}")
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf-8'))

def safe_post(endpoint, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(f"{URL}{endpoint}", data=data, headers={'Content-Type': 'application/json'})
    response = urllib.request.urlopen(req)
    return json.loads(response.read().decode('utf-8'))

try:
    print("1. Fetching last queue item to clone graph...")
    q_all = safe_get("/api/v1/queue/default/list_all")
    if not q_all or len(q_all) == 0:
        print("Error: No items in the queue. You must create at least one picture from the Invoke web UI first!")
        exit(1)
        
    last_item = q_all[-1]
    graph = last_item["session"]["graph"]
    
    print("2. Modifying graph with new prompt...")
    prompt = "A stunning cyberpunk portrait of a female cyborg with glowing neon wires, highly detailed, dramatic lighting, 8k resolution, masterpiece."
    negative_prompt = "blurry, low quality, deformed, mutated, ugly"
    new_seed = random.randint(0, 2147483647)
    
    prompt_injected = False
    for node_id, node in graph["nodes"].items():
        node_type = node.get("type", "")
        if node_type == "string" and "positive" in node_id.lower():
            node["value"] = prompt
            prompt_injected = True
        elif node_type == "string" and "negative" in node_id.lower():
            node["value"] = negative_prompt
        elif node_type == "core_metadata":
            node["positive_prompt"] = prompt
            node["negative_prompt"] = negative_prompt
            node["seed"] = new_seed
        elif node_type == "integer" and "seed" in node_id.lower():
            node["value"] = new_seed
            
    if not prompt_injected:
        print("Warning: Could not strictly identify 'positive' text node. Relying on core_metadata.")
        
    batch_payload = {
        "batch": {
            "graph": graph,
            "runs": 1
        },
        "prepend": False
    }
    
    print("3. Enqueueing new image generation...")
    res = safe_post("/api/v1/queue/default/enqueue_batch", batch_payload)
    batch_id = res.get("batch", {}).get("batch_id")
    print(f"Success! Enqueued batch ID: {batch_id}")
    print(f"Prompt used: {prompt}")
    
except Exception as e:
    print(f"Error: {e}")
