"""
Shim module to re-export the DesktopCommanderAgent and a simple CommandStatus
class for compatibility with older imports and tests.

This module delegates to the implementation in `twisterlab.agents.base` where
the `DesktopCommanderAgent` now lives.
"""

from __future__ import annotations

from dataclasses import dataclass

from twisterlab.agents.base import DesktopCommanderAgent as BaseDesktopCommanderAgent


@dataclass
class CommandStatus:
    status: str
    exit_code: int = 0
    output: str | None = None
    error: str | None = None


class DesktopCommanderAgent(BaseDesktopCommanderAgent):
    """Compatibility wrapper that re-uses the DesktopCommanderAgent from base.

    This keeps old import paths intact while avoiding duplication.
    """

    pass


__all__ = ["DesktopCommanderAgent", "CommandStatus"]
