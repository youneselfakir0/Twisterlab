"""
Modernized RealCodeReviewAgent
"""

import re
from typing import List
from twisterlab.agents.core.base import (
    TwisterAgent, 
    AgentCapability, 
    CapabilityParam, 
    ParamType, 
    AgentResponse,
    CapabilityType
)
from twisterlab.services.analytics.code_review_orchestrator import CodeReviewOrchestrator

class RealCodeReviewAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "code-review"

    @property
    def description(self) -> str:
        return "Coordinated Code Analysis & Remediation Platform (DevSecOps)."

    def __init__(self, registry=None):
        super().__init__(registry)
        self.orchestrator = CodeReviewOrchestrator()

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_code",
                description="Analyze a snippet of code for basic issues.",
                handler="handle_analyze",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("code", ParamType.STRING, "The code snippet to analyze", required=True),
                    CapabilityParam("language", ParamType.STRING, "The programming language", required=False)
                ]
            ),
            AgentCapability(
                name="deep_audit",
                description="Executes a coordinated multi-agent analysis (Quality, Security, Arch).",
                handler="handle_deep_audit",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("code", ParamType.STRING, "The code snippet to audit", required=True),
                    CapabilityParam("filename", ParamType.STRING, "Optional filename for context", required=False)
                ]
            )
        ]

    async def handle_analyze(self, code: str, language: str = "python", **kwargs) -> AgentResponse:
        """Fallback to orchestrator for basic analysis."""
        return await self.handle_deep_audit(code, **kwargs)

    async def handle_deep_audit(self, code: str, filename: str = "snippet.py", **kwargs) -> AgentResponse:
        """Coordinated multi-agent analysis."""
        try:
            report = await self.orchestrator.full_review(code, filename)
            return AgentResponse(success=True, data=report)
        except Exception as e:
            logger.error(f"CodeReview: Audit failed: {e}")
            return AgentResponse(success=False, error=str(e))

    async def handle_security_scan(self, code: str, **kwargs) -> AgentResponse:
        """Dedicated security scan."""
        try:
            findings = await self.orchestrator.security_advisor.analyze(code)
            return AgentResponse(success=True, data={
                "status": "vulnerable" if findings else "secure",
                "findings": findings
            })
        except Exception as e:
            return AgentResponse(success=False, error=str(e))
