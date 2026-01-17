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
        """Comprehensive security scan for common vulnerabilities."""
        findings = []
        
        # Security patterns with their descriptions
        SECURITY_PATTERNS = [
            # Hardcoded secrets - assignment patterns
            (r"(?i)(password|secret|api_?key|token|credentials?)\s*=\s*['\"][^'\"]+['\"]",
             "high", "Potential hardcoded secret in assignment"),
            
            # Hardcoded secrets - comparison patterns (leaked in condition)
            (r"(?i)(password|secret|pin|code)\s*==\s*['\"][^'\"]+['\"]",
             "high", "Hardcoded credential in comparison - security vulnerability"),
            
            # SQL Injection risks
            (r"(?i)(execute|query|cursor\.execute)\s*\([^)]*\+\s*[^\)]+\)|f['\"].*\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE)",
             "critical", "Potential SQL injection - use parameterized queries"),
            
            # Dangerous functions
            (r"\beval\s*\(", "critical", "Use of 'eval()' detected - code injection risk"),
            (r"\bexec\s*\(", "critical", "Use of 'exec()' detected - code injection risk"),
            (r"\b__import__\s*\(", "high", "Dynamic import detected - potential security issue"),
            
            # Insecure deserialization
            (r"pickle\.loads?\(", "high", "Use of pickle - potential arbitrary code execution"),
            (r"yaml\.load\s*\([^)]*\)", "high", "Use of yaml.load - use safe_load instead"),
            
            # Weak cryptography
            (r"(?i)md5|sha1\s*\(", "medium", "Weak hash algorithm - use SHA-256 or better"),
            
            # Sensitive data exposure
            (r"print\s*\([^)]*(?:password|secret|token|key)[^)]*\)",
             "medium", "Potential sensitive data in print statement"),
            
            # Debug/development code
            (r"DEBUG\s*=\s*True", "medium", "Debug mode enabled - disable in production"),
        ]
        
        for pattern, severity, message in SECURITY_PATTERNS:
            if match := re.search(pattern, code):
                findings.append({
                    "severity": severity,
                    "message": message,
                    "match": match.group(0)[:100]  # Truncate long matches
                })
        
        status = "vulnerable" if findings else "secure"
        
        return AgentResponse(success=True, data={
             "status": status,
             "findings_count": len(findings),
             "findings": findings
        })
