
import subprocess
import time
import sys
import os

NAMESPACE = "twisterlab"
DEV_NAMESPACE = "twisterlab-dev"
BUILDER_POD = "builder"
DEBUGGER_POD = "node-debugger"
IMAGE_NAME = "twisterlab/mcp-unified:dev"
TAR_PATH = "/transfer/dev.tar"

def run_cmd(cmd, shell=True, check=True):
    print(f"🔄 Executing: {cmd}")
    try:
        subprocess.run(cmd, shell=shell, check=check)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)

def ensure_pods():
    print("🔍 Checking builder and debugger pods...")
    # Check builder
    try:
        subprocess.run(f"kubectl get pod {BUILDER_POD} -n {NAMESPACE}", shell=True, check=True, stdout=subprocess.DEVNULL)
    except:
        print(f"⚠️ Builder pod missing in {NAMESPACE}. Please deploy builder-pod.yaml first.")
        sys.exit(1)
        
    # Check debugger
    try:
        subprocess.run(f"kubectl get pod {DEBUGGER_POD} -n {NAMESPACE}", shell=True, check=True, stdout=subprocess.DEVNULL)
    except:
        print(f"⚠️ Node debugger pod missing in {NAMESPACE}. Please deploy node-debugger.yaml first.")
        sys.exit(1)

def build_and_deploy():
    ensure_pods()
    
    print("\n📦 1. Cleaning remote build directory...")
    run_cmd(f"kubectl exec {BUILDER_POD} -n {NAMESPACE} -- rm -rf /build/src")
    run_cmd(f"kubectl exec {BUILDER_POD} -n {NAMESPACE} -- mkdir -p /build/src")
    
    print("\n📂 2. Transferring source code...")
    run_cmd(f"kubectl cp src {NAMESPACE}/{BUILDER_POD}:/build/")
    run_cmd(f"kubectl cp requirements.txt {NAMESPACE}/{BUILDER_POD}:/build/requirements.txt")
    run_cmd(f"kubectl cp deploy/docker/Dockerfile.mcp-unified {NAMESPACE}/{BUILDER_POD}:/build/Dockerfile")
    
    # Verify structure
    run_cmd(f"kubectl exec {BUILDER_POD} -n {NAMESPACE} -- ls -F /build/src")
        
    # Append deps fix - Removed as local file is now fixed
    print("\n✅ Requirements should be up to date from local source.")

    print("\n🔨 5. Building Docker image (Remote)...")
    # run_cmd(f"kubectl exec {BUILDER_POD} -n {NAMESPACE} -- sh -c 'cd /build && docker build --no-cache -t {IMAGE_NAME} .'")
    run_cmd(f"kubectl exec {BUILDER_POD} -n {NAMESPACE} -- docker build --no-cache -t {IMAGE_NAME} -f /build/Dockerfile /build")
    
    print("\n💾 6. Exporting image to shared volume...")
    run_cmd(f"kubectl exec {BUILDER_POD} -n {NAMESPACE} -- docker save {IMAGE_NAME} -o {TAR_PATH}")
    
    print("\n📥 7. Importing image to K3s/Containerd...")
    run_cmd(f"kubectl exec {DEBUGGER_POD} -n {NAMESPACE} -- chroot /host k3s ctr images import /tmp/dev.tar")
    
    print(f"\n🚀 8. Restarting Deployment in {DEV_NAMESPACE}...")
    run_cmd(f"kubectl rollout restart deployment mcp-unified -n {DEV_NAMESPACE}")
    run_cmd(f"kubectl rollout status deployment/mcp-unified -n {DEV_NAMESPACE} --timeout=60s")
    
    print("\n✅ DEPLOYMENT COMPLETE! Dev Environment Updated.")
    print(f"👉 Access URL: http://192.168.0.30:31080/tools")

if __name__ == "__main__":
    build_and_deploy()
