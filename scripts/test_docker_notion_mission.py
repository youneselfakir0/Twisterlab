import asyncio
import os
import json
import requests
from dotenv import load_dotenv

# Force UTF-8 encoding for Windows
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

async def run_docker_mission():
    print("🚀 Démarrage de la mission : Recherche Docker v30 & Fiche Notion")
    
    # On importe les agents localement pour le test
    from twisterlab.agents.registry import agent_registry
    from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
    from twisterlab.agents.real.real_notion_agent import RealNotionAgent
    from twisterlab.agents.real.browser_agent import RealBrowserAgent
    
    # 1. Vérification du Registry
    maestro = agent_registry.get_agent("maestro")
    notion = agent_registry.get_agent("notion")
    browser = agent_registry.get_agent("browser")
    
    if not maestro or not notion or not browser:
        print("❌ Erreur : Agents manquants dans le registry")
        return

    task = "Fais une recherche sur les nouveautés de Docker v30 et crée une fiche technique détaillée dans Notion. Inclus les fonctionnalités clés, les changements cassants et les améliorations de performance."
    
    print(f"🧠 Orchestration Maestro pour : {task[:50]}...")
    
    # L'orchestration va appeler le browser puis le notion agent
    result = await maestro.execute("orchestrate", task=task)
    
    if result.success:
        print("✅ Mission terminée avec succès !")
        print("\n--- SYNTHÈSE MAESTRO ---")
        print(result.data.get("synthesis", "Aucune synthèse"))
        
        # On va chercher l'URL Notion dans les logs si possible
        # Dans log_mission, on a l'URL de la page créée
        print("\n--- DÉTAILS NOTION ---")
        if "notion_report_url" in result.data:
            print(f"📄 Page créée : {result.data['notion_report_url']}")
        else:
            print("💡 La fiche a été créée dans ta base Notion 'TwisterLab — Missions'")
    else:
        print(f"❌ Échec de la mission : {result.error}")

if __name__ == "__main__":
    asyncio.run(run_docker_mission())
