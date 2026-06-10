import sys
import argparse
import httpx
import json

BASE_URL = "http://192.168.0.30:30000"

def create_mission(name):
    print(f"⚡ Creating mission: {name}...")
    try:
        r = httpx.post(f"{BASE_URL}/api/dashboard/archive", json={"mission_id": name, "task": f"Mission {name} créée via CLI"})
        print(f"✅ Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

def delete_mission(name):
    print(f"🗑 Deleting mission: {name}...")
    try:
        r = httpx.post(f"{BASE_URL}/api/dashboard/history/delete", json={"mission_id": name})
        print(f"✅ Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
    except Exception as e:
        print(f"❌ Error: {e}")

def start_mission(name):
    print(f"🧠 Maestro starting mission: {name}...")
    try:
        # Trigger actual orchestration
        payload = {"arguments": {"task": name}}
        r = httpx.post(f"{BASE_URL}/api/tools/maestro_orchestrate", json=payload, timeout=60.0)
        data = r.json()
        if data.get("isError"):
            print(f"❌ Failed: {data.get('content',[{}])[0].get('text')}")
        else:
            text = data.get('content',[{}])[0].get('text')
            print(f"🏁 Result: {text}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="TwisterLab Mission Control CLI")
    subparsers = parser.add_subparsers(dest="command")

    # n8n
    n8n_p = subparsers.add_parser("n8n")
    n8n_sub = n8n_p.add_subparsers(dest="sub")
    
    n8n_create = n8n_sub.add_parser("create")
    n8n_create.add_argument("type", choices=["mission"])
    n8n_create.add_argument("--name", required=True)
    
    n8n_delete = n8n_sub.add_parser("delete")
    n8n_delete.add_argument("type", choices=["mission"])
    n8n_delete.add_argument("name")

    # Maestro
    mae_p = subparsers.add_parser("Maestro")
    mae_sub = mae_p.add_subparsers(dest="sub")
    
    mae_start = mae_sub.add_parser("start")
    mae_start.add_argument("type", choices=["mission"])
    mae_start.add_argument("name")

    # Shortcut for help if no args
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "n8n":
        if args.sub == "create":
            create_mission(args.name)
        elif args.sub == "delete":
            delete_mission(args.name)
    elif args.command == "Maestro":
        if args.sub == "start":
            start_mission(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
