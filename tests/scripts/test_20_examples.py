import json
import urllib.request
import random
import copy
from run_instagram_bot import INVOKE_URL, AGENCY_MODELS, DAILY_CONTENT

print("Démarrage du test pour 20 exemples de l'Agence (Visage + Corps + Réalisme)...")

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

original_graph = queue[-1].get("session", {}).get("graph")

PROTECTED_LORA_KEYWORDS = ["realism", "detailed", "style", "texture", "muscle", "toned", "body", "hips", "fitness", "ass", "leg", "gym", "skin"]

count = 0
for i in range(20):
    model_info = random.choice(AGENCY_MODELS)
    lora_search = model_info["lora_search"]
    keyword = model_info["keyword"]
    
    # Context
    content = random.choice(DAILY_CONTENT)
    prompt = content["prompt"].replace("{model}", keyword)
    
    target_lora = next((m for m in models_data.get("models", []) if lora_search in m.get("name", "").lower() and m.get("type") == "lora"), None)
    
    if not target_lora:
        print(f"[{i+1}/20] ⚠️ LoRA {lora_search} est introuvable. Skip.")
        continue

    graph = copy.deepcopy(original_graph)
    new_seed = random.randint(0, 2147483647)

    for node_id, node in graph["nodes"].items():
        node_type = node.get("type", "")
        if node_type == "string" and "positive" in node_id.lower():
            node["value"] = prompt
        
        elif node_type == "core_metadata":
            node["positive_prompt"] = prompt
            node["seed"] = new_seed
            if target_lora and "loras" in node:
                for idx in range(len(node["loras"])):
                    lname = node["loras"][idx].get("model", {}).get("name", "").lower()
                    if not any(k in lname for k in PROTECTED_LORA_KEYWORDS):
                        node["loras"][idx]["model"]["key"] = target_lora["key"]
                        node["loras"][idx]["model"]["hash"] = target_lora["hash"]
                        node["loras"][idx]["model"]["name"] = target_lora["name"]
                        node["loras"][idx]["model"]["base"] = target_lora["base"]
                        break
                        
        elif node_type == "lora_selector" and target_lora:
            lname = node.get("lora", {}).get("name", "").lower()
            if not any(k in lname for k in PROTECTED_LORA_KEYWORDS):
                node["lora"] = {
                    "key": target_lora["key"],
                    "hash": target_lora["hash"],
                    "name": target_lora["name"],
                    "base": target_lora["base"],
                    "type": "lora",
                    "submodel_type": None
                }
                
        elif node_type == "integer" and "seed" in node_id.lower():
            node["value"] = new_seed

    batch_payload = {"batch": {"graph": graph, "runs": 1}, "prepend": False}
    print(f"[{i+1}/20] Modèle: {keyword} | Tâche en File d'Attente.")
    post_json(f"{INVOKE_URL}/api/v1/queue/default/enqueue_batch", batch_payload)
    count += 1
    
print(f"\n✅ {count} images combinant vos 3 LoRAs ont été envoyées à Invoke AI !")
