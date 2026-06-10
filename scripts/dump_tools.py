import json, subprocess
p = subprocess.Popen(
    ['cmd.exe', '/c', r'C:\Users\Administrator\Documents\twisterlab\scripts\run_twisterlab_mcp.bat'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
out, err = p.communicate(b'{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}\n')
data = json.loads(out.decode('utf-8'))
with open('C:/Users/Administrator/Documents/twisterlab/tools_dump.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(data, indent=2))
