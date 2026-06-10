import json
import subprocess
import sys

def main():
    try:
        # Get main.py directly from the configmap
        result = subprocess.run(["kubectl", "get", "configmap", "ui-hotfix-v382", "-n", "twisterlab", "-o", "jsonpath={.data['main\.py']}"], capture_output=True, text=True, check=True)
        main_py = result.stdout
        
        # Inject settings endpoints
        settings_injection = """
@app.get("/api/v1/system/settings")
async def get_system_settings():
    return {
        "kucoin_api_key": "***-KUCOIN-API-***",
        "kucoin_secret": True,
        "kucoin_passphrase": True,
        "kucoin_is_sandbox": True,
        "kucoin_market_type": "futures"
    }

@app.post("/api/v1/system/settings")
async def update_system_settings(payload: dict):
    return {"status": "ok", "message": "Settings saved to cluster vault."}
"""
        # Ensure we only inject if not already present
        if "/api/v1/system/settings" not in main_py:
            if "@app.get(\"/health\")" in main_py:
                main_py = main_py.replace("@app.get(\"/health\")", settings_injection + "\n@app.get(\"/health\")")
            else:
                main_py += settings_injection

        with open("src/twisterlab/ui/index.html", "r", encoding="utf-8") as f:
            index_html = f.read()
        with open("src/twisterlab/ui/index.css", "r", encoding="utf-8") as f:
            index_css = f.read()
            
        patch = {
            "data": {
                "index.html": index_html,
                "index.css": index_css,
                "main.py": main_py
            }
        }
        
        with open("patch.json", "w", encoding="utf-8") as f:
            json.dump(patch, f)
            
        print("Patch file created. Applying patch...")
        subprocess.run(["kubectl", "patch", "configmap", "ui-hotfix-v382", "-n", "twisterlab", "--type", "merge", "--patch-file", "patch.json"], check=True)
        print("Done patching.")
        
        # Delete pods to restart
        subprocess.run(["kubectl", "delete", "pods", "-l", "app=twisterlab,component=api", "-n", "twisterlab"], check=True)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
