"""
HybridAuth stub - picks between LocalAuth and AzureADAuth depending on
configuration. Keep this minimal and test-friendly.
"""

from __future__ import annotations

import os
from typing import Optional

from twisterlab.agents.auth.local_auth import LocalAuth
from twisterlab.agents.auth.azure_ad_auth import AzureADAuth


class HybridAuth:
    """Very small HybridAuth that selects LocalAuth if TWISTERLAB_AUTH_LOCAL is set
    otherwise uses AzureADAuth. This is test/dev utility only.
    """

    def __init__(self, force_local: Optional[bool] = None):
        self.force_local = (
            force_local
            if force_local is not None
            else os.getenv("TWISTERLAB_AUTH_LOCAL") == "true"
        )
        self.local = LocalAuth()
        self.azure = AzureADAuth()

    def get_adapter(self):
        return self.local if self.force_local else self.azure

    def validate_token_structure(self, token: str) -> bool:
        return self.get_adapter().validate_token_structure(token)

    def get_authorization_url(self, state: str = "") -> str:
        return self.get_adapter().get_authorization_url(state)

    async def acquire_token_by_code(self, code: str) -> dict:
        return await self.get_adapter().acquire_token_by_code(code)
