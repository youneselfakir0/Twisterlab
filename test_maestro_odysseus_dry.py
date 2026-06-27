
import asyncio
import logging
import os
import sys

# Ajout du path src pour l'import de twisterlab
sys.path.append(os.path.join(os.getcwd(), "src"))

from twisterlab.agents.registry import get_agent_registry

logging.basicConfig(level=logging.INFO)

async def test_maestro_odysseus():
    registry = get_agent_registry()
    maestro = registry.get_agent("maestro")
    
    if not maestro:
        print("❌ Agent Maestro non trouvé!")
        return

    # On s'assure que l'agent Odysseus est enregistré
    odysseus = registry.get_agent("odysseus")
    if not odysseus:
        print("❌ Agent Odysseus non trouvé dans le registre!")
    else:
        print(f"✅ Agent Odysseus trouvé. URL: {odysseus._base_url}")

    task = "Peux-tu demander à Odysseus d'optimiser cette séquence ADN: ATGCATGC ?"
    
    print(f"\n🚀 Lancement de la mission Maestro pour: {task}")
    
    # On utilise dry_run=True pour voir le plan sans exécution réelle
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
