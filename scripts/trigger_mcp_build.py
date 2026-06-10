#!/usr/bin/env python3
"""
Trigger GitHub Actions Workflow
Declenche le workflow MCP build via GitHub API
"""

import requests
import sys
import os
import time

# Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'youneselfakir0'
REPO_NAME = 'Twisterlab'
WORKFLOW_FILE = 'build-mcp.yml'
BRANCH = 'main'

def trigger_workflow():
    """Déclenche le workflow GitHub Actions"""
    
    if not GITHUB_TOKEN:
        print("❌ ERROR: GITHUB_TOKEN environment variable not set")
        print("   Export your GitHub PAT: export GITHUB_TOKEN=ghp_xxxxx")
        return False
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    data = {
        'ref': BRANCH
    }
    
    print(f"🔄 Triggering workflow: {WORKFLOW_FILE}")
    print(f"   Repository: {REPO_OWNER}/{REPO_NAME}")
    print(f"   Branch: {BRANCH}")
    print()
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 204:
            print("✅ Workflow triggered successfully!")
            print()
            print("📊 Check status at:")
            print(f"   https://github.com/{REPO_OWNER}/{REPO_NAME}/actions")
            print()
            print("⏱️  Build typically takes 3-5 minutes")
            print()
            
            # Wait and check runs
            time.sleep(5)
            check_recent_runs()
            return True
            
        else:
            print(f"❌ Failed to trigger workflow")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_recent_runs():
    """Vérifie les runs récents"""
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/runs"
    
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            runs = data.get('workflow_runs', [])
            
            if runs:
                latest = runs[0]
                print("📋 Latest Workflow Run:")
                print(f"   Status: {latest['status']}")
                print(f"   Conclusion: {latest.get('conclusion', 'in progress')}")
                print(f"   Run ID: {latest['id']}")
                print(f"   Created: {latest['created_at']}")
                print(f"   URL: {latest['html_url']}")
    except Exception as e:
        print(f"⚠️  Could not check runs: {e}")

def main():
    """Main function"""
    
    print("=" * 60)
    print("GitHub Actions Workflow Trigger")
    print("=" * 60)
    print()
    
    success = trigger_workflow()
    
    if success:
        print()
        print("🎉 Next steps:")
        print("   1. Wait for build to complete (~3-5 min)")
        print("   2. Deploy to K8s:")
        print("      kubectl set image deployment/mcp-server \\")
        print("        mcp-server=ghcr.io/youneselfakir0/twisterlab/mcp-unified:latest -n default")
        print("      kubectl scale deployment mcp-server --replicas=1 -n default")
        print()
        sys.exit(0)
    else:
        print()
        print("💡 Manual trigger:")
        print(f"   https://github.com/{REPO_OWNER}/{REPO_NAME}/actions")
        print()
        sys.exit(1)

if __name__ == '__main__':
    main()
