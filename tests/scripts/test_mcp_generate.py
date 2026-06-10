import subprocess
import json
import time

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
    "method": "tools/call",
    "params": {
        "name": "invoke-ai_generate_image",
        "arguments": {
            "prompt": "A breathtaking cinematic wide-shot of the 'Ouroboros Ring', a colossal abandoned torus-shaped space station orbiting a dormant black hole. The outer rings are decaying and overgrown with glowing blue and purple bioluminescent alien flora. The architecture features gothic metallic curves, deep rust, and shattered glass domes. In the background, the faint accretion disk of the black hole emits an eerie golden light. Highly detailed, sci-fi concept art, dramatic lighting, 8k resolution, photorealistic, masterpiece."
        }
    }
}

req_str = json.dumps(req) + "\n"
p.stdin.write(req_str.encode('utf-8'))
p.stdin.flush()

while True:
    line = p.stdout.readline()
    if not line: break
    print(line.decode('utf-8'))
    if b'"result"' in line:
        break

p.terminate()
