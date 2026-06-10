import json
import urllib.request
import random
import copy
from run_instagram_bot import INVOKE_URL, AGENCY_MODELS, DAILY_CONTENT

print("Démarrage du test pour TOUS les modèles de l'Agence...")

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

count = 0
for model_info in AGENCY_MODELS:
    lora_search = model_info["lora_search"]
    keyword = model_info["keyword"]
    
    # Random context for this model
    content = random.choice(DAILY_CONTENT)
    prompt = content["prompt"].replace("{model}", keyword)
    
    print(f"\n🌟 Modèle : {keyword} (Recherche: {lora_search})")
    print(f"   Prompt : '{prompt[:60]}...'")
    
    target_lora = next((m for m in models_data.get("models", []) if lora_search in m.get("name", "").lower() and m.get("type") == "lora"), None)
    
    if not target_lora:
        print(f"   ⚠️ Attention, le LoRA {lora_search} est introuvable sur le serveur ! Génération annulée pour ce modèle.")
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
            if target_lora and "loras" in node and len(node["loras"]) > 0:
                node["loras"][0]["model"] = {
                    "key": target_lora["key"],
                    "hash": target_lora["hash"],
                    "name": target_lora["name"],
                    "base": target_lora["base"],
                    "type": "lora",
                    "submodel_type": None
                }
        elif node_type == "lora_selector" and target_lora:
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
    post_json(f"{INVOKE_URL}/api/v1/queue/default/enqueue_batch", batch_payload)
    count += 1
    
print(f"\n✅ {count} images d'agence ont été envoyées à la file d'attente d'Invoke AI !")
