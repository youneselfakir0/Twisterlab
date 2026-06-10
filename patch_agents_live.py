import json
import subprocess
import sys

def main():
    # Get main.py directly from the configmap
    result = subprocess.run(["kubectl", "get", "configmap", "ui-hotfix-v382", "-n", "twisterlab", "-o", "jsonpath={.data['main\\.py']}"], capture_output=True, text=True, check=True)
    main_py = result.stdout

    # Inject a new live agents endpoint that reads from the in-memory registry
    live_agents_endpoint = """
@app.get("/api/v1/agents/live")
async def list_live_agents():
    \"\"\"Lists all agents from the in-memory registry (not DB repo).\"\"\"
    try:
        from twisterlab.agents.registry import get_agent_registry
        registry = get_agent_registry()
        agents_dict = registry.list_agents()
        result = []
        for name, meta in agents_dict.items():
            if isinstance(meta, dict):
                result.append({
                    "name": meta.get("name", name),
                    "description": meta.get("description", ""),
                    "status": "online" if meta.get("initialized") else "registered",
                    "capabilities": meta.get("capabilities", []),
                    "tools": meta.get("capabilities", []),
                })
            else:
                result.append({"name": name, "description": str(meta), "status": "registered", "capabilities": [], "tools": []})
        return result
    except Exception as e:
        return []
"""

    if "/api/v1/agents/live" not in main_py:
        if '@app.get("/health")' in main_py:
            main_py = main_py.replace('@app.get("/health")', live_agents_endpoint + '\n@app.get("/health")')
        else:
            main_py += live_agents_endpoint

    with open("src/twisterlab/ui/index.html", "r", encoding="utf-8") as f:
        index_html = f.read()
    # Swap the agents fetch URL
    index_html = index_html.replace(
        "const r = await fetch('/api/v1/agents/');",
        "const r = await fetch('/api/v1/agents/live');"
    )
    with open("src/twisterlab/ui/index.css", "r", encoding="utf-8") as f:
        index_css = f.read()

    patch = {"data": {"index.html": index_html, "index.css": index_css, "main.py": main_py}}
    with open("patch.json", "w", encoding="utf-8") as f:
        json.dump(patch, f)

    subprocess.run(["kubectl", "patch", "configmap", "ui-hotfix-v382", "-n", "twisterlab", "--type", "merge", "--patch-file", "patch.json"], check=True)
    print("ConfigMap patched. Restarting pods...")
    subprocess.run(["kubectl", "delete", "pods", "-l", "app=twisterlab,component=api", "-n", "twisterlab"], check=True)
    print("Done.")

if __name__ == "__main__":
    main()
