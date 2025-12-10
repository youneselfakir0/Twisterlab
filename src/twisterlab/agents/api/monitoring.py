"""
Middleware et utilitaires de monitoring pour l'API TwisterLab
"""

import logging
import time
from typing import Callable

from fastapi.responses import PlainTextResponse


class MetricsMiddleware:
    """
    Middleware pour collecter des métriques de performance
    """

    def __init__(self, app: Callable, logger: logging.Logger):
        self.app = app
        self.logger = logger

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()

        # Traiter la requête
        await self.app(scope, receive, send)

        # Calculer le temps de traitement
        final_process_time = time.time() - start_time
        self.logger.info(f"Request processed in {final_process_time:.4f}s")


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Configure le logging structuré pour la production
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            *(logging.FileHandler(log_file) for _ in [log_file] if log_file),
        ],
    )
    return logging.getLogger(__name__)


async def create_health_endpoint():
    """
    Point de terminaison de santé de l'API
    """
    return PlainTextResponse("OK", status_code=200)
