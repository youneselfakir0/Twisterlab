import json
with open('C:/Users/Administrator/Documents/twisterlab/tools_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
tools = [t for t in data['result']['tools'] if 'invoke' in t['name']]
with open('C:/Users/Administrator/Documents/twisterlab/tools_invoke.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(tools, indent=2))
