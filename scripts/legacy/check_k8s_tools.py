
import requests
import json
import sys

URL = "http://192.168.0.30:30080/tools"
try:
    print(f"Checking {URL}...")
    resp = requests.get(URL, timeout=5)
    resp.raise_for_status()
    data = resp.json()
    tools = data.get('tools', [])
    tool_names = [t['name'] for t in tools]
    print(f"Found {len(tools)} tools.")
    print(f"Tools: {', '.join(tool_names)}")
    
    required = ['browser_browse', 'real-desktop-commander_execute_command']
    missing = [r for r in required if r not in tool_names]
    
    if missing:
        print(f"❌ MISSING TOOLS: {missing}")
        sys.exit(1)
    else:
        print("✅ All required tools present.")
        
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
