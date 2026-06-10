@echo off
set SSH_EXE=ssh.exe

if exist "C:\Windows\Sysnative\OpenSSH\ssh.exe" (
    set SSH_EXE="C:\Windows\Sysnative\OpenSSH\ssh.exe"
) else if exist "C:\Windows\System32\OpenSSH\ssh.exe" (
    set SSH_EXE="C:\Windows\System32\OpenSSH\ssh.exe"
)

%SSH_EXE% -o StrictHostKeyChecking=no -o PasswordAuthentication=no -o BatchMode=yes -q -T twister@192.168.0.30 "/home/twister/twisterlab-mcp/run_mcp.sh"
