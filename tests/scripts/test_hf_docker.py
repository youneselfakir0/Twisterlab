import asyncio
import logging
from twisterlab.services.system_client import DockerSystemClient

logging.basicConfig(level=logging.DEBUG)

async def test():
    client = DockerSystemClient()
    try:
        health = await client.health_check()
        print(f"Health returned successfully: {health.status.value}, {health.message}")
        print(f"Metadata Services: {health.metadata.get('services', {})}")
    except Exception as e:
        print(f"FAILED WITH EXCEPTION: {type(e).__name__} - {str(e)}")

asyncio.run(test())
