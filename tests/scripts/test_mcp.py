import subprocess
p = subprocess.Popen(
    ['cmd.exe', '/c', r'C:\Users\Administrator\Documents\twisterlab\scripts\run_twisterlab_mcp.bat'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
out, err = p.communicate(b'{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}\n{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}\n{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}\n')
print('OUT:', out.decode('utf-8', errors='replace')[:500])
import json
try:
    lines = out.decode('utf-8').strip().split('\n')
    json.loads(lines[-1])
    print('JSON IS VALID')
except Exception as e:
    print('JSON ERROR:', e)
print('ERR:', err.decode('utf-8', errors='replace'))
print('RC:', p.returncode)
