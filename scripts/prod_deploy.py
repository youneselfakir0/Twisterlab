"""
Production Deploy Script for TwisterLab MCP Unified
Builds and deploys the MCP server to production namespace
"""

import os
import subprocess
import tarfile
import sys
import time

# Configuration
NAMESPACE = "twisterlab"
BUILDER_POD = "builder"
IMAGE_NAME = "twisterlab/mcp-unified:v2.1.0-stable"
DOCKERFILE = "deploy/docker/Dockerfile.mcp-unified"
DEPLOYMENT_NAME = "mcp-unified"
REMOTE_BUILD_DIR = "/build"

EXCLUDES = [
    ".git", ".venv", "__pycache__", ".idea", ".vscode", "node_modules",
    "coverage", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".copilot", ".continue", "archive", "videos", "screenshots",
    "htmlcov", ".coverage", "*.pyc", "*.pyo"
]

def log(msg):
    print(f"[PROD-DEPLOY] {msg}")

def run_command(cmd, shell=True):
    log(f"Running: {cmd}")
    try:
        subprocess.check_call(cmd, shell=shell)
    except subprocess.CalledProcessError as e:
        log(f"Error running command: {e}")
        sys.exit(1)

def stream_and_build():
    log("Step 1: Streaming context to builder and building Docker image...")
    
    # Combined command: Clean, Extract, Build, Save
    remote_cmd = (
        f"rm -rf {REMOTE_BUILD_DIR} && "
        f"mkdir -p {REMOTE_BUILD_DIR} && "
        f"cd {REMOTE_BUILD_DIR} && "
        f"tar xzm && "
        f"docker build -t {IMAGE_NAME} -f {DOCKERFILE} . && "
        f"echo 'Saving image to transfer volume...' && "
        f"docker save {IMAGE_NAME} -o /transfer/mcp-prod.tar && "
        f"docker image prune -f"
    )
    
    kubectl_cmd = ["kubectl", "exec", "-i", "-n", NAMESPACE, BUILDER_POD, "--", "sh", "-c", remote_cmd]
    
    log(f"Building image: {IMAGE_NAME}")
    
    proc = subprocess.Popen(kubectl_cmd, stdin=subprocess.PIPE)
    
    with tarfile.open(fileobj=proc.stdin, mode="w:gz") as tar:
        for item in os.listdir("."):
            skip = False
            for exclude in EXCLUDES:
                if item == exclude or item.endswith(exclude.replace("*", "")):
                    skip = True
                    break
            if skip:
                continue
            tar.add(item)
    
    proc.stdin.close()
    
    ret = proc.wait()
    if ret != 0:
        log("❌ Build failed!")
        sys.exit(1)
    
    log("✅ Build successful!")

def import_image():
    log("Step 2: Importing image into K3s containerd...")
    # Using node-debugger to execute k3s ctr import on the host
    cmd = [
        "kubectl", "exec", "-n", NAMESPACE, "node-debugger", "--",
        "chroot", "/host", "k3s", "ctr", "images", "import", "/tmp/mcp-prod.tar"
    ]
    run_command(cmd, shell=False)
    log("✅ Image imported!")

def update_deployment():
    log("Step 3: Updating deployment to use new image...")
    cmd = f"kubectl set image deployment/{DEPLOYMENT_NAME} mcp-unified={IMAGE_NAME} -n {NAMESPACE}"
    run_command(cmd)
    
    log("Step 4: Waiting for rollout...")
    cmd = f"kubectl rollout status deployment/{DEPLOYMENT_NAME} -n {NAMESPACE} --timeout=120s"
    run_command(cmd)
    log("✅ Deployment updated!")

def verify_health():
    log("Step 5: Verifying health...")
    time.sleep(5)
    try:
        import requests
        url = "http://192.168.0.30:30080/health"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                log(f"✅ Health Check PASSED: Version {data.get('version')}, Tools: {data.get('tools')}")
                return True
            else:
                log(f"❌ Health Check FAILED: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            log(f"❌ Health Check Error: {e}")
            return False
    except ImportError:
        log("requests module not found, skipping health verification")
        return True

def main():
    start_time = time.time()
    try:
        # Step 1: Build & Save
        stream_and_build()
        # Step 2: Import to K3s
        import_image()
        # Step 3: Deploy
        update_deployment()
        # Step 4: Verify
        verify_health()
        
        log(f"🚀 Production deployment completed in {time.time() - start_time:.2f}s")
    except KeyboardInterrupt:
        log("Deployment cancelled.")

if __name__ == "__main__":
    if not os.path.exists("deploy/docker"):
        log("Error: Run this script from the project root")
        sys.exit(1)
    main()
