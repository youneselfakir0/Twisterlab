import json
import os
import sys

# Path mapping for hotfixed files
MAPPING = {
    "cortex_ia_agent.py": "src/twisterlab/agents/real/cortex_ia_agent.py",
    "index.css": "index.css",
    "index.html": "index.html",
    "invoke_ai_agent.py": "src/twisterlab/agents/real/invoke_ai_agent.py",
    "main.py": "src/twisterlab/api/main.py",
    "n8n_navigator_agent.py": "src/twisterlab/agents/real/n8n_navigator_agent.py",
    "openclaw_agent.py": "src/twisterlab/agents/real/openclaw_agent.py",
    "openclaw_tool.py": "src/twisterlab/agents/core/openclaw_tool.py",
    "real_archive_agent.py": "src/twisterlab/agents/real/real_archive_agent.py",
    "real_maestro_agent.py": "src/twisterlab/agents/real/real_maestro_agent.py",
    "real_notion_agent.py": "src/twisterlab/agents/real/real_notion_agent.py",
    "real_summarizer_agent.py": "src/twisterlab/agents/real/real_summarizer_agent.py",
    "real_translation_agent.py": "src/twisterlab/agents/real/real_translation_agent.py",
    "real_vba_expert_agent.py": "src/twisterlab/agents/real/real_vba_expert_agent.py",
    "registry.py": "src/twisterlab/agents/registry.py",
    "security.py": "src/twisterlab/agents/api/security.py"
}

def sync():
    if not os.path.exists("api_hotfix_v3.json"):
        print("ERROR: api_hotfix_v3.json not found. Run 'kubectl get configmap api-hotfix-v3 -n twisterlab -o json > api_hotfix_v3.json' first.")
        return

    try:
        with open("api_hotfix_v3.json", "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
        with open("api_hotfix_v3.json", "r", encoding="utf-16") as f:
            data = json.load(f)
    
    file_data = data.get("data", {})
    
    print(f"Syncing {len(file_data)} files from production hotfixes to local repository...")
    
    for key, content in file_data.items():
        if key in MAPPING:
            local_path = MAPPING[key]
            # Ensure directory exists if not root
            dir_name = os.path.dirname(local_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            # Write content
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Synced: {local_path}")
        else:
            print(f"  Skipping unknown key: {key}")

    print("\nSync complete. Your local repository now contains the EXACT logic running in production.")
    print("You are ready to build the consolidated Docker image.")

if __name__ == "__main__":
    sync()