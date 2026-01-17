import logging
import threading
from typing import Dict, List, Optional

from twisterlab.agents.base.base_agent import BaseAgent
from twisterlab.agents.real.browser_agent import RealBrowserAgent
from twisterlab.agents.real.real_backup_agent import RealBackupAgent

# Importe les classes d'agents v2 que nous avons refactorisées
from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
from twisterlab.agents.real.real_code_review_agent import RealCodeReviewAgent
from twisterlab.agents.real.real_desktop_commander_agent import (
    RealDesktopCommanderAgent,
)
from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent
from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
from twisterlab.agents.real.real_resolver_agent import RealResolverAgent
from twisterlab.agents.real.real_sentiment_analyzer_agent import (
    SentimentAnalyzerAgent,
)
from twisterlab.agents.real.real_sync_agent import RealSyncAgent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Thread-safe Singleton qui instancie, détient et gère tous les agents actifs du système.
    C'est la source unique de vérité pour l'état des agents.
    
    Features:
    - Thread-safe singleton with double-checked locking
    - Pre-computed lookup indices for O(1) agent retrieval
    - Lifecycle management (start/shutdown hooks)
    - Observability via logging
    """

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern for thread safety
                if cls._instance is None:
                    cls._instance = super(AgentRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Prevent re-initialization in singleton
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._agents: Dict[str, BaseAgent] = {}
        self._agents_by_id: Dict[str, BaseAgent] = {}
        self._lookup_index: Dict[str, BaseAgent] = {}  # Pre-computed normalized keys
        self._agent_list: List[BaseAgent] = []  # Ordered list for iteration
        
        self.initialize_agents()

    def initialize_agents(self):
        """Instancie tous les agents v2 au démarrage de l'API."""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        with self._lock:
            if hasattr(self, '_initialized') and self._initialized:
                return
                
            try:
                # Create all agents
                agents_list = [
                    RealClassifierAgent(),
                    RealResolverAgent(),
                    RealMonitoringAgent(),
                    RealBackupAgent(),
                    RealSyncAgent(),
                    RealDesktopCommanderAgent(),
                    RealBrowserAgent(),
                    SentimentAnalyzerAgent(),
                    RealCodeReviewAgent(),
                ]
                
                # Maestro needs registry reference for cross-agent communication
                maestro = RealMaestroAgent(agent_registry=self)
                agents_list.append(maestro)
                
                # Build lookup indices
                self._agents = {}
                self._agents_by_id = {}
                self._lookup_index = {}
                self._agent_list = agents_list
                
                for agent in agents_list:
                    key = agent.name.lower()
                    self._agents[key] = agent
                    
                    # Agent ID lookup (if available)
                    agent_id = getattr(agent, 'agent_id', None)
                    if agent_id:
                        self._agents_by_id[agent_id] = agent
                    
                    # Pre-compute normalized keys for fast lookup
                    self._add_lookup_keys(agent, key)
                
                self._initialized = True
                logger.info(f"Agent Registry initialized with {len(agents_list)} agents.")
                print(f"Agent Registry initialized with {len(agents_list)} agents.")
                
            except Exception as e:
                logger.error(f"Failed to initialize agents: {e}", exc_info=True)
                raise

    def _add_lookup_keys(self, agent: BaseAgent, primary_key: str):
        """Pre-compute multiple lookup keys for an agent."""
        # Primary key
        self._lookup_index[primary_key] = agent
        
        # Without hyphens/underscores
        normalized = primary_key.replace("-", "").replace("_", "")
        self._lookup_index[normalized] = agent
        
        # Without 'agent' suffix
        if normalized.endswith("agent"):
            self._lookup_index[normalized[:-5]] = agent
        
        # With 'real' prefix variations
        if primary_key.startswith("real-"):
            self._lookup_index[primary_key[5:]] = agent  # Without 'real-'
        
        # Agent ID as key (if available)
        agent_id = getattr(agent, 'agent_id', None)
        if agent_id:
            self._lookup_index[agent_id] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """
        Récupère une instance d'agent par son nom.
        
        Supports multiple naming conventions:
        - Exact match: "real-classifier"
        - Normalized: "realclassifier", "classifier"
        - Agent ID lookup
        """
        if not name:
            logger.warning("get_agent called with empty name")
            return None
        
        key = name.lower()
        
        # Fast O(1) lookup via pre-computed index
        agent = self._lookup_index.get(key)
        if agent:
            return agent
        
        # Fallback: try normalized key
        normalized = key.replace("-", "").replace("_", "")
        agent = self._lookup_index.get(normalized)
        if agent:
            return agent
        
        # Last resort: substring match (for fuzzy lookups like 'monitor' -> 'monitoring')
        for registered_agent in self._agent_list:
            rn = (registered_agent.name or "").lower()
            if key in rn or rn in key:
                logger.debug(f"Fuzzy match: '{name}' -> '{registered_agent.name}'")
                return registered_agent
        
        logger.warning(f"Agent not found: '{name}'. Available: {list(self._agents.keys())}")
        return None

    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        """Récupère un agent par son ID unique."""
        return self._agents_by_id.get(agent_id)

    def list_agents(self) -> Dict[str, Dict]:
        """Retourne le statut réel et les métadonnées de tous les agents."""
        try:
            result = {}
            for name, agent in self._agents.items():
                status = getattr(agent, 'status', None)
                result[name] = {
                    "agent_id": getattr(agent, 'agent_id', name),
                    "name": getattr(agent, 'name', name),
                    "version": getattr(agent, 'version', "1.0.0"),
                    "description": getattr(agent, 'description', ""),
                    "status": status.value if status else "active",
                }
            return result
        except Exception as e:
            logger.error(f"Error listing agents: {e}", exc_info=True)
            raise

    def get_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Find agents that have a specific capability."""
        result = []
        for agent in self._agent_list:
            if hasattr(agent, 'get_capabilities'):
                caps = agent.get_capabilities()
                if any(c.name == capability for c in caps):
                    result.append(agent)
            elif hasattr(agent, 'list_capabilities'):
                caps = agent.list_capabilities()
                if any(c.get('name') == capability for c in caps):
                    result.append(agent)
        return result

    async def start_all_agents(self):
        """Start all registered agents (lifecycle hook)."""
        logger.info("Starting all agents...")
        for agent in self._agent_list:
            if hasattr(agent, 'start'):
                try:
                    await agent.start()
                    logger.info(f"Started agent: {agent.name}")
                except Exception as e:
                    logger.error(f"Failed to start agent {agent.name}: {e}")

    async def shutdown_all_agents(self):
        """Gracefully shutdown all agents (lifecycle hook)."""
        logger.info("Shutting down all agents...")
        for agent in self._agent_list:
            if hasattr(agent, 'shutdown'):
                try:
                    await agent.shutdown()
                    logger.info(f"Shutdown agent: {agent.name}")
                except Exception as e:
                    logger.error(f"Failed to shutdown agent {agent.name}: {e}")

    def health_check(self) -> Dict[str, bool]:
        """Check health status of all agents (sync version)."""
        health = {}
        for agent in self._agent_list:
            try:
                # Check status attribute if available
                status = getattr(agent, 'status', None)
                if status:
                    health[agent.name] = status.value in ("active", "idle", "ready")
                else:
                    health[agent.name] = True  # Assume healthy if no status
            except Exception as e:
                logger.error(f"Health check failed for {agent.name}: {e}")
                health[agent.name] = False
        return health

    async def health_check_async(self) -> Dict[str, bool]:
        """Check health status of all agents (async version)."""
        health = {}
        for agent in self._agent_list:
            try:
                if hasattr(agent, 'health_check'):
                    result = agent.health_check()
                    # Handle both sync and async health_check methods
                    if hasattr(result, '__await__'):
                        health[agent.name] = await result
                    else:
                        health[agent.name] = result
                else:
                    status = getattr(agent, 'status', None)
                    health[agent.name] = status.value in ("active", "idle", "ready") if status else True
            except Exception as e:
                logger.error(f"Health check failed for {agent.name}: {e}")
                health[agent.name] = False
        return health

    @property
    def agent_count(self) -> int:
        """Return the number of registered agents."""
        return len(self._agent_list)

    def __len__(self) -> int:
        return self.agent_count

    def __iter__(self):
        return iter(self._agent_list)


# Instance unique du registre, prête à être importée
agent_registry = AgentRegistry()
