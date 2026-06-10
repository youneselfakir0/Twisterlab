import json
from twisterlab.agents.registry import get_agent_registry

def main():
    registry = get_agent_registry()
    agents = registry.list_agents()
    print(json.dumps(agents))

if __name__ == "__main__":
    main()
