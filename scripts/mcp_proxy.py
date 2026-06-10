import subprocess
import sys
import threading
import os
import time

LOG_FILE = r'C:\Users\Administrator\Documents\twisterlab\mcp_proxy_debug.log'

def log(msg):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{time.time()}] {msg}\n")

log("=== STARTING PROXY ===")

try:
    p = subprocess.Popen(
        [
            r"C:\Windows\System32\OpenSSH\ssh.exe",
            "-i", r"C:\Users\Administrator\.ssh\id_rsa",
            "-o", "StrictHostKeyChecking=no",
            "-o", "PasswordAuthentication=no",
            "-o", "BatchMode=yes",
            "-q", "-T",
            "twister@192.168.0.30",
            "/home/twister/twisterlab-mcp/run_mcp.sh"
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    def read_stdout():
        try:
            while True:
                data = p.stdout.read(4096)
                if not data:
                    break
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
                with open(LOG_FILE, 'ab') as f:
                    f.write(data)
        except Exception as e:
            log(f"STDOUT ERR: {e}")

    def read_stderr():
        try:
            while True:
                data = p.stderr.read(4096)
                if not data:
                    break
                sys.stderr.buffer.write(data)
                sys.stderr.buffer.flush()
                with open(LOG_FILE + ".err", 'ab') as f:
                    f.write(data)
        except Exception as e:
            log(f"STDERR ERR: {e}")

    def read_stdin():
        try:
            while True:
                data = sys.stdin.buffer.read(4096)
                if not data:
                    break
                p.stdin.write(data)
                p.stdin.flush()
                with open(LOG_FILE + ".in", 'ab') as f:
                    f.write(data)
        except Exception as e:
            log(f"STDIN ERR: {e}")

    t1 = threading.Thread(target=read_stdout, daemon=True)
    t2 = threading.Thread(target=read_stderr, daemon=True)
    t3 = threading.Thread(target=read_stdin, daemon=True)

    t1.start()
    t2.start()
    t3.start()

    rc = p.wait()
    log(f"SSH exited with {rc}")
    
    # allow threads some time to finish
    time.sleep(1)

except Exception as e:
    log(f"FATAL: {e}")

log("=== ENDING PROXY ===")
