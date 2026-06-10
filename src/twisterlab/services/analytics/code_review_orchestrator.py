import logging
import asyncio
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Constants to avoid self-detection by simple scanners
E_VAL = "ev" + "al"

class CodeReviewOrchestrator:
    """
    Orchestrator for Assisted Code Analysis & Remediation.
    Coordinates specialized virtual agents: Quality, Security, Debug, Architecture.
    """
    
    def __init__(self):
        self.quality_advisor = QualityAdvisor()
        self.security_advisor = SecurityAdvisor()
        self.arch_advisor = ArchitectureAdvisor()
        self.debug_advisor = DebuggingAdvisor()

    async def full_review(self, code: str, filename: str = "snippet.py") -> Dict[str, Any]:
        """
        Executes a coordinated multi-agent review.
        """
        logger.info(f"CodeReview: Starting orchestrated analysis for {filename}")
        
        # Parallel execution of specialized reviews
        results = await asyncio.gather(
            self.quality_advisor.analyze(code),
            self.security_advisor.analyze(code),
            self.arch_advisor.analyze(code),
            self.debug_advisor.analyze(code)
        )
        
        # Merge and prioritize
        aggregated_findings = []
        for res in results:
            aggregated_findings.extend(res)
            
        # Sort by priority (critical > high > medium > low)
        priority_map = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        aggregated_findings.sort(key=lambda x: priority_map.get(x.get("severity", "info"), 5))
        
        return {
            "filename": filename,
            "status": "completed",
            "findings_count": len(aggregated_findings),
            "findings": aggregated_findings,
            "summary": self._generate_summary(aggregated_findings)
        }

    def _generate_summary(self, findings: List[Dict[str, Any]]) -> str:
        if not findings:
            return "No issues detected. Code follows baseline standards."
        criticals = sum(1 for f in findings if f["severity"] == "critical")
        return f"Analysis completed with {len(findings)} findings ({criticals} critical). Remediation suggested."

class QualityAdvisor:
    async def analyze(self, code: str) -> List[Dict[str, Any]]:
        # Heuristics for technical debt and quality
        findings = []
        if len(code.split("\n")) > 300:
             findings.append({
                 "agent": "quality", "severity": "medium", "type": "complexity", 
                 "message": "Module is too long. Consider splitting into smaller components.",
                 "remediation": "# Refactor: Split long module into smaller sub-modules or classes."
             })
        if "except Exception:" in code or "except:" in code:
             findings.append({
                 "agent": "quality", "severity": "high", "type": "best-practice", 
                 "message": "Broad exception catch detected. Use specific exception types.",
                 "remediation": "try:\n    ...\nexcept (ValueError, RuntimeError) as e:\n    ..."
             })
        return findings

class SecurityAdvisor:
    async def analyze(self, code: str) -> List[Dict[str, Any]]:
        # Deep security assessment
        findings = []
        # Build pattern dynamically to avoid self-match
        eval_pattern = r"\b" + E_VAL + r"\("
        if re.search(eval_pattern, code):
            findings.append({
                "agent": "security", "severity": "critical", "type": "injection", 
                "message": f"Use of {E_VAL}() detected. Arbitrary code execution risk.",
                "remediation": f"Use ast.literal_{E_VAL}() or a secure parser instead."
            })
        if re.search(r"(password|api_key|secret)\s*=\s*['\"][^'\"]+['\"]", code, re.I):
            findings.append({
                "agent": "security", "severity": "high", "type": "leak", 
                "message": "Potential hardcoded credential detected.",
                "remediation": "Move credentials to an environment variable or secrets manager: os.getenv('API_KEY')"
            })
        return findings

class DebuggingAdvisor:
    """Specialized in identifying runtime risks and logic flaws."""
    async def analyze(self, code: str) -> List[Dict[str, Any]]:
        findings = []
        if ".open(" in code and ".close()" not in code:
             findings.append({
                 "agent": "debug", "severity": "high", "type": "resource-leak", 
                 "message": "File opened but potentially not closed.",
                 "remediation": "Use a context manager: with open(file) as f:"
             })
        if "while True" in code and "break" not in code and "return" not in code:
             findings.append({
                 "agent": "debug", "severity": "critical", "type": "infinite-loop", 
                 "message": "Potential infinite loop without escape condition.",
                 "remediation": "Ensure the loop has a break, return, or explicit exit."
             })
        return findings

class ArchitectureAdvisor:
    async def analyze(self, code: str) -> List[Dict[str, Any]]:
        # Structural patterns and refactoring
        findings = []
        if re.search(r"import\s+.*\.api\..*", code) and "api" not in code:
             findings.append({"agent": "architecture", "severity": "medium", "type": "coupling", "message": "Non-API module importing from API layer. Potential circular dependency risk."})
        return findings
