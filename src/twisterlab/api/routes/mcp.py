from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from twisterlab.agents.real.real_sentiment_analyzer_agent import (
    SentimentAnalyzerAgent,
)

router = APIRouter()


class ExecuteRequest(BaseModel):
    tool_name: str
    args: dict | None = None


class AnalyzeSentimentRequest(BaseModel):
    """Request model for sentiment analysis."""

    text: str = Field(..., description="Text to analyze for sentiment")
    detailed: bool = Field(
        default=False, description="Return detailed analysis with keyword extraction"
    )


class MCPResponse(BaseModel):
    """Standard MCP response format."""

    content: list[dict] = Field(default_factory=list)
    isError: bool = False


@router.post("/execute")
async def execute_tool(req: ExecuteRequest):
    # Minimal stub for MCP execution used in tests / dev environment.
    try:
        # Simulate execution response
        return {
            "status": "success",
            "result": {"executed_tool": req.tool_name, "args": req.args},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    return {"status": "MCP server is running"}


@router.post("/analyze_sentiment", response_model=MCPResponse)
async def analyze_sentiment(request: AnalyzeSentimentRequest) -> MCPResponse:
    """
    Analyze text sentiment using SentimentAnalyzerAgent.

    **Input**:
    - `text`: Text to analyze for sentiment
    - `detailed`: Return detailed analysis (default: false)

    **Output**:
    - sentiment, confidence, keywords (if detailed)
    """
    try:
        # Create agent instance
        agent = SentimentAnalyzerAgent()

        # Execute sentiment analysis using capability name
        result = await agent.execute(
            "analyze_sentiment", 
            text=request.text, 
            detailed=request.detailed
        )

        # Return success response with MCP content format
        return MCPResponse(
            content=result.to_mcp_content(), 
            isError=not result.success
        )

    except Exception as e:
        # Return error response
        return MCPResponse(
            content=[{"type": "text", "text": f"Error: {str(e)}"}], isError=True
        )

