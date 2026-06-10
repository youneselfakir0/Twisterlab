
import os
import subprocess
import tarfile
import sys
import time

# Configuration
NAMESPACE_DEV = "twisterlab-dev"
NAMESPACE_PROD = "twisterlab"
BUILDER_POD = "builder"
IMAGE_NAME = "twisterlab/mcp-unified:dev"
DOCKERFILE = "deploy/docker/Dockerfile.mcp-unified"
DEPLOYMENT_NAME = "mcp-unified"
LOCAL_ARCHIVE = "context.tar.gz"
REMOTE_ARCHIVE = "/tmp/context.tar.gz"
REMOTE_BUILD_DIR = "/build"

EXCLUDES = [
    ".git", ".venv", "__pycache__", ".idea", ".vscode", "node_modules",
    "coverage", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".copilot", ".continue", "archive", "videos", "screenshots"
]

def log(msg):
    print(f"[DEV-DEPLOY] {msg}")

def run_command(cmd, shell=False):
    log(f"Running: {cmd}")
    try:
        subprocess.check_call(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        log(f"Error running command: {e}")
        sys.exit(1)

def create_archive():
    log("Creating context archive...")
    with tarfile.open(LOCAL_ARCHIVE, "w:gz") as tar:
        for item in os.listdir("."):
            if item in EXCLUDES or item == LOCAL_ARCHIVE:
                continue
            tar.add(item)
    log(f"Archive created: {LOCAL_ARCHIVE} ({os.path.getsize(LOCAL_ARCHIVE) / 1024 / 1024:.2f} MB)")

def stream_and_build():
    log("1. Streaming context to builder and building...")
    
    # Combined command: Clean, Extract, Build, Save
    remote_cmd = (
        f"rm -rf {REMOTE_BUILD_DIR} && "
        f"mkdir -p {REMOTE_BUILD_DIR} && "
        f"cd {REMOTE_BUILD_DIR} && "
        f"tar xzm && "
        f"docker build -t {IMAGE_NAME} -f {DOCKERFILE} . && "
        f"echo 'Saving image to transfer volume...' && "
        f"docker save {IMAGE_NAME} -o /transfer/mcp-dev.tar && "
        f"docker image prune -f"
    )
    
    kubectl_cmd = ["kubectl", "exec", "-i", "-n", NAMESPACE_PROD, BUILDER_POD, "--", "sh", "-c", remote_cmd]
    
    log(f"Executing build & save: {' '.join(kubectl_cmd)}")
    
    proc = subprocess.Popen(kubectl_cmd, stdin=subprocess.PIPE)
    
    with tarfile.open(fileobj=proc.stdin, mode="w:gz") as tar:
        for item in os.listdir("."):
            if item in EXCLUDES or item == LOCAL_ARCHIVE:
                continue
            tar.add(item)
    
    proc.stdin.close()
    
    ret = proc.wait()
    if ret != 0:
        log("Build failed!")
        sys.exit(1)

def import_image():
    log("2. Importing image into K3s containerd...")
    # Using node-debugger to execute k3s ctr import on the host
    # Host /tmp is mounted as /transfer in builder, so file is at /tmp/mcp-dev.tar on host
    cmd = [
        "kubectl", "exec", "-n", NAMESPACE_PROD, "node-debugger", "--",
        "chroot", "/host", "k3s", "ctr", "images", "import", "/tmp/mcp-dev.tar"
    ]
    run_command(cmd)

def restart_deployment():
    log("3. Restarting deployment...")
    cmd = f"kubectl rollout restart deployment/{DEPLOYMENT_NAME} -n {NAMESPACE_DEV}"
    run_command(cmd)
    
    log("Waiting for rollout...")
    cmd = f"kubectl rollout status deployment/{DEPLOYMENT_NAME} -n {NAMESPACE_DEV}"
    run_command(cmd)

def verify_health():
    log("4. Verifying health...")
    time.sleep(5)
    try:
        import requests
        url = "http://192.168.0.30:31080/health"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                log(f"✅ Health Check PASSED: Version {data.get('version')}")
            else:
                log(f"❌ Health Check FAILED: {resp.status_code} - {resp.text}")
        except Exception as e:
            log(f"❌ Health Check Error: {e}")
    except ImportError:
        log("requests module not found, skipping python verification")

def main():
    start_time = time.time()
    try:
        # Step 1: Build & Save
        stream_and_build()
        # Step 2: Import to K3s
        import_image()
        # Step 3: Deploy
        restart_deployment()
        # Step 4: Verify
        verify_health()
        
        log(f"🚀 Deployment completed in {time.time() - start_time:.2f}s")
    except KeyboardInterrupt:
        log("Deployment cancelled.")
    finally:
        if os.path.exists(LOCAL_ARCHIVE):
            os.remove(LOCAL_ARCHIVE)

if __name__ == "__main__":
    if not os.path.exists("deploy/docker"):
        log("Error: Run this script from the project root")
        sys.exit(1)
    main()
