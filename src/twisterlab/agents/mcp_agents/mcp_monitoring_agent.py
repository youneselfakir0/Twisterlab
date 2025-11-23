#!/usr/bin/env python3
"""
MCP Monitoring Agent - Remplace le workflow service-health-check de N8N
Gère la surveillance intelligente des services avec alertes
"""

import asyncio
import aiohttp
from aiohttp import web
import json
import logging
from datetime import datetime
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPMonitoringAgent:
    def __init__(self):
        self.services = ['docker', 'prometheus', 'grafana', 'mcp_agents']
        self.alerts = []

    async def check_service_health(self, service_name):
        """Vérifie la santé d'un service"""
        try:
            if service_name == 'docker':
                result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
                return result.returncode == 0
            elif service_name == 'prometheus':
                # Vérifier si le conteneur Prometheus fonctionne
                result = subprocess.run(['docker', 'ps', '--filter', 'name=prometheus', '--format', '{{.Names}}'],
                                      capture_output=True, text=True)
                return 'prometheus' in result.stdout
            elif service_name == 'grafana':
                result = subprocess.run(['docker', 'ps', '--filter', 'name=grafana', '--format', '{{.Names}}'],
                                      capture_output=True, text=True)
                return 'grafana' in result.stdout
            elif service_name == 'mcp_agents':
                # Vérifier les agents MCP
                agents_running = 0
                for port in [8080, 8081, 8082]:
                    try:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(f'http://localhost:{port}/health', timeout=5) as response:
                                if response.status == 200:
                                    agents_running += 1
                    except:
                        pass
                return agents_running >= 2  # Au moins 2 agents sur 3
            return False
        except Exception as e:
            logger.error(f"Erreur vérification {service_name}: {e}")
            return False

    async def perform_health_check(self, request):
        """Effectue une vérification de santé complète"""
        try:
            results = {}
            alerts = []

            for service in self.services:
                is_healthy = await self.check_service_health(service)
                results[service] = 'healthy' if is_healthy else 'unhealthy'

                if not is_healthy:
                    alert = {
                        'service': service,
                        'status': 'unhealthy',
                        'timestamp': datetime.now().isoformat(),
                        'message': f'Service {service} est défaillant'
                    }
                    alerts.append(alert)
                    self.alerts.append(alert)

            # Garder seulement les 100 dernières alertes
            self.alerts = self.alerts[-100:]

            return web.json_response({
                'timestamp': datetime.now().isoformat(),
                'services': results,
                'alerts': alerts[-10:]  # Dernières 10 alertes
            })

        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            return web.json_response({'error': str(e)}, status=500)

    async def get_alerts(self, request):
        """Récupère les alertes récentes"""
        limit = int(request.query.get('limit', 10))
        return web.json_response({
            'alerts': self.alerts[-limit:],
            'total': len(self.alerts)
        })

    async def health_check(self, request):
        """Point de contrôle santé de l'agent"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'monitored_services': self.services,
            'active_alerts': len([a for a in self.alerts if a.get('status') == 'unhealthy'])
        })

async def main():
    agent = MCPMonitoringAgent()
    app = web.Application()

    app.router.add_get('/check', agent.perform_health_check)
    app.router.add_get('/alerts', agent.get_alerts)
    app.router.add_get('/health', agent.health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8082)
    await site.start()

    logger.info("MCP Monitoring Agent démarré sur le port 8082")
    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())
