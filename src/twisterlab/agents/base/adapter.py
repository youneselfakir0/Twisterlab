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
            try:
                sig = inspect.signature(handler)
                params = sig.parameters
                has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
                
                if has_kwargs:
                    return await handler(**kwargs)
                else:
                    # Filter and Map kwargs
                    allowed_params = list(params.keys())
                    final_kwargs = {}
                    used_keys = set()
                    
                    # 1. Direct match
                    for k in allowed_params:
                        if k in kwargs:
                            final_kwargs[k] = kwargs[k]
                            used_keys.add(k)
                    
                    # 2. Smart mapping for missing required params
                    for k, p in params.items():
                        if k not in final_kwargs and p.default is p.empty and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY):
                            # Try to find a fuzzy match in remaining kwargs
                            # common synonyms for text/content
                            synonyms = ['text', 'content', 'ticket_text', 'task', 'message', 'msg', 'input', 'text_content', 'query', 'query_string']
                            if k in synonyms:
                                for sk in synonyms:
                                    if sk in kwargs and sk not in used_keys:
                                        final_kwargs[k] = kwargs[sk]
                                        used_keys.add(sk)
                                        break
                    
                    # 3. Fallback: if still missing but we have some unused kwargs
                    for k, p in params.items():
                        if k not in final_kwargs and p.default is p.empty:
                            remaining_keys = [sk for sk in kwargs.keys() if sk not in used_keys]
                            if remaining_keys:
                                # Prioritize keys that look like 'text', 'code', 'query', 'task'
                                best_key = remaining_keys[0]
                                for rk in remaining_keys:
                                    if any(s in rk.lower() for s in ['text', 'task', 'query', 'content', 'message', 'code']):
                                        best_key = rk
                                        break
                                
                                final_kwargs[k] = kwargs[best_key]
                                used_keys.add(best_key)
                                logger.info(f"Fuzzy-mapped {best_key} to {k} for {self.name}.{tool_name}")

                    # 4. Final check: if still empty but we have ANY kwarg, and handler has 1 param
                    if not final_kwargs and len(params) == 1 and kwargs:
                        first_param = list(params.keys())[0]
                        first_val = list(kwargs.values())[0]
                        final_kwargs[first_param] = first_val
                        logger.warning(f"Brute-force mapped first arg to {first_param} for {self.name}.{tool_name}")

                    return await handler(**final_kwargs)
            except Exception as e:
                logger.error(f"Dispatch failure for {self.name}.{tool_name}: {e}. Input: {list(kwargs.keys())}")
                raise e

        # Style B: execute("tool", **kwargs) - Modern CoreAgent
        if hasattr(self.agent, "execute"):
            sig = inspect.signature(self.agent.execute)
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            
            try:
                # If target has single arg task/context signature (e.g., execute(task))
                if len(sig.parameters) == 1 and not has_kwargs:
                    logger.warning(f"DEPRECATION: Agent {self.name} uses legacy execute signature.")
                    return await self.agent.execute(kwargs)
                
                if has_kwargs:
                    return await self.agent.execute(tool_name, **kwargs)
                else:
                    # Filter kwargs, but keep tool_name as positional if it's the first param
                    params_to_pass = list(sig.parameters.keys())
                    if params_to_pass and params_to_pass[0] in ('tool_name', 'capability', 'name', 'task'):
                        # It probably expects tool_name as first arg
                        filtered_kwargs = {k: v for k, v in kwargs.items() if k in params_to_pass[1:]}
                        return await self.agent.execute(tool_name, **filtered_kwargs)
                    else:
                        filtered_kwargs = {k: v for k, v in kwargs.items() if k in params_to_pass}
                        return await self.agent.execute(**filtered_kwargs)
            except TypeError:
                logger.warning(f"DEPRECATION: Fallback for Agent {self.name} legacy execute signature.")
                return await self.agent.execute(kwargs)

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
