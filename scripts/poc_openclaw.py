import subprocess
import json

def ask_openclaw(message: str, session_id: str = "python_demo"):
    """
    Test simple d'interaction avec OpenClaw via sa CLI.
    L'agent va recevoir le message, potentiellement utiliser son navigateur interne,
    et nous retourner la réponse sous format JSON.
    """
    command = [
        "npx.cmd", "openclaw", "agent",
        "--session-id", session_id,
        "--message", message,
        "--json"
    ]
    
    print(f"[*] Envoi de la requête à OpenClaw...\n    Message: '{message}'")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Le CLI peut afficher quelques logs sur stderr avant le JSON sur stdout
        # On essaie de parser la dernière ligne (ou tout le flow)
        try:
            # On cherche le premier bloc JSON de la sortie standard
            output_str = result.stdout.strip()
            # on tente un parse direct
            parsed = json.loads(output_str)
            print("\n[+] Réponse de l'Agent IA :")
            if 'text' in parsed:
                print(f"-> {parsed['text']}")
            else:
                print(parsed)
                
            return parsed
            
        except json.JSONDecodeError:
            print("[?] Sortie brute (pas de JSON strict) :")
            print(result.stdout)
            return result.stdout
            
    except subprocess.CalledProcessError as e:
        print(f"[-] Erreur lors de l'exécution de la commande OpenClaw.")
        print(f"Exit code: {e.returncode}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")

if __name__ == "__main__":
    # Test d'une action "web" demandant l'utilisation du navigateur de l'agent
    test_prompt = "Utilise ton navigateur pour aller sur https://example.com et donne-moi le texte principal affiché (le header) ainsi que le lien."
    ask_openclaw(test_prompt)
