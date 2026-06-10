import subprocess
import time
p = subprocess.Popen(
    ['cmd.exe', '/c', r'C:\Users\Administrator\Documents\twisterlab\scripts\run_twisterlab_mcp.bat'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

def send(data):
    p.stdin.write(data + b"\n")
    p.stdin.flush()
    time.sleep(0.5)

send(b'{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}')
print("INIT SENT")
print(p.poll())

send(b'{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}')
print("NOTIF SENT")
print(p.poll())

send(b'{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}')
print("TOOLS LIST SENT")
print(p.poll())

# Wait and read output
time.sleep(1)
out = p.stdout.read()
err = p.stderr.read()
print(f"RC: {p.poll()}")
print(f"OUT ({len(out)}):", out.decode('utf-8', errors='replace')[:200])
print(f"ERR ({len(err)}):", err.decode('utf-8', errors='replace'))
