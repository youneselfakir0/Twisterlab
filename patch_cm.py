import json
import subprocess
import sys

def main():
    try:
        with open("src/twisterlab/ui/index.html", "r", encoding="utf-8") as f:
            index_html = f.read()
        with open("src/twisterlab/ui/index.css", "r", encoding="utf-8") as f:
            index_css = f.read()
        with open("src/twisterlab/api/main.py", "r", encoding="utf-8") as f:
            main_py = f.read()
            
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
        print("Restarting pods...")
        subprocess.run(["kubectl", "rollout", "restart", "deployment/twisterlab-api", "-n", "twisterlab"], check=True)
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
