import sys
import argparse
import asyncio

# ANSI colors
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_logo():
    logo = f"""{CYAN}
  _____  __      __  _          _               _          _     
 |_   _| \ \    / / (_)  ___  | |_    ___   _ __  | |   __ _  | |__  
   | |    \ \/\/ /  | | / __| | __|  / _ \ | '__| | |  / _` | | '_ \ 
   | |     \  /\  /   | | \__ \ | |_  |  __/ | |    | | | (_| | | |_) |
   |_|      \/  \/    |_| |___/  \__|  \___| |_|    |_|  \__,_| |_.__/ 
{RESET}
               TwisterLab Unified Agent Gateway CLI
    """
    try:
        print(logo)
    except UnicodeEncodeError:
        print("\n=== TwisterLab Unified Agent Gateway CLI ===\n")


def main():
    parser = argparse.ArgumentParser(
        description="TwisterLab Unified Agent Gateway Command Line Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command")

    # Command: onboard
    subparsers.add_parser("onboard", help="Run the interactive onboarding wizard to configure TwisterLab")

    # Command: doctor
    subparsers.add_parser("doctor", help="Run diagnostic health checks on services and integrations")

    # Command: gateway
    gateway_parser = subparsers.add_parser("gateway", help="Manage the background API Gateway server")
    gateway_sub = gateway_parser.add_subparsers(dest="action")
    gateway_sub.add_parser("start", help="Start the gateway API server in the background")
    gateway_sub.add_parser("stop", help="Stop the background gateway server")
    gateway_sub.add_parser("status", help="Show the gateway server status (CPU, RAM, PID)")
    gateway_sub.add_parser("restart", help="Restart the gateway server")

    # Command: agent
    agent_parser = subparsers.add_parser("agent", help="List and run agents in the registry")
    agent_sub = agent_parser.add_subparsers(dest="action")
    agent_sub.add_parser("list", help="List all registered agents and their capabilities")
    
    agent_run = agent_sub.add_parser("run", help="Execute an agent task")
    agent_run.add_argument("agent_name", help="Name of the agent (e.g. maestro, trader, notion)")
    agent_run.add_argument("capability_name", nargs="?", default=None, help="Name of the capability to invoke (optional)")
    agent_run.add_argument("args_json", nargs="?", default=None, help="JSON arguments or string task for the agent (optional)")

    # Command: domain
    domain_parser = subparsers.add_parser("domain", help="Manage TwisterLab Active Directory integration")
    domain_sub = domain_parser.add_subparsers(dest="action")
    domain_sub.add_parser("sync", help="Synchronize AI agents as domain users in twisterlab.local")

    # Print logo if no arguments or help requested
    if len(sys.argv) == 1:
        print_logo()
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "onboard":
        from twisterlab.cli.onboard import run_onboard
        run_onboard()
        
    elif args.command == "doctor":
        from twisterlab.cli.doctor import run_doctor
        asyncio.run(run_doctor())
        
    elif args.command == "gateway":
        from twisterlab.cli.gateway import start_gateway, stop_gateway, show_status
        if args.action == "start":
            start_gateway()
        elif args.action == "stop":
            stop_gateway()
        elif args.action == "status":
            show_status()
        elif args.action == "restart":
            stop_gateway()
            start_gateway()
        else:
            gateway_parser.print_help()
            
    elif args.command == "agent":
        from twisterlab.cli.agent import run_list, run_agent
        if args.action == "list":
            run_list()
        elif args.action == "run":
            run_agent(args.agent_name, args.capability_name, args.args_json)
        else:
            agent_parser.print_help()
            
    elif args.command == "domain":
        from twisterlab.cli.domain import run_ad_sync
        if args.action == "sync":
            run_ad_sync()
        else:
            domain_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
