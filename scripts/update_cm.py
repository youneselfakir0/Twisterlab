import subprocess
import json
import os

def update_configmap():
    # Get current configmap
    print("Fetching current configmap api-hotfix-v3...")
    result = subprocess.run(
        ["kubectl", "get", "cm", "api-hotfix-v3", "-n", "twisterlab", "-o", "json"],
        capture_output=True
    )
    if result.returncode != 0:
        print("Failed to get configmap:", result.stderr.decode('utf-8', errors='ignore'))
        return

    cm = json.loads(result.stdout.decode('utf-8'))
    
    # Read our local files
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        with open("index.css", "r", encoding="utf-8") as f:
            css_content = f.read()
        # Add main.py fix
        main_path = os.path.join("src", "twisterlab", "api", "main.py")
        with open(main_path, "r", encoding="utf-8") as f:
            main_content = f.read()
        # Add agent fixes
        notion_path = os.path.join("src", "twisterlab", "agents", "real", "real_notion_agent.py")
        with open(notion_path, "r", encoding="utf-8") as f:
            notion_content = f.read()
    except Exception as e:
        print("Error reading local files:", e)
        return

    # Update the data
    if "data" not in cm:
        cm["data"] = {}
    
    cm["data"]["index.html"] = html_content
    cm["data"]["index.css"] = css_content
    cm["data"]["main.py"] = main_content
    cm["data"]["real_notion_agent.py"] = notion_content

    # Save to temp file
    with open("temp_cm.json", "w", encoding="utf-8") as f:
        json.dump(cm, f)

    # Apply
    print("Applying updated configmap...")
    apply_result = subprocess.run(
        ["kubectl", "apply", "-f", "temp_cm.json"],
        capture_output=True
    )
    
    print(apply_result.stdout.decode('utf-8', errors='ignore'))
    if apply_result.stderr:
        print("Errors:", apply_result.stderr.decode('utf-8', errors='ignore'))
        
    print("Now restarting deployment to ensure changes take effect...")
    restart = subprocess.run(
        ["kubectl", "rollout", "restart", "deployment/twisterlab-api", "-n", "twisterlab"],
        capture_output=True, text=True
    )
    print(restart.stdout)

if __name__ == "__main__":
    update_configmap()
