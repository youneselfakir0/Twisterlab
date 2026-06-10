import subprocess
import json

p = subprocess.Popen(
    [
        r'C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe',
        '-u',
        r'C:\Users\Administrator\Documents\twisterlab\mcp_paramiko.py'
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

req = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
}

req_str = json.dumps(req) + "\n"
p.stdin.write(req_str.encode('utf-8'))
p.stdin.flush()

while True:
    line = p.stdout.readline()
    if not line: break
    if b'"result"' in line:
        data = json.loads(line.decode('utf-8'))
        tools = [t['name'] for t in data['result']['tools']]
        n8n_tools = [t for t in tools if 'n8n' in t]
        print("n8n tools found:", n8n_tools)
        break

p.terminate()
