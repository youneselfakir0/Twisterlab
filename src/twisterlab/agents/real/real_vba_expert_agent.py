from typing import List
from twisterlab.agents.core.base import (
    TwisterAgent, 
    AgentCapability, 
    CapabilityParam, 
    ParamType, 
    AgentResponse,
    CapabilityType
)

class RealVbaExpertAgent(TwisterAgent):
    @property
    def name(self) -> str:
        return "vba-expert"

    @property
    def description(self) -> str:
        return "Expert assistant for VBA macros, Excel automation, and Office scripting."

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="analyze_vba",
                description="Analyze VBA code for issues, improvements, or optimization.",
                handler="handle_analyze_vba",
                capability_type=CapabilityType.QUERY,
                params=[
                    CapabilityParam("code", ParamType.STRING, "The VBA code snippet to analyze", required=True)
                ]
            ),
             AgentCapability(
                name="generate_macro",
                description="Generate a new VBA macro based on natural language requirements.",
                handler="handle_generate_macro",
                capability_type=CapabilityType.ACTION,
                params=[
                    CapabilityParam("requirements", ParamType.STRING, "What the macro should do", required=True)
                ]
            )
        ]

    async def handle_analyze_vba(self, code: str) -> AgentResponse:
        """Analyze VBA code using Cortex AI."""
        from twisterlab.services.cortex import CortexClient
        client = CortexClient()
        
        prompt = f"""You are an expert VBA (Excel) code reviewer.
Analyze the following VBA code and provide ONLY a JSON list of issues. Each issue must have "severity" (low, medium, high, critical) and "message".
If no issues are found, return an empty array [].

Code to analyze:
```vba
{code}
```
"""
        response = await client.generate(prompt=prompt, model="llama3.2:1b")
        
        # Simple heuristic fallback or extraction logic could be added,
        # but for now we'll just pass the LLM response.
        import json
        issues = []
        try:
            # Try to parse the response text if it's pure JSON
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.split("```json")[1].split("```")[0].strip()
            elif text.startswith("["):
                text = text.split("]")[0] + "]"
            
            issues = json.loads(text)
            if not isinstance(issues, list):
                issues = []
        except Exception:
            # Fallback to heuristics if LLM JSON parsing fails
            if "Select" in code or "Activate" in code:
                issues.append({"severity": "medium", "message": "Avoid using .Select or .Activate."})
            
            issues.append({"severity": "info", "message": "LLM review parsing failed. Showing static heuristic results.", "llm_raw": response.text[:200]})

        return AgentResponse(success=True, data={
            "status": "completed",
            "language": "vba", 
            "issues_found": len(issues),
            "issues": issues,
            "tip": "Analyzed successfully by Cortex AI"
        })

    async def handle_generate_macro(self, requirements: str) -> AgentResponse:
        """Generate VBA macro using Cortex AI."""
        from twisterlab.services.cortex import CortexClient
        client = CortexClient()
        
        prompt = f"""You are an expert VBA developer.
Write a secure and optimized VBA macro that accomplishes the following task:
{requirements}

Return ONLY the VBA code within ```vba ... ``` codeblocks. Do not include any other explanations.
Start with:
Application.ScreenUpdating = False
Application.Calculation = xlCalculationManual

And end with restoring them.
"""
        response = await client.generate(prompt=prompt, model="llama3.2:1b")
        
        code_result = response.text
        if "```vba" in code_result:
            code_result = code_result.split("```vba")[1].split("```")[0].strip()
        elif "```" in code_result:
            code_result = code_result.split("```")[1].split("```")[0].strip()
            
        return AgentResponse(success=True, data={
             "status": "success",
             "message": "Macro generated successfully by Cortex AI",
             "code": code_result
        })
