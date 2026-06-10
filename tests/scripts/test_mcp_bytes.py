import subprocess
p = subprocess.Popen(
    ['cmd.exe', '/c', r'C:\Users\Administrator\Documents\twisterlab\scripts\run_twisterlab_mcp.bat'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
out, err = p.communicate(b'{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}\n')
print(f"OUT bytes ({len(out)}):")
print(out)
print(f"ERR bytes ({len(err)}):")
print(err)
