"""
Claude Code Integration with Ollama Tools Server
Permet à un modèle Ollama d'utiliser les outils disponibles
"""

import requests
import json
import re
import time
from typing import Dict, Any, Optional

class OllamaToolsClient:
    """Client pour intégrer les outils du serveur FastAPI avec Ollama"""
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        tools_server: str = "http://localhost:8001",
        model: str = "qwen2.5-coder:7b"
    ):
        self.ollama_host = ollama_host
        self.tools_server = tools_server
        self.model = model
        self.system_prompt = self._load_system_prompt()
        
    def _load_system_prompt(self) -> str:
        """Charge le system prompt depuis le fichier"""
        try:
            with open('ollama_system_prompt.txt', 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "You are Claude Code, an expert code analysis agent for TwisterLab."
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Récupère la liste des outils disponibles"""
        try:
            response = requests.get(f"{self.tools_server}/tools/available")
            return response.json()
        except Exception as e:
            print(f"[ERROR] Failed to get tools: {e}")
            return {}
    
    def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un outil sur le serveur"""
        try:
            response = requests.post(
                f"{self.tools_server}/tools/{tool_name}",
                json=params,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def call_ollama_with_tools(self, prompt: str, verbose: bool = True) -> Dict[str, Any]:
        """
        Appelle Ollama avec support des outils
        Réponse: {"response": texte, "tool_calls": [résultats]}
        """
        
        full_prompt = f"{self.system_prompt}\n\n### USER REQUEST ###\n{prompt}"
        
        if verbose:
            print(f"\n[OLLAMA] Calling {self.model}...")
            print(f"[OLLAMA] Prompt length: {len(full_prompt)} chars")
        
        try:
            # Appel à Ollama
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=300
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Ollama error: {response.status_code}",
                    "response": None,
                    "tool_calls": []
                }
            
            response_text = response.json()['response']
            
            if verbose:
                print(f"[OLLAMA] Response received ({len(response_text)} chars)")
            
            # Parser les [TOOL_CALL] ... [/TOOL_CALL]
            tool_calls = re.findall(
                r'\[TOOL_CALL\](.*?)\[/TOOL_CALL\]',
                response_text,
                re.DOTALL
            )
            
            tool_results = []
            
            for i, call_json in enumerate(tool_calls):
                try:
                    call = json.loads(call_json)
                    tool = call['tool']
                    params = call['params']
                    
                    if verbose:
                        print(f"\n[TOOL] Executing: {tool}")
                        print(f"       Params: {params}")
                    
                    # Exécuter le tool
                    result = self.execute_tool(tool, params)
                    
                    if verbose:
                        status = "✓" if result.get('success') else "✗"
                        print(f"       Result: {status} {result}")
                    
                    tool_results.append({
                        "tool": tool,
                        "params": params,
                        "result": result
                    })
                    
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Invalid JSON in tool call {i}: {e}")
                    tool_results.append({
                        "tool": "unknown",
                        "error": "Invalid JSON"
                    })
            
            return {
                "success": True,
                "response": response_text,
                "tool_calls": tool_results
            }
            
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to Ollama at {self.ollama_host}",
                "response": None,
                "tool_calls": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None,
                "tool_calls": []
            }
    
    def interactive_session(self):
        """Lance une session interactive avec le modèle"""
        print("\n" + "="*60)
        print("  Claude Code + Ollama Tools Server (Interactive Mode)")
        print("="*60)
        print(f"  Model: {self.model}")
        print(f"  Ollama: {self.ollama_host}")
        print(f"  Tools Server: {self.tools_server}")
        print("  Type 'tools' to list available tools")
        print("  Type 'exit' to quit")
        print("="*60 + "\n")
        
        # Vérifier la santé
        try:
            requests.get(f"{self.tools_server}/health", timeout=5)
            print("✓ Tools server is healthy\n")
        except:
            print("✗ WARNING: Tools server not responding\n")
        
        while True:
            try:
                prompt = input("\n[INPUT] Your request: ").strip()
                
                if not prompt:
                    continue
                
                if prompt.lower() == 'exit':
                    print("\nGoodbye!")
                    break
                
                if prompt.lower() == 'tools':
                    tools = self.get_available_tools()
                    print("\n[TOOLS] Available:")
                    for tool in tools.get('tools', []):
                        print(f"  - {tool['name']}: {tool['description']}")
                    continue
                
                # Appeler Ollama
                result = self.call_ollama_with_tools(prompt, verbose=True)
                
                if result['success']:
                    print(f"\n[RESPONSE]\n{result['response']}")
                    
                    if result['tool_calls']:
                        print(f"\n[TOOLS EXECUTED] {len(result['tool_calls'])} tool(s)")
                else:
                    print(f"\n[ERROR] {result['error']}")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")

# ============ MAIN ============

if __name__ == "__main__":
    import sys
    
    # Configuration
    ollama_host = "http://localhost:11434"  # À adapter si Ollama est ailleurs
    tools_server = "http://localhost:8001"
    model = "qwen2.5-coder:7b"  # ou "deepseek-r1:latest"
    
    client = OllamaToolsClient(
        ollama_host=ollama_host,
        tools_server=tools_server,
        model=model
    )
    
    if len(sys.argv) > 1:
        # Mode: argument passé en ligne de commande
        prompt = " ".join(sys.argv[1:])
        result = client.call_ollama_with_tools(prompt, verbose=True)
        print(f"\n{result['response']}")
    else:
        # Mode: session interactive
        client.interactive_session()