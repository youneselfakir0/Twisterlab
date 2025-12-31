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

class RealCodeReviewAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "code-review"

    @property
    def description(self) -> str:
        return "Analyzes code for potential issues and security vulnerabilities."

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
                name="security_scan",
                description="Scan code for known security patterns (e.g., hardcoded secrets).",
                handler="handle_security_scan",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("code", ParamType.STRING, "The code snippet to scan", required=True)
                ]
            )
        ]

    async def handle_analyze(self, code: str, language: str = "python") -> AgentResponse:
        """Simple heuristic-based analysis."""
        issues = []
        
        if "print(" in code:
            issues.append({"severity": "info", "message": "Discovered 'print' statement. Consider using logging."})
        
        if "TODO" in code:
            issues.append({"severity": "low", "message": "Discovered TODO comment. Please address."})
            
        if "try:" in code and "except:" in code and "Exception" not in code:
             issues.append({"severity": "medium", "message": "Bare 'except:' clause found. Catch specific exceptions."})

        return AgentResponse(success=True, data={
            "status": "completed",
            "language": language, 
            "issues_found": len(issues),
            "issues": issues
        })

    async def handle_security_scan(self, code: str) -> AgentResponse:
        """Simple security scan."""
        findings = []
        
        # Check for potential hardcoded secrets
        if match := re.search(r"(?i)(password|secret|key)\s*=\s*['\"][^'\"]+['\"]", code):
             findings.append({"severity": "high", "message": f"Potential hardcoded secret found: {match.group(0)}"})

        if "eval(" in code:
             findings.append({"severity": "critical", "message": "Use of 'eval()' detected. This is a huge security risk."})

        return AgentResponse(success=True, data={
             "status": "secure" if not findings else "vulnerable",
             "findings_count": len(findings),
             "findings": findings
        })
