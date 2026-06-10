import subprocess
import json

p = subprocess.Popen(
    ['cmd.exe', '/c', r'C:\Users\Administrator\Documents\twisterlab\scripts\run_twisterlab_mcp.bat'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

out, err = p.communicate(b'{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}\n')

try:
    data = json.loads(out.decode('utf-8'))
    tools = data.get('result', {}).get('tools', [])
    print(f"Total tools: {len(tools)}")
    invoke_tools = [t for t in tools if 'invoke' in t.get('name', '')]
    for t in invoke_tools:
        print(json.dumps(t, indent=2))
except Exception as e:
    print("Error parsing json:", e)
    print("RAW:", repr(out[:200]))
