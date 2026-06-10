import subprocess

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

out, err = p.communicate(b'{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}\n')
print("OUT:", repr(out[:100]))
print("ERR:", err.decode('utf-8'))
