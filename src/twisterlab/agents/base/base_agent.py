"""
Base Agent module for TwisterLab.

Provides the foundational BaseAgent class and utilities with OpenTelemetry tracing.
"""

from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Any, Dict
import uuid

from opentelemetry import trace
from opentelemetry.trace import StatusCode


def accepts_context_or_task(func):
    """Decorator for backward compatibility with different execute signatures."""
    return func


class BaseAgent(ABC):
    """Abstract base class for all TwisterLab agents."""

    # Subclasses can override this to specify the operation name for tracing
    operation_name: str = "execute"

    def __init__(self):
        self.agent_id = str(uuid.uuid4())
        self.status = SimpleNamespace(value="READY")
        self.version = "1.0"
        # Get a tracer for this module
        self._tracer = trace.get_tracer(__name__)

    @abstractmethod
    async def _process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task context. Must be implemented by subclasses."""
        pass

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with the given context, creating a trace span."""
        # Use the class name and operation_name for the span name
        span_name = f"{self.__class__.__name__}.{self.operation_name}"
        
        with self._tracer.start_as_current_span(
            span_name,
            attributes={
                "agent.id": self.agent_id,
                "agent.name": self.__class__.__name__,
                "agent.version": self.version,
            }
        ) as span:
            try:
                result = await self._process(context)
                span.set_status(StatusCode.OK)
                # Add output size as an attribute (useful for debugging, avoid if large/PII)
                if isinstance(result, dict) and "text" in result:
                    span.set_attribute("output.text_length", len(result["text"]))
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise


__all__ = ["BaseAgent", "accepts_context_or_task"]
