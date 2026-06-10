import asyncio
import io
import os
import sys
from datetime import datetime

# Force UTF-8 for Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from twisterlab.agents.real.real_notion_agent import RealNotionAgent
from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
from twisterlab.agents.registry import agent_registry

async def run_complete_test():
    print("--- DEBUT DU TEST COMPLET TWISTERLAB ---")
    
    # 1. Vérification des variables d'env
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DEFAULT_DATABASE_ID")
    
    if not token or not db_id:
        print("❌ Erreur: NOTION_TOKEN ou NOTION_DEFAULT_DATABASE_ID manquant dans l'env.")
        return

    print(f"OK: Configuration trouvee (Token: {token[:8]}...)")

    # 2. Test Direct NotionAgent
    print("\n[Etape 1] Test direct du RealNotionAgent...")
    notion = RealNotionAgent()
    test_title = f"Test Complet - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    test_content = """# Rapport de Test Complet
Ce rapport a ete genere par le script de validation TwisterLab.

## Details
- Agent : RealNotionAgent
- Statut : En cours de validation
- Format : Markdown supporte

## Liste de controle
- [x] Connexion API
- [x] Parsing Markdown
- [x] Creation de blocs
"""
    
    res = await notion.handle_create_page(title=test_title, content=test_content)
    if res.success:
        print(f"OK: Page Notion creee avec succes ! URL: {res.data.get('url')}")
    else:
        print(f"ERREUR: Echec creation page Notion: {res.error}")
        return

    # 3. Test Orchestration Maestro
    print("\n[Etape 2] Test d'orchestration via Maestro...")
    maestro = agent_registry.get_agent("maestro")
    
    task = "Verifier la sante du systeme et documenter dans Notion (Test de validation v3.6.0)"
    print(f"Lancement de la mission: '{task}'")
    
    # On utilise handle_orchestrate qui fait tout de A à Z
    m_res = await maestro.handle_orchestrate(task=task)
    
    if m_res.success:
        data = m_res.data
        print(f"OK: Mission terminee: {data.get('status')}")
        print(f"Mission ID: {data.get('mission_id')}")
        print(f"Notion Logged: {data.get('notion_logged')}")
        print(f"Agents utilises: {', '.join(data.get('agents_used', []))}")
    else:
        print(f"ERREUR: Echec mission Maestro: {m_res.error}")

    print("\n--- FIN DU TEST COMPLET ---")


if __name__ == "__main__":
    asyncio.run(run_complete_test())
