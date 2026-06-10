import json
import subprocess
import os

def run(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}")
        exit(1)
    return res.stdout

print("Fetching live deployment...")
live_json = run('kubectl get deployment mcp-unified -n twisterlab -o json')
deploy_data = json.loads(live_json)

# Clean out old hotfixes
container = deploy_data['spec']['template']['spec']['containers'][0]

if 'volumeMounts' in container:
    container['volumeMounts'] = [vm for vm in container['volumeMounts'] 
                                 if not any(v in vm['name'] for v in ['patch', 'hotfix'])]
    if not container['volumeMounts']:
        del container['volumeMounts']

pod_spec = deploy_data['spec']['template']['spec']
if 'volumes' in pod_spec:
    pod_spec['volumes'] = [v for v in pod_spec['volumes'] 
                           if not any(v['name'] in ['fixes'] or p in v['name'] for p in ['patch', 'hotfix'])]
    if not pod_spec['volumes']:
        del pod_spec['volumes']

# Set image to v4.0
container['image'] = '192.168.0.30:8090/library/mcp-unified:v4.0'

# Clean metadata for replace
if 'status' in deploy_data:
    del deploy_data['status']
for key in ['resourceVersion', 'uid', 'creationTimestamp', 'generation']:
    if key in deploy_data['metadata']:
        del deploy_data['metadata'][key]

with open('mcp_v4_clean.json', 'w') as f:
    json.dump(deploy_data, f, indent=2)

print("Patching deployment...")
run('kubectl replace --force -f mcp_v4_clean.json')
print("K8s deployment successfully updated to v4.0 and cleaned of technical debt!")
