import json
import os

CONFIG_PATH = r"C:\Users\Administrator\.gemini\antigravity\mcp_config.json"

def update_config():
    print(f"Reading {CONFIG_PATH}...")
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading config: {e}")
        return

    print("Adding 'twisterlab' server...")
    
    # Define the new server config
    twisterlab_config = {
        "command": "npx",
        "args": [
            "-y",
            "mcp-remote",
            "http://192.168.0.30:30080/mcp", 
            "--allow-http"
        ],
        "env": {
            "MCP_LOG_LEVEL": "INFO"
        }
    }

    # Ensure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Update or add twisterlab
    config["mcpServers"]["twisterlab"] = twisterlab_config

    print("Writing updated config...")
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        print("Success!")
    except Exception as e:
        print(f"Error writing config: {e}")

if __name__ == "__main__":
    update_config()
