#!/usr/bin/env python3
"""
Monitor MCP Build Progress on EdgeServer
Surveille le build Docker en cours
"""

import subprocess
import time
import sys

def check_build_status():
    """Vérifie le statut du build"""
    
    print("=" * 60)
    print("MCP Build Monitor - EdgeServer")
    print("=" * 60)
    print()
    
    # Check if build process is running
    cmd_ps = "ssh twister@192.168.0.30 \"ps aux | grep 'docker build' | grep -v grep\""
    
    try:
        result = subprocess.run(cmd_ps, shell=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            print("✅ Build process is RUNNING")
            print()
            print("Processes:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line[:100]}")
            print()
        else:
            print("⚠️  No build process found")
            print()
            
            # Check if image exists
            cmd_img = 'ssh twister@192.168.0.30 "sudo docker images twisterlab/mcp-unified:latest"'
            img_result = subprocess.run(cmd_img, shell=True, capture_output=True, text=True)
            
            if "twisterlab/mcp-unified" in img_result.stdout:
                print("🎉 BUILD COMPLETE! Image exists:")
                print(img_result.stdout)
                print()
                print("✅ Ready to deploy!")
                return "COMPLETE"
            else:
                print("❌ Build not running and no image found")
                print("   Check logs: ssh twister@192.168.0.30 'cat /tmp/mcp-build/build.log'")
                return "FAILED"
        
        # Check build log
        cmd_log = "ssh twister@192.168.0.30 \"tail -20 /tmp/mcp-build/build.log 2>/dev/null\""
        log_result = subprocess.run(cmd_log, shell=True, capture_output=True, text=True)
        
        if log_result.stdout.strip():
            print("📋 Last 20 lines of build log:")
            print("-" * 60)
            print(log_result.stdout)
            print("-" * 60)
        
        return "RUNNING"
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return "ERROR"

def main():
    """Main loop"""
    
    status = check_build_status()
    
    print()
    print("=" * 60)
    
    if status == "COMPLETE":
        print("🎉 BUILD SUCCESSFUL!")
        print()
        print("Next steps:")
        print("  1. Import to K3s:")
        print("     ssh twister@192.168.0.30 \\")
        print("       'sudo docker save twisterlab/mcp-unified:latest | \\")
        print("        sudo k3s ctr images import -'")
        print()
        print("  2. Deploy:")
        print("     kubectl scale deployment mcp-unified --replicas=1 -n twisterlab")
        
    elif status == "RUNNING":
        print("⏱️  Build is in progress...")
        print()
        print("💡 Check again in 5-10 minutes:")
        print("   python scripts/monitor_mcp_build.py")
        
    elif status == "FAILED":
        print("❌ Build failed or stopped")
        print()
        print("💡 Check full logs:")
        print("   ssh twister@192.168.0.30 'cat /tmp/mcp-build/build.log'")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
