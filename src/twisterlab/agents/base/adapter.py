"""
Agent Migration Adapter
Normalizes legacy agent contracts into the UnifiedAgentResponse format.
Handles handle_*, execute({...}), and execute("tool", **kwargs) signatures.
"""

import logging
import time
import asyncio
from typing import Any, Dict, Optional, Callable
from twisterlab.api.schemas.common import UnifiedAgentResponse, AgentErrorCode

logger = logging.getLogger(__name__)

class AgentAdapter:
    """
    Wraps a legacy TwisterLab agent and provides a unified interface.
    Ensures Phase 1 compatibility without requiring immediate agent code changes.
    """

    def __init__(self, agent: Any):
        self.agent = agent
        self.name = getattr(agent, "name", "unknown")

    @property
    def agent_name(self) -> str:
        """Compatibility property for Maestro execution log."""
        return self.name
        
    async def call(self, tool_name: str, **kwargs) -> UnifiedAgentResponse:
        """
        Executes a tool on the agent using the detected legacy signature.
        Always returns a UnifiedAgentResponse.
        """
        try:
            from twisterlab.monitoring_utils import agent_call_timer, record_agent_error
        except ImportError:
            agent_call_timer = None
            record_agent_error = None

        timer_ctx = None
        if agent_call_timer:
            timer_ctx = agent_call_timer(self.name, tool_name)
            timer_ctx.__enter__()

        start_time = time.perf_counter()
        
        try:
            # 1. Detect Signature and Execute
            result = await self._dispatch(tool_name, **kwargs)
            
            # 2. Normalize Result
            response = self._normalize_result(result)
            
            # 3. Add Metadata
            response.metadata["execution_time_ms"] = int((time.perf_counter() - start_time) * 1000)
            response.metadata["agent_name"] = self.name
            response.metadata["tool_name"] = tool_name
            
            if not response.success and record_agent_error:
                record_agent_error(self.name, response.error_code or "AGENT_FAILURE")

            return response

        except Exception as e:
            logger.exception(f"Adapter error calling {self.name}.{tool_name}")
            if record_agent_error:
                record_agent_error(self.name, "ADAPTER_CRASH")
                
            return UnifiedAgentResponse(
                success=False,
                error=str(e),
                error_code=AgentErrorCode.AGENT_FAILURE,
                metadata={"exception": type(e).__name__}
            )
        finally:
            if timer_ctx:
                timer_ctx.__exit__(None, None, None)

    async def _dispatch(self, tool_name: str, **kwargs) -> Any:
        """Heuristic dispatch to the correct agent method with signature sniffing."""
        import inspect

        handler = None
        if hasattr(self.agent, "get_capability"):
            cap = self.agent.get_capability(tool_name)
            if cap and hasattr(self.agent, cap.handler):
                handler = getattr(self.agent, cap.handler)

        if not handler:
            handler_name = f"handle_{tool_name}"
            if hasattr(self.agent, handler_name):
                handler = getattr(self.agent, handler_name)

        if handler:
            sig = inspect.signature(handler)
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            cleaned_kwargs = kwargs.copy()
            if "request_id" in cleaned_kwargs and "request_id" not in sig.parameters and not has_kwargs:
                cleaned_kwargs.pop("request_id", None)
            return await handler(**cleaned_kwargs)

        # Style B: execute("tool", **kwargs) - Modern CoreAgent
        if hasattr(self.agent, "execute"):
            sig = inspect.signature(self.agent.execute)
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            cleaned_kwargs = kwargs.copy()
            
            try:
                # If target has single arg task/context signature (e.g., execute(task))
                if len(sig.parameters) == 1 and not has_kwargs:
                    logger.warning(f"DEPRECATION: Agent {self.name} uses legacy execute signature.")
                    return await self.agent.execute(cleaned_kwargs)
                
                if "request_id" in cleaned_kwargs and "request_id" not in sig.parameters and not has_kwargs:
                    cleaned_kwargs.pop("request_id", None)
                return await self.agent.execute(tool_name, **cleaned_kwargs)
            except TypeError:
                logger.warning(f"DEPRECATION: Fallback for Agent {self.name} legacy execute signature.")
                return await self.agent.execute(cleaned_kwargs)

        raise AttributeError(f"No handler found for tool '{tool_name}' on agent '{self.name}'")

    def _normalize_result(self, result: Any) -> UnifiedAgentResponse:
        """Converts heterogeneous agent outputs to UnifiedAgentResponse."""
        
        # 1. Null handling
        if result is None:
            return UnifiedAgentResponse(success=True, data=None)

        # 2. Already normalized? (AgentResponse or UnifiedAgentResponse)
        if hasattr(result, "success"):
            return UnifiedAgentResponse(
                success=getattr(result, "success", True),
                data=getattr(result, "data", None),
                error=getattr(result, "error", None),
                metadata=getattr(result, "metadata", {})
            )

        # 3. Dictionary response? (The most common legacy format)
        if isinstance(result, dict):
            # Try to find a success indicator
            status = str(result.get("status") or result.get("state") or "").upper()
            success_from_dict = result.get("success")
            
            # Map common legacy success strings
            success = (
                success_from_dict is True or 
                status in ("SUCCESS", "OK", "READY", "COMPLETED", "DONE", "TRUE", "PASS")
            )
            
            # If we didn't find an explicit status, and it's not a known error, assume success if data is present
            if status == "" and success_from_dict is None:
                success = "error" not in result

            # Extract data: use 'data' key, or 'result', or 'content', or fallback to the whole dict
            data = result.get("data")
            if data is None:
                 data = result.get("result") or result.get("content") or result

            return UnifiedAgentResponse(
                success=success,
                data=data,
                error=result.get("error") or result.get("message") or result.get("err"),
                metadata=result.get("metadata", {})
            )

        # 4. Fallback for raw outputs (primitives, lists, etc)
        # We wrap these as success=True
        return UnifiedAgentResponse(success=True, data=result)
