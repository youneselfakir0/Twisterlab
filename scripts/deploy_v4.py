import subprocess
import json
import sys

def run(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}")
        sys.exit(1)
    return res.stdout

print("1. Creating build directory on remote...")
run('ssh twister@192.168.0.30 "mkdir -p /tmp/build-v4"')

print("2. Copying source files...")
run('scp -r src requirements.txt deploy/docker/Dockerfile.mcp-unified twister@192.168.0.30:/tmp/build-v4/')

print("3. Building and importing image (v4.0)...")
build_cmd = 'ssh twister@192.168.0.30 "cd /tmp/build-v4 && sudo docker build -t twisterlab/mcp-unified:v4.0 -f Dockerfile.mcp-unified . && sudo docker save twisterlab/mcp-unified:v4.0 | sudo k3s ctr images import - && rm -rf /tmp/build-v4"'
run(build_cmd)

print("4. Updating Kubernetes deployment...")
live_json = run('kubectl get deployment mcp-unified -n twisterlab -o json')
deploy_data = json.loads(live_json)

# Clean out specific patches and volumes
container = deploy_data['spec']['template']['spec']['containers'][0]

# Remove volume mounts related to hotfixes
if 'volumeMounts' in container:
    container['volumeMounts'] = [vm for vm in container['volumeMounts'] 
                                 if not any(v in vm['name'] for v in ['patch', 'hotfix'])]
    if not container['volumeMounts']:
        del container['volumeMounts']

# Remove volumes from pod spec
pod_spec = deploy_data['spec']['template']['spec']
if 'volumes' in pod_spec:
    pod_spec['volumes'] = [v for v in pod_spec['volumes'] 
                           if not any(p in v['name'] for p in ['patch', 'hotfix'])]
    if not pod_spec['volumes']:
        del pod_spec['volumes']

# Set new image
container['image'] = 'twisterlab/mcp-unified:v4.0'
container['imagePullPolicy'] = 'Never' # Force use of local ctr imported image

# Remove status and redundant metadata for clean replace
if 'status' in deploy_data:
    del deploy_data['status']
if 'resourceVersion' in deploy_data['metadata']:
    del deploy_data['metadata']['resourceVersion']
if 'uid' in deploy_data['metadata']:
    del deploy_data['metadata']['uid']

with open('patched_mcp_unified.json', 'w') as f:
    json.dump(deploy_data, f, indent=2)

print("5. Applying cleaned deployment...")
run('kubectl replace --force -f patched_mcp_unified.json')

print("Phase 1 Complete! v4.0 deployed and technical debt eliminated.")
