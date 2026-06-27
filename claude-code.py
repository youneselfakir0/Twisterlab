#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Claude Code + TwisterLab via Ollama API"""

import requests
import json
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:11434"
MODEL = "gemma4:latest"
REPO_PATH = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = f"""You are Claude Code, an expert AI assistant analyzing the TwisterLab codebase.

REPOSITORY: {REPO_PATH}
MODEL: gemma4:latest (Ollama)
ROLE: Senior code analyst for TwisterLab GENESIS PRIME

TwisterLab is a multi-agent AI platform with:
- FastAPI backend (src/twisterlab/api/)
- SQLAlchemy async database (src/twisterlab/database/)
- Agent registry (src/twisterlab/agents/)
- 13+ specialized agents
- Kubernetes deployment on EdgeServer

INSTRUCTIONS:
1. When asked, explore and analyze the TwisterLab codebase
2. Provide technical insights about architecture, patterns, and design
3. Help with code modifications, debugging, and feature implementation
4. Use Python/Bash tools when appropriate
5. Be concise but thorough

START: Begin by introducing yourself and asking what task the user wants help with."""

def check_ollama():
    """Verify Ollama is running."""
    try:
        response = requests.get(f"{BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def chat_with_claude(messages):
    """Send message to Claude via Ollama API."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "model": MODEL,
                "messages": messages,
                "stream": False,
            },
            timeout=60
        )
        if response.status_code == 200:
            return response.json()["message"]["content"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.Timeout:
        return "Timeout: Ollama took too long to respond"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    """Main interactive loop."""
    # Check Ollama
    print("\n" + "="*60)
    print("Claude Code + TwisterLab")
    print("="*60)
    print(f"\nChecking Ollama... ", end="", flush=True)
    
    if not check_ollama():
        print("FAILED")
        print("Error: Ollama is not running on localhost:11434")
        print("Launch in separate terminal: ollama serve")
        sys.exit(1)
    
    print("OK")
    print(f"Model: {MODEL}")
    print(f"Repository: {REPO_PATH}")
    print("\nStarting Claude Code session...")
    print("Type 'exit' to quit\n")
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    
    # Get initial response
    print("Claude: ", end="", flush=True)
    response = chat_with_claude(messages)
    print(response)
    print()
    
    messages.append({"role": "assistant", "content": response})
    
    # Interactive loop
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nClaude: Goodbye! Let me know if you need help with TwisterLab later.")
                break
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Get response
            print("\nClaude: ", end="", flush=True)
            response = chat_with_claude(messages)
            print(response)
            print()
            
            # Add assistant response
            messages.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            print("\n\nClaude: Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Trying again...\n")

if __name__ == "__main__":
    main()
