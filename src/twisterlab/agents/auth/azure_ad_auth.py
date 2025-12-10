"""
Minimal Azure AD authentication stub used in tests and as a placeholder in the
project during development. This is intentionally simple and not production
ready. Replace with a full implementation (MSAL or similar) when needed.
"""

from __future__ import annotations

import os
from typing import Optional


class AzureADAuth:
    """Test-friendly Azure AD authentication stub.

    Provides a very small surface used by the API and tests:
      - validate_token_structure(token) -> bool
      - get_authorization_url(state: str) -> str
      - acquire_token_by_code(code: str) -> dict
    """

    def __init__(
        self, tenant_id: Optional[str] = None, client_id: Optional[str] = None
    ):
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID", "demo-tenant")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID", "demo-client")

    def validate_token_structure(self, token: str) -> bool:
        """Quick heuristic to validate token shape used in tests.

        This is not a security control — it only avoids import/attribute errors
        in the test environment while keeping tests fast.
        """
        if not token or not isinstance(token, str):
            return False
        return token.count(".") == 2

    def get_authorization_url(self, state: str = "") -> str:
        return (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
            f"?client_id={self.client_id}&response_type=code&state={state}"
        )

    async def acquire_token_by_code(self, code: str) -> dict:
        # Return a shallow fake token response suitable for tests
        return {"access_token": "fake-access-token", "expires_in": 3600}
