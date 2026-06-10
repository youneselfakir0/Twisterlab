import asyncio
import time
import sys
import os
import random

# Add /app to sys.path if running in container
if '/app' not in sys.path:
    sys.path.insert(0, '/app')

try:
    from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
    AGENT_AVAILABLE = True
except ImportError:
    AGENT_AVAILABLE = False

async def run_injection():
    print("🚀 GÉNÉRATION DE FLUX DE MÉTRIQUES AGENT (60 secondes)...")
    
    if not AGENT_AVAILABLE:
        print("❌ Agent non disponible dans ce pod.")
        return

    agent = SentimentAnalyzerAgent()
    texts = [
        "TwisterLab is the best platform for AI!",
        "I love how fast the monitoring dashboard is.",
        "The system is down again, this is frustrating.",
        "Average day at the office.",
        "Excellent results on the last training run.",
        "The GPU temperature is rising too fast!",
        "Nice work on the MCP router optimization."
    ]

    for i in range(30):  # 30 iterations
        text = random.choice(texts)
        print(f"[{i+1}/30] Analysing: {text}")
        await agent.execute(text, context={"detailed": True})
        # Sleep for a bit to spread metrics
        await asyncio.sleep(2)
    
    print("\n✅ Flux terminé. Les graphiques devraient être bien visibles.")

if __name__ == "__main__":
    asyncio.run(run_injection())
