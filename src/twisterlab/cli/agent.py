import json
import asyncio
from typing import Optional

# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def run_list():
    try:
        print("\n" + "=" * 80)
        print(f"{BOLD}{CYAN}🤖 TwisterLab Agent Registry{RESET}")
        print("=" * 80)
    except UnicodeEncodeError:
        print("\n" + "=" * 80)
        print(f"{BOLD}{CYAN}[Agents] TwisterLab Agent Registry{RESET}")
        print("=" * 80)
        
    from twisterlab.agents.registry_hybrid import agent_registry
    agent_registry.initialize_agents()
    
    agents = agent_registry.list_agents()
    
    # Print formatted table
    print(f"{BOLD}{'Agent Name':<20} | {'Status':<10} | {'Capabilities / Description':<45}{RESET}")
    print("-" * 80)
    for name, info in agents.items():
        agent_obj = agent_registry.get_agent(name)
        caps = []
        if agent_obj and hasattr(agent_obj, "get_capabilities"):
            caps = [c.name for c in agent_obj.get_capabilities()]
        caps_str = ", ".join(caps) if caps else info["description"]
        if len(caps_str) > 42:
            caps_str = caps_str[:39] + "..."
            
        status_color = GREEN if info["status"] == "active" else YELLOW
        status_str = f"{status_color}{info['status']}{RESET}"
        
        print(f"{info['name']:<20} | {status_str:<19} | {caps_str:<45}")
    print("=" * 80 + "\n")


async def execute_agent_task(agent_name: str, capability_name: Optional[str], args_json: Optional[str]):
    from twisterlab.agents.registry_hybrid import agent_registry
    from twisterlab.agents.base.adapter import AgentAdapter
    
    agent_registry.initialize_agents()
    agent = agent_registry.get_agent(agent_name)
    
    if not agent:
        print(f"{RED}Error: Agent '{agent_name}' not found in registry.{RESET}")
        return
        
    # Helper shortcut: if agent is maestro and capability is missing, default to orchestrate
    if agent_name.lower() == "maestro" and not capability_name:
        capability_name = "orchestrate"
        
    if not capability_name:
        # Try to find the first capability
        if hasattr(agent, "get_capabilities"):
            caps = agent.get_capabilities()
            if caps:
                capability_name = caps[0].name
                print(f"{YELLOW}Capability omitted. Defaulting to first capability: '{capability_name}'{RESET}")
                
    if not capability_name:
        print(f"{RED}Error: Could not determine capability to run for agent '{agent_name}'.{RESET}")
        return

    # Parse arguments
    params = {}
    if args_json:
        try:
            params = json.loads(args_json)
        except json.JSONDecodeError as je:
            # If it's not a JSON dict, check if the capability takes a single parameter like 'task' or 'text'
            # and map it.
            if hasattr(agent, "get_capabilities"):
                caps = agent.get_capabilities()
                target_cap = next((c for c in caps if c.name == capability_name), None)
                if target_cap and len(target_cap.params) == 1:
                    param_name = target_cap.params[0].name
                    params = {param_name: args_json}
                else:
                    # Default fallback
                    params = {"task": args_json, "text": args_json}
            else:
                params = {"task": args_json}
    else:
        # Prompt for interactive arguments if required parameters exist
        pass

    try:
        print(f"\n{BOLD}{CYAN}⚡ Executing agent command:{RESET}")
    except UnicodeEncodeError:
        print(f"\n{BOLD}{CYAN}[RUN] Executing agent command:{RESET}")
        
    print(f"   Agent      : {agent.name}")
    print(f"   Capability : {capability_name}")
    print(f"   Arguments  : {json.dumps(params)}")
    print("-" * 60)

    adapter = AgentAdapter(agent)
    try:
        response = await adapter.call(capability_name, **params)
        print("-" * 60)
        if response.success:
            try:
                print(f"{BOLD}{GREEN}✓ Execution Succeeded!{RESET}")
            except UnicodeEncodeError:
                print(f"{BOLD}{GREEN}[OK] Execution Succeeded!{RESET}")
            # Format and print output
            if "content" in response.data:
                print(f"\n{response.data['content']}")
            elif "response" in response.data:
                print(f"\n{response.data['response']}")
            else:
                print(json.dumps(response.data or response.content, indent=2))
        else:
            try:
                print(f"{BOLD}{RED}✗ Execution Failed.{RESET}")
            except UnicodeEncodeError:
                print(f"{BOLD}{RED}[FAILED] Execution Failed.{RESET}")
            print(f"Error Message : {response.error}")
            print(f"Error Code    : {response.error_code}")
    except Exception as e:
        print(f"{RED}Fatal execution error: {e}{RESET}")
    print("=" * 60 + "\n")


def run_agent(agent_name: str, capability_name: Optional[str], args_json: Optional[str]):
    asyncio.run(execute_agent_task(agent_name, capability_name, args_json))
