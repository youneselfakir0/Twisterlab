import subprocess
import os
import sys
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def run_ad_sync():
    """
    Triggers the PowerShell script to synchronize agents with Active Directory.
    Requires the ActiveDirectory module and appropriate permissions.
    """
    print(f"\n{BOLD}{CYAN}=== TwisterLab Active Directory Synchronization ==={RESET}")
    
    # Locate the powershell script
    project_root = Path(__file__).resolve().parents[3]
    script_path = project_root / "scripts" / "sync-agents-ad.ps1"
    
    if not script_path.exists():
        print(f"{RED}[ERROR] PowerShell sync script not found at {script_path}{RESET}")
        return

    print(f"{YELLOW}[INFO] Executing AD Synchronization...{RESET}")
    
    try:
        # Execute PowerShell
        process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.communicate()
        
        if process.returncode == 0:
            print(f"{GREEN}[OK] AD Synchronization process finished successfully.{RESET}")
        else:
            print(f"{RED}[ERROR] PowerShell script exited with code {process.returncode}{RESET}")
            
    except Exception as e:
        print(f"{RED}[ERROR] Failed to launch synchronization: {e}{RESET}")
    
    print("=" * 60 + "\n")

if __name__ == "__main__":
    import sys
    run_ad_sync()
