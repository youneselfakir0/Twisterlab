#!/usr/bin/env python3
"""
MCP Orchestrator Agent - Remplace le workflow supervisor_dispatcher de N8N
Gère l'orchestration intelligente des tâches via analyse LLM
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPOrchestratorAgent:
    def __init__(self):
        self.tasks = {}
        self.agents = {
            'campaign': 'http://mcp_campaign_agent:8081',
            'monitoring': 'http://mcp_monitoring_agent:8082'
        }

    async def analyze_task(self, task_data):
        """Analyse la tâche via LLM pour déterminer l'agent approprié"""
        # Simulation d'analyse LLM - en production, intégrer un vrai LLM
        task_type = task_data.get('type', 'unknown')

        if 'campaign' in task_type.lower() or 'marketing' in task_type.lower():
            return 'campaign'
        elif 'monitor' in task_type.lower() or 'health' in task_type.lower():
            return 'monitoring'
        else:
            return 'orchestrator'

    async def route_task(self, request):
        """Route une tâche vers l'agent approprié"""
        try:
            task_data = await request.json()
            logger.info(f"Nouvelle tâche reçue: {task_data}")

            # Analyser la tâche
            target_agent = await self.analyze_task(task_data)

            if target_agent in self.agents:
                # Router vers l'agent spécialisé
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{self.agents[target_agent]}/execute",
                                          json=task_data) as response:
                        result = await response.json()
                        return web.json_response({
                            'status': 'routed',
                            'agent': target_agent,
                            'result': result
                        })
            else:
                # Traiter localement
                return web.json_response({
                    'status': 'processed',
                    'agent': 'orchestrator',
                    'result': {'message': 'Tâche traitée par l\'orchestrateur'}
                })

        except Exception as e:
            logger.error(f"Erreur routing tâche: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def health_check(self, request):
        """Point de contrôle santé"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'agents': list(self.agents.keys())
        })

async def main():
    agent = MCPOrchestratorAgent()
    app = web.Application()

    app.router.add_post('/route', agent.route_task)
    app.router.add_get('/health', agent.health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

    logger.info("MCP Orchestrator Agent démarré sur le port 8080")
    await asyncio.Future()  # Run forever

if __name__ == '__main__':
    asyncio.run(main())
