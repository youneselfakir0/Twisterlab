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
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

# Core agents for database and cache operations
from twisterlab.agents.core.cache_agent import CacheAgent
from twisterlab.agents.core.db_agent import DatabaseAgent


logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Thread-safe Singleton qui instancie, détient et gère tous les agents actifs du système.
    """

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(AgentRegistry, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        # Initialisation via la méthode initialize_agents()
        if not hasattr(self, "_initialized"):
            self._initialized = False

    def initialize_agents(self):
        """Initialise tous les agents s'ils ne le sont pas déjà."""
        with self._lock:
            if self._initialized:
                return
                
            try:
                # Create all agents (Matching Image + Notion)
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
                    RealNotionAgent(),
                    CacheAgent(),
                    DatabaseAgent(),
                ]
                
                # Maestro needs registry reference
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
                    
                    # Agent ID lookup
                    agent_id = getattr(agent, 'agent_id', None)
                    if agent_id:
                        self._agents_by_id[agent_id] = agent
                    
                    # Pre-compute normalized keys
                    self._add_lookup_keys(agent, key)
                
                self._initialized = True
                logger.info(f"Agent Registry initialized with {len(agents_list)} agents.")
                
            except Exception as e:
                logger.error(f"Failed to initialize agents: {e}", exc_info=True)
                raise

    def _add_lookup_keys(self, agent: BaseAgent, primary_key: str):
        """Pre-compute multiple lookup keys for an agent."""
        self._lookup_index[primary_key] = agent
        normalized = primary_key.replace("-", "").replace("_", "")
        self._lookup_index[normalized] = agent
        if normalized.endswith("agent"):
            self._lookup_index[normalized[:-5]] = agent
        if primary_key.startswith("real-"):
            self._lookup_index[primary_key[5:]] = agent
        agent_id = getattr(agent, 'agent_id', None)
        if agent_id:
            self._lookup_index[agent_id] = agent

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        if not name: return None
        key = name.lower()
        agent = self._lookup_index.get(key)
        if agent: return agent
        normalized = key.replace("-", "").replace("_", "")
        agent = self._lookup_index.get(normalized)
        if agent: return agent
        for registered_agent in self._agent_list:
            rn = (registered_agent.name or "").lower()
            if key in rn or rn in key:
                return registered_agent
        return None

    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents_by_id.get(agent_id)

    def list_agents(self) -> Dict[str, Dict]:
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

    def health_check(self) -> Dict[str, bool]:
        health = {}
        for agent in self._agent_list:
            try:
                status = getattr(agent, 'status', None)
                if status:
                    health[agent.name] = status.value in ("active", "idle", "ready")
                else:
                    health[agent.name] = True
            except Exception as e:
                health[agent.name] = False
        return health

    @property
    def agent_count(self) -> int:
        return len(self._agent_list)

    def __iter__(self):
        return iter(self._agent_list)


# Instance unique du registre, prête à être importée
agent_registry = AgentRegistry()
