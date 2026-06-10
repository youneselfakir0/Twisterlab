import json
import os

with open('configmap.json', 'r', encoding='utf-16') as f:
    cm = json.load(f)

cm['data'] = {}

# 1. Base files (Hybrid/Graceful)
with open('index.html', 'r', encoding='utf-8') as f:
    cm['data']['index.html'] = f.read()
with open('index.css', 'r', encoding='utf-8') as f:
    cm['data']['index.css'] = f.read()
with open('main_graceful.py', 'r', encoding='utf-8') as f:
    cm['data']['main.py'] = f.read()
with open('api_init.py', 'r', encoding='utf-8') as f:
    cm['data']['__init__.py'] = f.read()
with open('session_stable.py', 'r', encoding='utf-8') as f:
    cm['data']['session.py'] = f.read()

# We only mount files that we are sure exist or that we want to try to override
# For now, let's keep it simple to ensure it STARTS.

with open('configmap_stabilized.json', 'w', encoding='utf-8') as f:
    json.dump(cm, f, indent=2)
