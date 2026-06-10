import json
import subprocess
import sys

def main():
    try:
        # Get main.py directly from the configmap
        result = subprocess.run(["kubectl", "get", "configmap", "ui-hotfix-v382", "-n", "twisterlab", "-o", "jsonpath={.data['main\.py']}"], capture_output=True, text=True, check=True)
        main_py = result.stdout
        
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
