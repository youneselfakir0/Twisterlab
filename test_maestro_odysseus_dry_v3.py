
import asyncio
import logging
import os
import sys
import json

# Ajout du path src pour l'import de twisterlab
sys.path.append(os.path.join(os.getcwd(), "src"))

from twisterlab.agents.registry import get_agent_registry

logging.basicConfig(level=logging.INFO)

async def test_maestro_odysseus():
    registry = get_agent_registry()
    
    # Force instantiation of Odysseus to update capabilities
    print("🛠️ Pré-instanciation des agents critiques...")
    registry.get_agent("odysseus")
    registry.get_agent("maestro")
    
    maestro = registry.get_agent("maestro")
    
    # Liste des agents disponibles selon Maestro (après instanciation)
    print("\n🔍 Discovery: Agents et leurs capacités réelles")
    resp_agents = await maestro.handle_list_agents()
    if resp_agents.success:
        for agent in resp_agents.data.get("agents", []):
            if "odysseus" in agent['name']:
                print(f"  ⭐ {agent['name']}: {agent['description']}")
                print(f"     Capacités: {agent['capabilities']}")
    
    task = "Use the odysseus agent and its 'chat' capability to discuss gene sequence optimization."
    
    print(f"\n🚀 Lancement de la mission Maestro pour: {task}")
    
    # On utilise dry_run=True
    response = await maestro.handle_orchestrate(task=task, dry_run=True)
    
    if response.success:
        print("\n✅ Plan de Maestro généré avec succès!")
        data = response.data
        print(f"Mode: {data.get('mode')}")
        print(f"Pensée: {data.get('thought')}")
        
        plan = data.get("plan", {})
        print(f"Agents impliqués: {plan.get('agents')}")
        for step in plan.get("steps", []):
            print(f"  Step {step['order']}: {step['agent']} -> {step['capability']} ({step['purpose']})")
    else:
        print(f"\n❌ Échec de la planification: {response.error}")

if __name__ == "__main__":
    asyncio.run(test_maestro_odysseus())
