"""
Verification Script for Phase 2: AgentRegistry
Validates:
1. Lazy Loading (No instances at start)
2. Initialization on demand
3. Naming normalization/lookup
4. Status tracking
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parents[3]))

from twisterlab.agents.registry import get_agent_registry, AgentStatus

class TestRegistryPhase2(unittest.TestCase):
    def setUp(self):
        self.registry = get_agent_registry()

    def test_lazy_loading(self):
        print("Test: Lazy Loading...")
        status = self.registry.get_registry_status()
        # In a singleton, some other test might have already triggered an init
        # We just want to check that it hasn't initialized EVERYTHING
        self.assertLess(status["initialized"], 5, "Most agents should still be lazy-loaded")
        self.assertGreater(status["total"], 15, "Registry should have registered factories")

    def test_initialization_on_demand(self):
        print("Test: Initialization on demand...")
        agent = self.registry.get_agent("sentiment")
        self.assertIsNotNone(agent, "Should return an agent instance")
        self.assertEqual(agent.name, "sentiment-analyzer")
        
        status = self.registry.get_registry_status()
        self.assertEqual(status["initialized"], 1, "Only one agent should be initialized now")

    def test_naming_normalization(self):
        print("Test: Naming Normalization...")
        # Test various aliases
        a1 = self.registry.get_agent("real-classifier")
        a2 = self.registry.get_agent("classifier")
        a3 = self.registry.get_agent("CLASSIFIER_AGENT")
        
        self.assertIsNotNone(a1)
        self.assertEqual(a1, a2)
        self.assertEqual(a1, a3)

    def test_status_tracking(self):
        print("Test: Status Tracking...")
        metadata = self.registry.list_agents()
        self.assertIn("browser", metadata)
        self.assertEqual(metadata["browser"]["status"], AgentStatus.REGISTERED.value)
        
        # Trigger browser
        self.registry.get_agent("browser")
        metadata = self.registry.list_agents()
        self.assertEqual(metadata["browser"]["status"], AgentStatus.ONLINE.value)

if __name__ == "__main__":
    unittest.main()
