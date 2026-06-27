from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
import json
from pathlib import Path
from typing import Optional

app = FastAPI(title="Ollama Tools Server for TwisterLab")

# ============ MODELS ============
class CommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None

class FileReadRequest(BaseModel):
    path: str
    lines: int = 100

class FileWriteRequest(BaseModel):
    path: str
    content: str

class KubernetesRequest(BaseModel):
    command: str

# ============ UTILITY FUNCTIONS ============
def validate_command(cmd: str) -> bool:
    """Vérifier que la commande est safe"""
    dangerous = ['rm -rf', 'mkfs', 'dd if=', 'sudo reboot', '>>', '| rm']
    if any(d in cmd.lower() for d in dangerous):
        return False
    return True

def get_default_cwd():
    """Retourner le répertoire par défaut TwisterLab"""
    return r"C:\Users\Administrator\Documents\twisterlab"

# ============ TOOLS ============

@app.post("/tools/execute_shell")
async def execute_shell(req: CommandRequest):
    """Exécute une commande shell PowerShell ou cmd"""
    if not validate_command(req.command):
        return {"success": False, "error": "Command not allowed (security restriction)"}
    
    cwd = req.cwd or get_default_cwd()
    
    try:
        result = subprocess.run(
            req.command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[:3000],
            "stderr": result.stderr[:1000],
            "returncode": result.returncode,
            "cwd": cwd
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out (>30s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tools/read_file")
async def read_file(req: FileReadRequest):
    """Lit un fichier (dernières N lignes)"""
    try:
        path = Path(req.path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {req.path}"}
        
        with open(path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            content = ''.join(all_lines[-req.lines:])
        
        return {
            "success": True,
            "content": content,
            "total_lines": len(all_lines),
            "returned_lines": len(all_lines[-req.lines:])
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tools/write_file")
async def write_file(req: FileWriteRequest):
    """Écrit dans un fichier (crée les répertoires parents)"""
    try:
        path = Path(req.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(req.content)
        return {
            "success": True,
            "path": str(path),
            "size": len(req.content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tools/list_directory")
async def list_dir(path: Optional[str] = None):
    """Liste un répertoire"""
    if not path:
        path = get_default_cwd()
    
    try:
        items = []
        for item in Path(path).iterdir():
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        return {
            "success": True,
            "path": str(path),
            "items": sorted(items, key=lambda x: (x['type'] != 'dir', x['name']))
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tools/kubernetes")
async def kubectl_command(req: KubernetesRequest):
    """Exécute une commande kubectl sur EdgeServer"""
    allowed_verbs = ["get", "describe", "logs", "apply", "delete", "exec"]
    
    if not any(verb in req.command for verb in allowed_verbs):
        return {
            "success": False,
            "error": f"Command not allowed. Allowed verbs: {', '.join(allowed_verbs)}"
        }
    
    try:
        # Utilise kubectl avec le namespace twisterlab par défaut
        cmd = f"kubectl -n twisterlab {req.command}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        return {
            "success": result.returncode == 0,
            "command": cmd,
            "output": result.stdout[:4000],
            "error": result.stderr[:1000] if result.stderr else None
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "kubectl command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/tools/available")
async def list_tools():
    """Liste tous les outils disponibles"""
    return {
        "tools": [
            {
                "name": "execute_shell",
                "description": "Exécute une commande shell (cmd/PowerShell)",
                "params": {
                    "command": "str (required) - La commande à exécuter",
                    "cwd": "str (optional) - Répertoire de travail"
                }
            },
            {
                "name": "read_file",
                "description": "Lit un fichier",
                "params": {
                    "path": "str (required) - Chemin du fichier",
                    "lines": "int (optional, default=100) - Nombre de dernières lignes"
                }
            },
            {
                "name": "write_file",
                "description": "Écrit ou crée un fichier",
                "params": {
                    "path": "str (required) - Chemin du fichier",
                    "content": "str (required) - Contenu à écrire"
                }
            },
            {
                "name": "list_directory",
                "description": "Liste les fichiers/répertoires",
                "params": {
                    "path": "str (optional) - Répertoire à lister"
                }
            },
            {
                "name": "kubernetes",
                "description": "Exécute une commande kubectl sur EdgeServer",
                "params": {
                    "command": "str - Commande kubectl (sans 'kubectl -n twisterlab')"
                }
            }
        ],
        "default_cwd": get_default_cwd(),
        "security": "Commands with rm, mkfs, dd are blocked"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Ollama Tools Server",
        "version": "1.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Ollama Tools Server on http://0.0.0.0:8001")
    print("📚 Available tools: http://localhost:8001/tools/available")
    uvicorn.run(app, host="0.0.0.0", port=8001)