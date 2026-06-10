"""
Final Verification for TwisterLab Modernization (v3.8.2)
Tests:
1. Dynamic Discovery (Correct count, no hardcoded drift)
2. Service Layer wiring (Ticket classification)
3. Security Policy (SSRF blocking)
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parents[3]))

from twisterlab.api.services.agent_service import get_agent_service
from twisterlab.api.services.ticket_service import get_ticket_service
from twisterlab.api.services.security_policy import SecurityPolicy

async def main():
    print("--- TwisterLab Modernization v3.8.2 Final Verification ---")
    
    agent_service = get_agent_service()
    ticket_service = get_ticket_service()
    
    # 1. Test Discovery
    print("\n1. Testing Dynamic Discovery...")
    status = agent_service.get_fleet_status()
    print(f"Total Registered Agents: {status['total_registered']}")
    if status['total_registered'] >= 21:
        print("[SUCCESS] Discovery shows full fleet of 21+ agents.")
    else:
        print(f"[FAILURE] Expected 21+ agents, got {status['total_registered']}")
        
    # 2. Test Service Layer (Classification)
    print("\n2. Testing TicketService (Business Logic Extraction)...")
    res = await ticket_service.classify_ticket("My internet is very slow in the bedroom")
    if res.success:
        print(f"[SUCCESS] Ticket classified as '{res.data.get('category')}'")
    else:
        print(f"[FAILURE] Classification failed: {res.error}")
        
    # 3. Test Security Policy (SSRF)
    print("\n3. Testing SecurityPolicy (SSRF Protection)...")
    unsafe_url = "http://127.0.0.1:6379/config"
    safe_url = "https://www.google.com"
    
    if not SecurityPolicy.validate_url(unsafe_url):
        print(f"[SUCCESS] Blocked internal URL: {unsafe_url}")
    else:
        print(f"[FAILURE] Security Policy bypassed for internal URL!")
        
    if SecurityPolicy.validate_url(safe_url):
        print(f"[SUCCESS] Allowed external URL: {safe_url}")
    else:
        print(f"[FAILURE] Security Policy blocked a safe external URL.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
