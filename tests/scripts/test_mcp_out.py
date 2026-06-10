import subprocess
import time

out = subprocess.check_output(
    ['cmd.exe', '/c', r'C:\Users\Administrator\Documents\twisterlab\scripts\run_twisterlab_mcp.bat'],
    input=b'{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}\n'
)
print("RAW OUT REP:", repr(out[:100]))
