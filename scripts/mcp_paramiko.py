import sys
import json
import logging
import paramiko
import threading
import traceback
import signal
import time
import os
import msvcrt

logging.basicConfig(filename=r'C:\Users\Administrator\Documents\twisterlab\mcp_paramiko.log', level=logging.DEBUG)

logging.info("Starting text-based paramiko proxy")

HOST = "192.168.0.30"
PORT = 22
USER = "twister"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        key_path = r"C:\Users\Administrator\.ssh\id_rsa"
        try:
            key = paramiko.RSAKey.from_private_key_file(key_path)
            logging.info(f"Loaded key from {key_path}")
        except Exception as e:
            logging.error(f"Failed to load specific key: {e}")
            sys.exit(1)

        client.connect(hostname=HOST, port=PORT, username=USER, pkey=key, timeout=10)
        logging.info("Connected to SSH")
        
        # Setup reverse port forwarding: remote 9092 -> local 9091
        transport = client.get_transport()
        try:
            transport.request_port_forward('', 9092)
            
            def reverse_forward_handler():
                while running:
                    try:
                        chan = transport.accept(1.0)
                        if chan is None:
                            continue
                        
                        import socket
                        sock = socket.socket()
                        try:
                            sock.connect(('127.0.0.1', 9091))
                        except Exception as e:
                            logging.error(f"Reverse forward connect failed: {e}")
                            chan.close()
                            continue
                            
                        def forward_traffic(source, dest, name):
                            try:
                                while True:
                                    data = source.recv(1024)
                                    if not data:
                                        break
                                    if hasattr(dest, 'sendall'):
                                        dest.sendall(data)
                                    else:
                                        dest.send(data)
                            except:
                                pass
                            finally:
                                try: source.close()
                                except: pass
                                try: dest.close()
                                except: pass
                                
                        threading.Thread(target=forward_traffic, args=(chan, sock, 'R->L'), daemon=True).start()
                        threading.Thread(target=forward_traffic, args=(sock, chan, 'L->R'), daemon=True).start()
                        
                    except Exception as e:
                        if running:
                            logging.error(f"Forward handler error: {e}")
                            
            threading.Thread(target=reverse_forward_handler, daemon=True).start()
            logging.info("Reverse port forwarding established (remote 9092 -> local 127.0.0.1:9091)")
        except Exception as e:
            logging.error(f"Could not establish reverse port forward: {e}")
        
        channel = client.get_transport().open_session()
        channel.exec_command("/home/twister/twisterlab-mcp/run_mcp.sh")
        logging.info("Executed run_mcp.sh via channel")
        
        # Disable python stdout buffering globally using text format
        running = True
        
        def read_stdout():
            try:
                while running and not channel.closed:
                    data = channel.recv(8192)
                    if not data:
                        break
                    sys.stdout.write(data.decode('utf-8', errors='replace'))
                    sys.stdout.flush()
            except Exception as e:
                logging.error(f"Stdout error: {e}")

        def read_stderr():
            try:
                while running and not channel.closed:
                    data = channel.recv_stderr(8192)
                    if not data:
                        break
                    logging.info(f"STDERR FROM REMOTE: {data.decode('utf-8', errors='replace')}")
            except Exception as e:
                logging.error(f"Stderr error: {e}")
                
        def read_stdin():
            try:
                while running and not channel.closed:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    channel.sendall(line.encode('utf-8'))
            except Exception as e:
                logging.error(f"Stdin error: {e}")

        t1 = threading.Thread(target=read_stdout, daemon=True)
        t2 = threading.Thread(target=read_stderr, daemon=True)
        t3 = threading.Thread(target=read_stdin, daemon=True)

        t1.start()
        t2.start()
        t3.start()

        while not channel.exit_status_ready():
            time.sleep(0.1)

        rc = channel.recv_exit_status()
        logging.info(f"Remote process exited with: {rc}")

    except Exception as e:
        logging.error(f"Paramiko proxy error: {e}\n{traceback.format_exc()}")
    finally:
        running = False
        client.close()
        logging.info("Proxy stopped")

if __name__ == "__main__":
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    main()
