import logging
import os
from pathlib import Path
from typing import Dict, Optional, Any
try:
    import jinja2
except ImportError:
    jinja2 = None

logger = logging.getLogger(__name__)

class PromptLoader:
    """
    PromptLoader v4.0 (Operation Antigravity).
    Uses Jinja2 for robust prompt templating and variable validation.
    
    Supports:
    - Path resolution: src/twisterlab/agents/prompts/maestro/*.jinja2
    - Fallback: safe strings if files are missing.
    - Context: Dynamic injection of system variables.
    """
    
    _env: Optional[Any] = None
    _base_dir: Path = Path(__file__).parent
    
    # Safe fallbacks for business continuity
    _fallbacks: Dict[str, str] = {
        "maestro/planning": "Analyze this task: {{ task }}. Return JSON.",
        "maestro/synthesis": "Summarize results: {{ results }}.",
        "core/cortex": "You are Cortex IA. Objective: {{ objective }}."
    }

    @classmethod
    def _get_env(cls) -> Any:
        """Lazy-initialize the Jinja2 environment."""
        if cls._env is None and jinja2:
            cls._env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(cls._base_dir)),
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True,
                cache_size=100
            )
        return cls._env

    @classmethod
    def render(cls, template_name: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Renders a prompt template with the provided context.
        
        Args:
            template_name: Relative path to the template (e.g., 'maestro/planning')
            context: Variables to inject into the template.
        """
        context = context or {}
        env = cls._get_env()
        
        # 1. Try loading from Jinja2 filesystem
        if env:
            try:
                # Add .jinja2 extension automatically if not provided
                fname = template_name if template_name.endswith('.jinja2') else f"{template_name}.jinja2"
                template = env.get_template(fname)
                return template.render(**context)
            except (jinja2.TemplateNotFound, jinja2.TemplateSyntaxError) as e:
                logger.warning(f"Jinja2 error for '{template_name}': {e}. Switching to fallback.")
        else:
            logger.warning("Jinja2 not installed. Using simple fallback logic.")

        # 2. Fallback logic (Basic or Predefined)
        raw_text = cls._fallbacks.get(template_name, "Objective: {{ task }}")
        
        # Simple string replacement fallback if Jinja2 is unavailable
        for key, val in context.items():
            raw_text = raw_text.replace(f"{{{{ {key} }}}}", str(val)).replace(f"{{{{{key}}}}}", str(val))
        
        return raw_text

    @classmethod
    def get(cls, name: str, **kwargs) -> str:
        """Compatibility wrapper for v3 legacy code."""
        return cls.render(name, kwargs)

# Standardized path initialization
def ensure_prompt_structure():
    """Ensures directories for prompts exist (Build-time helper)."""
    (Path(__file__).parent / "maestro").mkdir(parents=True, exist_ok=True)
    (Path(__file__).parent / "core").mkdir(parents=True, exist_ok=True)
    (Path(__file__).parent / "agents").mkdir(parents=True, exist_ok=True)
