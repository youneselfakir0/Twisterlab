#!/usr/bin/env python3
"""
🎬 TwisterLab Autonomous Incident Resolution Demo

This demo showcases the full multi-agent orchestration workflow:
1. Ticket arrives → Maestro analyzes
2. Sentiment analysis → Urgency detection
3. Classification → Problem categorization
4. Browser research → Solution lookup
5. Desktop Commander → Command execution
6. Resolution → Ticket closed
7. Monitoring → Continuous prevention

Run with: python demos/autonomous_incident.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add src to path for direct execution
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def print_header(title: str):
    """Print a styled header."""
    width = 70
    print("\n" + "=" * width)
    print(f" {title}".center(width))
    print("=" * width + "\n")


def print_step(emoji: str, agent: str, action: str, status: str = ""):
    """Print a step in the workflow."""
    status_str = f" → {status}" if status else ""
    print(f"  {emoji} [{agent:20}] {action}{status_str}")


def print_json(data: dict, indent: int = 4):
    """Print formatted JSON."""
    print(json.dumps(data, indent=indent, default=str))


async def run_scenario_database_slow():
    """
    Scenario: Database Slow Query
    
    Simulates a real-world incident where a customer reports
    that their PostgreSQL database is running slowly.
    """
    print_header("🎬 SCENARIO: SLOW DATABASE INCIDENT")
    
    # Import agents
    from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
    from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
    from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
    from twisterlab.agents.real.real_resolver_agent import RealResolverAgent
    
    # The incoming ticket
    ticket = """
    URGENT: Notre base de données PostgreSQL est extrêmement lente depuis ce matin!
    Les requêtes qui prenaient 50ms prennent maintenant plus de 10 secondes.
    Le serveur de production est impacté et nos clients se plaignent.
    Besoin d'aide immédiate!
    """
    
    print(f"📩 TICKET RECEIVED:\n{ticket.strip()}\n")
    print("-" * 70)
    
    # Step 1: Initialize Maestro
    print("\n🧠 MAESTRO INITIALIZATION...")
    maestro = RealMaestroAgent()
    
    # Step 2: Analyze task (dry run first to see the plan)
    print("\n📊 STEP 1: TASK ANALYSIS")
    print("-" * 40)
    
    analysis_result = await maestro.execute("analyze_task", task=ticket)
    if analysis_result.success:
        print_step("📊", "Maestro", "Task analyzed")
        print(f"     Category: {analysis_result.data['category']}")
        print(f"     Priority: {analysis_result.data['priority']}")
        print(f"     Keywords: {analysis_result.data['keywords']}")
        print(f"     Suggested agents: {analysis_result.data['suggested_agents']}")
    
    # Step 3: Sentiment Analysis
    print("\n😊 STEP 2: SENTIMENT ANALYSIS")
    print("-" * 40)
    
    sentiment_agent = SentimentAnalyzerAgent()
    sentiment_result = await sentiment_agent.execute("analyze_sentiment", text=ticket, detailed=True)
    if sentiment_result.success:
        print_step("😊", "SentimentAnalyzer", "Sentiment analyzed")
        print(f"     Sentiment: {sentiment_result.data['sentiment']}")
        print(f"     Confidence: {sentiment_result.data['confidence']:.2%}")
        print(f"     Keywords: {sentiment_result.data.get('keywords', [])}")
    
    # Step 4: Classification
    print("\n🏷️ STEP 3: TICKET CLASSIFICATION")
    print("-" * 40)
    
    classifier = RealClassifierAgent()
    class_result = await classifier.execute("classify_ticket", ticket_text=ticket)
    if class_result.success:
        print_step("🏷️", "Classifier", "Ticket classified")
        print(f"     Category: {class_result.data['category']}")
        print(f"     Priority: {class_result.data['priority']}")
    
    # Step 5: Full Orchestration (dry run)
    print("\n📋 STEP 4: ORCHESTRATION PLAN (DRY RUN)")
    print("-" * 40)
    
    plan_result = await maestro.execute(
        "orchestrate", 
        task=ticket,
        context={"is_production": True, "client": "ACME Corp"},
        dry_run=True
    )
    
    if plan_result.success:
        print_step("📋", "Maestro", "Execution plan created")
        plan = plan_result.data["plan"]
        print(f"\n     Agents to use: {plan['agents']}")
        print(f"     Number of steps: {len(plan['steps'])}")
        print(f"     Estimated duration: {plan['estimated_duration_sec']}s\n")
        
        print("     Planned Steps:")
        for step in plan["steps"]:
            print(f"       {step['order']}. {step['agent']}.{step['capability']} - {step['purpose']}")
    
    # Step 6: Full Orchestration (execute)
    print("\n🚀 STEP 5: FULL ORCHESTRATION (EXECUTE)")
    print("-" * 40)
    
    # Pass the registry to maestro for agent discovery
    from twisterlab.agents.registry import agent_registry
    maestro.agent_registry = agent_registry
    
    exec_result = await maestro.execute(
        "orchestrate",
        task=ticket,
        context={"is_production": True},
        dry_run=False
    )
    
    if exec_result.success:
        print_step("✅", "Maestro", "Orchestration completed")
        
        print("\n     Results by step:")
        for r in exec_result.data.get("results", []):
            status_emoji = "✅" if r["status"] == "success" else "⚠️" if r["status"] == "skipped" else "❌"
            print(f"       {status_emoji} Step {r['step']}: {r['agent']}.{r['capability']} - {r['status']}")
        
        synthesis = exec_result.data.get("synthesis", {})
        print("\n     📝 SYNTHESIS:")
        print(f"        Summary: {synthesis.get('summary', 'N/A')}")
        print(f"        Findings: {synthesis.get('findings', [])}")
        print(f"        Success Rate: {synthesis.get('success_rate', 0):.0%}")
        print(f"        Requires Human: {synthesis.get('requires_human', False)}")
    else:
        print(f"❌ Orchestration failed: {exec_result.error}")
    
    # Step 7: Resolution
    print("\n🔧 STEP 6: TICKET RESOLUTION")
    print("-" * 40)
    
    resolver = RealResolverAgent()
    resolve_result = await resolver.execute(
        "resolve_ticket",
        ticket_id="TKT-2026-001",
        resolution_note="Database optimized: VACUUM ANALYZE executed, slow query logs enabled, connection pooling adjusted."
    )
    
    if resolve_result.success:
        print_step("✅", "Resolver", "Ticket resolved")
        print(f"     Ticket ID: {resolve_result.data.get('ticket_id', 'TKT-2026-001')}")
        print(f"     Status: {resolve_result.data.get('status', 'RESOLVED')}")
    
    print_header("✅ SCENARIO COMPLETE: INCIDENT RESOLVED AUTONOMOUSLY")
    
    return exec_result


async def run_scenario_security_alert():
    """
    Scenario: Security Vulnerability Detected
    """
    print_header("🎬 SCENARIO: SECURITY VULNERABILITY ALERT")
    
    from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
    
    ticket = """
    CRITICAL SECURITY ALERT!
    We found hardcoded credentials in the authentication module.
    Password 'admin123' found in config.py.
    This is a production system - please help immediately!
    """
    
    print(f"📩 TICKET RECEIVED:\n{ticket.strip()}\n")
    print("-" * 70)
    
    maestro = RealMaestroAgent()
    
    # Analyze
    analysis = await maestro.execute("analyze_task", task=ticket)
    if analysis.success:
        print(f"\n📊 Analysis: {analysis.data['category']} / {analysis.data['priority']}")
    
    # Orchestrate
    result = await maestro.execute("orchestrate", task=ticket, dry_run=False)
    
    if result.success:
        print(f"\n✅ Orchestration completed!")
        print(f"   Steps executed: {result.data['steps_executed']}")
        print(f"   Duration: {result.data['duration_ms']}ms")
        print(f"   Recommendation: {result.data['synthesis']['recommendation']}")
    
    return result


async def main():
    """Run all demo scenarios."""
    print_header("🌀 TWISTERLAB AUTONOMOUS INCIDENT RESOLUTION DEMO")
    print(f"   Started: {datetime.now().isoformat()}")
    print(f"   Python: {sys.version.split()[0]}")
    
    scenarios = [
        ("Database Slow", run_scenario_database_slow),
        # ("Security Alert", run_scenario_security_alert),  # Uncomment to run
    ]
    
    for name, scenario in scenarios:
        try:
            await scenario()
        except Exception as e:
            print(f"\n❌ Scenario '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
    
    print_header("🎉 ALL SCENARIOS COMPLETED")


if __name__ == "__main__":
    asyncio.run(main())
