#!/usr/bin/env python3
"""
Build and deploy MCP Unified image to K3s cluster
"""
import subprocess
import sys
import os

def run_cmd(cmd, shell=True, check=True, capture_output=False):
    """Run a command and handle errors"""
    print(f"🔄 {cmd}")
    try:
        result = subprocess.run(cmd, shell=shell, check=check, capture_output=capture_output, text=True)
        if capture_output:
            return result.stdout.strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if capture_output and e.stderr:
            print(f"Error output: {e.stderr}")
        if not check:
            return None
        sys.exit(1)

def build_and_deploy():
    """Build MCP image and deploy to K3s"""
    
    print("\n🚀 Building MCP Unified Image for K3s\n")
    print("=" * 60)
    
    # Step 1: Build the image using Docker on EdgeServer via SSH
    print("\n📦 Step 1: Building Docker image on EdgeServer...")
    remote_build_dir = "/tmp/twisterlab-build"
    
    # Create build directory on remote
    run_cmd(f'ssh twister@192.168.0.30 "mkdir -p {remote_build_dir}"')
    
    # Copy necessary files
    print("\n📂 Step 2: Copying files to EdgeServer...")
    run_cmd(f'scp -r src twister@192.168.0.30:{remote_build_dir}/')
    run_cmd(f'scp requirements.txt twister@192.168.0.30:{remote_build_dir}/')
    run_cmd(f'scp deploy/docker/Dockerfile.mcp-unified twister@192.168.0.30:{remote_build_dir}/Dockerfile')
    
    # Build the image
    print("\n🔨 Step 3: Building Docker image (this may take a few minutes)...")
    run_cmd(f'ssh twister@192.168.0.30 "cd {remote_build_dir} && sudo docker build -t twisterlab/mcp-unified:latest -f Dockerfile ."')
    
    #Export and import to containerd
    print("\n💾 Step 4: Importing image to K3s containerd...")
    run_cmd(f'ssh twister@192.168.0.30 "sudo docker save twisterlab/mcp-unified:latest | sudo k3s ctr images import -"')
    
    # Verify import
    print("\n✅ Step 5: Verifying image import...")
    result = run_cmd(f'ssh twister@192.168.0.30 "sudo k3s crictl images | grep twisterlab/mcp-unified"', capture_output=True, check=False)
    if result:
        print(f"📋 Image found: {result}")
    else:
        print("⚠️ Warning: Could not verify image import")
    
    # Clean up build directory
    print("\n🧹 Step 6: Cleaning up temporary files...")
    run_cmd(f'ssh twister@192.168.0.30 "rm -rf {remote_build_dir}"')
    
    # Restart deployments
    print("\n🔄 Step 7: Restarting MCP deployments...")
    run_cmd("kubectl rollout restart deployment mcp-server -n default")
    run_cmd("kubectl rollout restart deployment mcp-unified -n twisterlab")
    run_cmd("kubectl rollout restart deployment mcp-unified -n twisterlab-dev")
    
    # Wait for rollouts
    print("\n⏳ Step 8: Waiting for deployments to be ready...")
    print("   • default/mcp-server...")
    run_cmd("kubectl rollout status deployment/mcp-server -n default --timeout=120s", check=False)
    print("   • twisterlab/mcp-unified...")
    run_cmd("kubectl rollout status deployment/mcp-unified -n twisterlab --timeout=120s", check=False)
    print("   • twisterlab-dev/mcp-unified...")
    run_cmd("kubectl rollout status deployment/mcp-unified -n twisterlab-dev --timeout=120s", check=False)
    
    print("\n" + "=" * 60)
    print("✅ MCP BUILD AND DEPLOYMENT COMPLETE!")
    print("=" * 60)
    print("\n📊 Check deployment status:")
    print("   kubectl get pods -n default -l app=mcp-server")
    print("   kubectl get pods -n twisterlab -l app=mcp-unified")
    print("   kubectl get pods -n twisterlab-dev -l app=mcp-unified")
    print("\n")

if __name__ == "__main__":
    try:
        build_and_deploy()
    except KeyboardInterrupt:
        print("\n\n⚠️ Build cancelled by user")
        sys.exit(1)
