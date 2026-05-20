import logging
import threading
from typing import Dict, List, Optional, Callable, Any, Type
from enum import Enum

# Standardized Agent Status
class AgentStatus(str, Enum):
    REGISTERED = "registered"    # Factory known, instance not created
    INITIALIZING = "initializing" # Construction in progress
    ONLINE = "online"            # Ready for work
    FAILED = "failed"            # Construction or critical failure
    DEGRADED = "degraded"        # Online but with errors

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Modernized Thread-safe Singleton Registry.
    Implements Lazy Loading, Robust Naming, and Deterministic Discovery.
    """

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AgentRegistry, cls).__new__(cls)
                    cls._instance._initialized_context = False
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized_context") and self._initialized_context:
            return

        self._factories: Dict[str, Callable[[], Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._status: Dict[str, AgentStatus] = {}
        self._errors: Dict[str, str] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {} # Static Metadata
        self._lookup_index: Dict[str, str] = {} # normalized_name -> primary_key
        
        self._initialized_context = True
        self._register_default_factories()

    def _normalize_name(self, name: str) -> str:
        """Standardized naming normalization: lowercase and remove separators."""
        if not name:
            return ""
        return name.lower().replace("-", "").replace("_", "").replace(" ", "")

    def _register_default_factories(self):
        """Registers all core TwisterLab agents with static capabilities and explicit priorities."""
        
        def make_factory(import_path: str, class_name: str):
            def factory():
                import importlib
                module = importlib.import_module(import_path)
                cls = getattr(module, class_name)
                return cls()
            return factory

        # Core Registry List
        # Format: (key, import_path, class_name, description, capabilities, priority)
        # Higher priority agents win in capability resolution.
        registry_data = [
            ("classifier", "twisterlab.agents.real.real_classifier_agent", "RealClassifierAgent", "Classifies incoming text or tickets.", ["classify_ticket"], 10),
            ("sentiment", "twisterlab.agents.real.real_sentiment_analyzer_agent", "SentimentAnalyzerAgent", "Analyzes text sentiment.", ["analyze_sentiment"], 10),
            ("summarizer", "twisterlab.agents.real.real_summarizer_agent", "RealSummarizerAgent", "Summarizes long text snippets.", ["summarize"], 10),
            ("translation", "twisterlab.agents.real.real_translation_agent", "RealTranslationAgent", "Translates text between languages.", ["translate"], 10),
            ("cortex", "twisterlab.agents.real.cortex_ia_agent", "CortexIAAgent", "Cortex AI Master Core Interface.", ["chat"], 20), # Preferred AI
            ("code-review", "twisterlab.agents.real.real_code_review_agent", "RealCodeReviewAgent", "Performs automated code analysis.", ["analyze_code", "security_scan"], 10),
            ("vba-expert", "twisterlab.agents.real.real_vba_expert_agent", "RealVbaExpertAgent", "Excel/VBA automation expert.", ["write_vba"], 10),
            ("resolver", "twisterlab.agents.real.real_resolver_agent", "RealResolverAgent", "Resolves database or system issues.", ["resolve_ticket"], 10),
            ("monitoring", "twisterlab.agents.real.real_monitoring_agent", "RealMonitoringAgent", "Infrastructure monitoring agent.", ["monitor_system_health", "collect_metrics"], 10),
            ("backup", "twisterlab.agents.real.real_backup_agent", "RealBackupAgent", "Service and Docker backup lead.", ["create_backup"], 10),
            ("sync", "twisterlab.agents.real.real_sync_agent", "RealSyncAgent", "System synchronization manager.", ["sync_cache_db"], 10),
            ("archive", "twisterlab.agents.real.real_archive_agent", "RealArchiveAgent", "Data archiving and mission logs.", ["archive_mission", "archive_result", "archive_chat"], 20), # Primary archiver
            ("commander", "twisterlab.agents.real.real_desktop_commander_agent", "RealDesktopCommanderAgent", "Local system command execution.", ["execute_command"], 10),
            ("browser", "twisterlab.agents.real.browser_agent", "RealBrowserAgent", "Web browsing and automation.", ["browse"], 10),
            ("n8n-navigator", "twisterlab.agents.real.n8n_navigator_agent", "N8nNavigatorAgent", "Orchestrates n8n workflows.", ["n8n_trigger_webhook"], 10),
            ("invoke-ai", "twisterlab.agents.real.invoke_ai_agent", "InvokeAIAgent", "AI Image generation bridge.", ["generate_image"], 10),
            ("notion", "twisterlab.agents.real.real_notion_agent", "RealNotionAgent", "Notion workspace synchronization.", ["create_page", "list_pages", "sync_notion"], 10),
            ("trader", "twisterlab.agents.real.real_trader_agent", "RealTraderAgent", "Analyzes crypto markets and generates scalping signals (KuCoin).", ["analyze_market"], 10),
            ("database", "twisterlab.agents.core.db_agent", "DatabaseAgent", "Low-level SQL database interface.", ["db_health", "execute_query"], 10),
            ("market-data", "twisterlab.agents.signals.market_agent", "MarketDataAgent", "Ingests OHLCV and prepares clean market snapshots.", ["get_snapshot"], 10),
            ("pattern-detector", "twisterlab.agents.signals.pattern_agent", "PatternAgent", "Detects technical setups and proposes raw signals.", ["propose_signal"], 10),
            ("signal-filter", "twisterlab.agents.signals.filter_agent", "FilterAgent", "Validates signals and assigns confidence scores.", ["filter_signal"], 10),
            ("meta-signal", "twisterlab.agents.signals.meta_agent", "MetaSignalAgent", "Tranches final BUY/SELL/NO TRADE decisions.", ["decide"], 10)
        ]

        for key, path, cls, desc, caps, prio in registry_data:
            self.register_agent(key, make_factory(path, cls), description=desc, capabilities=caps, priority=prio)

        # Maestro is special
        def maestro_factory():
            from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
            return RealMaestroAgent(agent_registry=self)
        
        self.register_agent("maestro", maestro_factory, description="Master Orchestrator Core.", capabilities=["orchestrate", "analyze_task"], priority=100)

    def register_agent(self, key: str, factory: Callable[[], Any], description: str = "", capabilities: List[str] = None, priority: int = 0):
        """
        Registers a new agent factory with static metadata and priority.
        
        @param priority: The resolution weight for functional discovery. 
                         Higher priority agents win capability collisions.
                         Standard agents default to 10; Master agents default to 20+.
        """
        primary_key = key.lower()
        self._factories[primary_key] = factory
        self._status[primary_key] = AgentStatus.REGISTERED
        self._metadata[primary_key] = {
            "name": primary_key,
            "description": description or f"Agent {primary_key} (Lazy)",
            "primary_key": primary_key,
            "capabilities": capabilities or [],
            "priority": priority
        }
        
        # Populate lookup index
        norm = self._normalize_name(primary_key)
        self._lookup_index[norm] = primary_key
        
        # Add common aliases
        if primary_key.startswith("real-"):
            self._lookup_index[self._normalize_name(primary_key[5:])] = primary_key
        else:
            self._lookup_index[self._normalize_name("real-" + primary_key)] = primary_key
            
        if not primary_key.endswith("agent"):
            self._lookup_index[self._normalize_name(primary_key + "agent")] = primary_key

    def get_agent(self, name: str) -> Optional[Any]:
        """Lazy-instantiates and returns an agent by name or alias."""
        if not name:
            return None
            
        norm_name = self._normalize_name(name)
        primary_key = self._lookup_index.get(norm_name)
        
        if not primary_key:
            return None

        if primary_key in self._instances:
            return self._instances[primary_key]

        with self._lock:
            if primary_key in self._instances:
                return self._instances[primary_key]
                
            factory = self._factories.get(primary_key)
            if not factory:
                return None

            try:
                self._status[primary_key] = AgentStatus.INITIALIZING
                logger.info(f"Lazy-initializing agent: {primary_key}...")
                agent = factory()
                self._instances[primary_key] = agent
                self._status[primary_key] = AgentStatus.ONLINE
                
                # Update registry metrics
                try:
                    from twisterlab.monitoring_utils import update_registry_metrics
                    update_registry_metrics(len(self._instances))
                except ImportError:
                    pass

                # Dynamic metadata verification
                if hasattr(agent, "get_capabilities"):
                    try:
                        agent_caps = [c.name for c in agent.get_capabilities()]
                        existing = self._metadata[primary_key].get("capabilities", [])
                        self._metadata[primary_key]["capabilities"] = list(set(existing + agent_caps))
                    except Exception:
                        pass
                
                return agent
            except Exception as e:
                self._status[primary_key] = AgentStatus.FAILED
                self._errors[primary_key] = str(e)
                logger.error(f"Failed to initialize agent '{primary_key}': {e}", exc_info=True)
                return None

    def find_agent_by_capability(self, capability_name: str) -> Optional[str]:
        """
        Discovery: Returns the primary key of the best agent for a given capability.
        RULE: Highest Priority wins. Lexical order on primary_key if priorities tie.
        """
        if not capability_name:
            return None
            
        candidates = []
        for key, meta in self._metadata.items():
            if capability_name in meta.get("capabilities", []):
                candidates.append((meta.get("priority", 0), key))
        
        best_candidate = None
        if not candidates:
            # Fallback: check if the capability name *is* an agent name / alias
            best_candidate = self._lookup_index.get(self._normalize_name(capability_name))
        else:
            # Sort by: 1. Priority (Descending), 2. Key (Ascending)
            candidates.sort(key=lambda x: (-x[0], x[1]))
            best_candidate = candidates[0][1]
        
        # Telemetry
        try:
            from twisterlab.monitoring_utils import record_resolution
            record_resolution(
                requirement=capability_name, 
                agent=best_candidate or "none", 
                status="success" if best_candidate else "failed"
            )
        except ImportError:
            pass

        if best_candidate:
            logger.debug(f"Resolved capability '{capability_name}' to '{best_candidate}'")
        return best_candidate

    def list_agents(self) -> Dict[str, Dict[str, Any]]:
        """Returns metadata for all registered agents."""
        result = {}
        for key in self._factories.keys():
            meta = self._metadata.get(key, {})
            result[key] = {
                "name": meta.get("name", key),
                "description": meta.get("description", "Registration active"),
                "status": self._status.get(key, AgentStatus.REGISTERED).value,
                "initialized": key in self._instances,
                "error": self._errors.get(key),
                "capabilities": meta.get("capabilities", []),
                "priority": meta.get("priority", 0)
            }
        return result

    def get_registry_status(self) -> Dict[str, Any]:
        """Returns dynamic diagnostic metadata."""
        counts = {s.value: 0 for s in AgentStatus}
        for s in self._status.values():
            counts[s.value] += 1
            
        return {
            "total": len(self._factories),
            "initialized": len(self._instances),
            "status_breakdown": counts,
            "can_orchistrate": "maestro" in self._instances
        }

# Decoupled Provider
_global_registry = None

def get_agent_registry() -> AgentRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry

# Proxy for compatibility
class CompatibilityProxy:
    def __getattr__(self, name):
        return getattr(get_agent_registry(), name)
    def __len__(self):
        return len(get_agent_registry())

agent_registry = CompatibilityProxy()
