import os
import sys
import time
import socket
import signal
import psutil
import subprocess
from pathlib import Path

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

PID_FILE = Path(".gateway.pid")
LOG_FILE = Path("gateway.log")


def is_port_in_use(port=8000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def get_running_process():
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text(encoding="utf-8").strip())
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            # Verify it's actually uvicorn/python
            if "python" in proc.name().lower() or "uvicorn" in proc.name().lower():
                return proc
    except Exception:
        pass
    return None


def start_gateway():
    print(f"{BOLD}{CYAN}🚀 Starting TwisterLab Gateway Daemon...{RESET}")
    
    proc = get_running_process()
    if proc:
        print(f"{YELLOW}Gateway already running (PID: {proc.pid}){RESET}")
        return

    if is_port_in_use(8000):
        print(f"{RED}Error: Port 8000 is already in use by another application.{RESET}")
        return

    # Start uvicorn as a detached process
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "twisterlab.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--workers", "1"
    ]
    
    log_fd = open(LOG_FILE, "a", encoding="utf-8")
    
    # Detach process depending on OS
    if sys.platform == "win32":
        DETACHED_PROCESS = 0x00000008
        process = subprocess.Popen(
            cmd,
            creationflags=DETACHED_PROCESS,
            stdout=log_fd,
            stderr=log_fd,
            close_fds=True
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=log_fd,
            stderr=log_fd,
            start_new_session=True,
            close_fds=True
        )

    # Write PID file
    PID_FILE.write_text(str(process.pid), encoding="utf-8")
    print(f"Gateway process spawned with PID {process.pid}.")
    
    # Wait and check if it came online
    print("Waiting for Gateway to initialize...")
    for _ in range(10):
        time.sleep(1.0)
        if is_port_in_use(8000):
            print(f"{GREEN}✓ Gateway is ONLINE and listening on port 8000.{RESET}")
            print(f"Logs are being written to {LOG_FILE.absolute()}")
            return
            
    print(f"{RED}⚠ Warning: Gateway was spawned but is not responding on port 8000 yet.{RESET}")
    print(f"Please inspect the logs at {LOG_FILE.absolute()}")


def stop_gateway():
    print(f"{BOLD}{YELLOW}🛑 Stopping TwisterLab Gateway Daemon...{RESET}")
    proc = get_running_process()
    if not proc:
        if is_port_in_use(8000):
            print(f"{YELLOW}Port 8000 in use but no local PID file found. You might need to stop the process manually.{RESET}")
        else:
            print("Gateway is not running.")
        if PID_FILE.exists():
            PID_FILE.unlink()
        return

    pid = proc.pid
    try:
        if sys.platform == "win32":
            proc.terminate()
        else:
            os.kill(pid, signal.SIGTERM)
            
        # Wait up to 5 seconds for exit
        for _ in range(5):
            if not psutil.pid_exists(pid):
                break
            time.sleep(1.0)
            
        if psutil.pid_exists(pid):
            print("Process did not exit. Forcing kill...")
            proc.kill()
            
        print(f"{GREEN}✓ Gateway (PID: {pid}) stopped successfully.{RESET}")
    except Exception as e:
        print(f"{RED}Error stopping process: {e}{RESET}")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()


def show_status():
    proc = get_running_process()
    print("\n" + "=" * 60)
    print(f"{BOLD}{CYAN}📊 TwisterLab Gateway Status{RESET}")
    print("=" * 60)
    
    if proc:
        try:
            cpu = proc.cpu_percent(interval=0.1)
            mem = proc.memory_info().rss / (1024 * 1024)  # MB
            print_status = f"{GREEN}ONLINE{RESET}"
            print(f"  Status       : {print_status}")
            print(f"  PID          : {proc.pid}")
            print(f"  CPU Usage    : {cpu:.1f}%")
            print(f"  Memory Usage : {mem:.1f} MB")
            print(f"  Port         : 8000")
            print(f"  Log File     : {LOG_FILE.absolute()}")
        except Exception as e:
            print(f"  Status       : {YELLOW}UNKNOWN (Process check failed: {e}){RESET}")
    else:
        if is_port_in_use(8000):
            print(f"  Status       : {YELLOW}PORT ACTIVE (Another service is using port 8000){RESET}")
        else:
            print(f"  Status       : {RED}OFFLINE{RESET}")
            
    print("=" * 60 + "\n")
