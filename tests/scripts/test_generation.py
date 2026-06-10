import run_instagram_bot
import json
import urllib.request
import random

INVOKE_URL = run_instagram_bot.INVOKE_URL

print("Démarrage du test de génération des 8 nouveaux prompts...")

def get_json(url):
    return json.loads(urllib.request.urlopen(url).read())

def post_json(url, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read())

try:
    queue = get_json(f"{INVOKE_URL}/api/v1/queue/default/list_all")
    models_data = get_json(f"{INVOKE_URL}/api/v2/models/")
except Exception as e:
    print(f"❌ Impossible de joindre InvokeAI: {e}")
    exit(1)

mor3na_lora = next((m for m in models_data.get("models", []) if "mor3na" in m.get("name", "").lower() and m.get("type") == "lora"), None)
original_graph = queue[-1].get("session", {}).get("graph")

count = 0
for idx, item in enumerate(run_instagram_bot.DAILY_CONTENT):
    prompt = item["prompt"]
    import copy
    graph = copy.deepcopy(original_graph)
    new_seed = random.randint(0, 2147483647)

    for node_id, node in graph["nodes"].items():
        node_type = node.get("type", "")
        if node_type == "string" and "positive" in node_id.lower():
            node["value"] = prompt
        elif node_type == "core_metadata":
            node["positive_prompt"] = prompt
            node["seed"] = new_seed
            if mor3na_lora and "loras" in node and len(node["loras"]) > 0:
                node["loras"][0]["model"] = {
                    "key": mor3na_lora["key"],
                    "hash": mor3na_lora["hash"],
                    "name": mor3na_lora["name"],
                    "base": mor3na_lora["base"],
                    "type": "lora",
                    "submodel_type": None
                }
        elif node_type == "lora_selector" and mor3na_lora:
            node["lora"] = {
                "key": mor3na_lora["key"],
                "hash": mor3na_lora["hash"],
                "name": mor3na_lora["name"],
                "base": mor3na_lora["base"],
                "type": "lora",
                "submodel_type": None
            }
        elif node_type == "integer" and "seed" in node_id.lower():
            node["value"] = new_seed

    batch_payload = {"batch": {"graph": graph, "runs": 1}, "prepend": False}
    print(f"[{idx+1}/8] Mise en file d'attente du prompt: '{prompt[:40]}...'")
    post_json(f"{INVOKE_URL}/api/v1/queue/default/enqueue_batch", batch_payload)
    count += 1
    
print(f"✅ {count} images envoyées avec succès à InvokeAI pour le test !")
