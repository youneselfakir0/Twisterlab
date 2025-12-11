"""
Local JWT authentication stub used for development and testing.

This class provides a minimal interface for LocalAuth so HybridAuth can pick
it during tests that prefer local mode.
"""

from __future__ import annotations

from typing import Optional


class LocalAuth:
    def __init__(self, secret: Optional[str] = None):
        self.secret = secret or "local-secret"

    def validate_token_structure(self, token: str) -> bool:
        # For local tests, accept simple tokens that contain 2 dots (like a JWT)
        if not token or not isinstance(token, str):
            return False
        return token.count(".") == 2

    def get_authorization_url(self, state: str = "") -> str:
        # Local auth doesn't actually redirect — provide a fake URL for tests
        return f"http://localhost:8000/local-login?state={state}"

    async def acquire_token_by_code(self, code: str) -> dict:
        return {"access_token": "local-fake-token", "expires_in": 3600}
