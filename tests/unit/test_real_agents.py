"""
Unit tests for all Real Agents.
Tests the modern TwisterAgent-based implementations.
"""

import pytest
from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
from twisterlab.agents.real.real_resolver_agent import RealResolverAgent
from twisterlab.agents.real.real_backup_agent import RealBackupAgent
from twisterlab.agents.real.real_sync_agent import RealSyncAgent
from twisterlab.agents.real.real_desktop_commander_agent import RealDesktopCommanderAgent
from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
from twisterlab.agents.real.real_maestro_agent import RealMaestroAgent


# Mark all tests as unit tests
pytestmark = pytest.mark.unit


class TestRealClassifierAgent:
    """Test RealClassifierAgent."""

    @pytest.fixture
    def agent(self):
        return RealClassifierAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "real-classifier"
        assert "classif" in agent.description.lower()

    def test_capabilities(self, agent):
        """Test agent has classify_ticket capability."""
        caps = agent.get_capabilities()
        cap_names = [c.name for c in caps]
        assert "classify_ticket" in cap_names

    @pytest.mark.asyncio
    async def test_classify_password_issue(self, agent):
        """Test password issues are classified as ACCESS."""
        response = await agent.handle_classify("I forgot my password")
        assert response.success is True
        assert response.data["category"] == "ACCESS"

    @pytest.mark.asyncio
    async def test_classify_software_issue(self, agent):
        """Test software issues are classified as SOFTWARE."""
        response = await agent.handle_classify("Need to install new software")
        assert response.success is True
        assert response.data["category"] == "SOFTWARE"

    @pytest.mark.asyncio
    async def test_classify_bug_issue(self, agent):
        """Test bugs are classified as TECHNICAL."""
        response = await agent.handle_classify("There is a bug in the system")
        assert response.success is True
        assert response.data["category"] == "TECHNICAL"

    @pytest.mark.asyncio
    async def test_classify_general_issue(self, agent):
        """Test unknown issues are classified as GENERAL."""
        response = await agent.handle_classify("I have a question")
        assert response.success is True
        assert response.data["category"] == "GENERAL"


class TestRealResolverAgent:
    """Test RealResolverAgent."""

    @pytest.fixture
    def agent(self):
        return RealResolverAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "real-resolver"
        assert "resolve" in agent.description.lower()

    def test_capabilities(self, agent):
        """Test agent has resolve_ticket capability."""
        caps = agent.get_capabilities()
        cap_names = [c.name for c in caps]
        assert "resolve_ticket" in cap_names

    @pytest.mark.asyncio
    async def test_resolve_ticket(self, agent):
        """Test ticket resolution."""
        response = await agent.handle_resolve(
            ticket_id="TICKET-123",
            resolution_note="Fixed the issue"
        )
        assert response.success is True
        assert response.data["ticket_id"] == "TICKET-123"
        assert response.data["status"] == "RESOLVED"


class TestRealBackupAgent:
    """Test RealBackupAgent."""

    @pytest.fixture
    def agent(self):
        return RealBackupAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "real-backup"
        assert "backup" in agent.description.lower()

    def test_capabilities(self, agent):
        """Test agent has create_backup capability."""
        caps = agent.get_capabilities()
        cap_names = [c.name for c in caps]
        assert "create_backup" in cap_names

    @pytest.mark.asyncio
    async def test_create_backup(self, agent):
        """Test backup creation."""
        response = await agent.handle_backup(
            service_name="test-service",
            location="cloud"
        )
        assert response.success is True
        assert response.data["service"] == "test-service"
        assert "backup_id" in response.data


class TestRealSyncAgent:
    """Test RealSyncAgent."""

    @pytest.fixture
    def agent(self):
        return RealSyncAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert "sync" in agent.name.lower()

    @pytest.mark.asyncio
    async def test_execute(self, agent):
        """Test sync execution."""
        result = await agent.execute("sync_now")
        assert result is not None
        assert result["status"] == "ok"


class TestRealDesktopCommanderAgent:
    """Test RealDesktopCommanderAgent."""

    @pytest.fixture
    def agent(self):
        return RealDesktopCommanderAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "real-desktop-commander"
        assert "command" in agent.description.lower()

    def test_capabilities(self, agent):
        """Test agent has execute_command capability."""
        caps = agent.get_capabilities()
        cap_names = [c.name for c in caps]
        assert "execute_command" in cap_names

    @pytest.mark.asyncio
    async def test_execute_command(self, agent):
        """Test executing a command."""
        response = await agent.handle_execute_command(
            device_id="local",
            command="echo hello"
        )
        assert response.success is True
        assert response.data["status"] == "completed"
        assert "output" in response.data


class TestRealMonitoringAgent:
    """Test RealMonitoringAgent."""

    @pytest.fixture
    def agent(self):
        return RealMonitoringAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert "monitoring" in agent.name.lower()

    @pytest.mark.asyncio
    async def test_execute(self, agent):
        """Test monitoring execution."""
        result = await agent.execute("health_check")
        assert result is not None
        assert "status" in result or "metrics" in result


class TestRealMaestroAgent:
    """Test RealMaestroAgent."""

    @pytest.fixture
    def agent(self):
        return RealMaestroAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.name == "maestro"
        assert "orchestrat" in agent.description.lower()

    def test_capabilities(self, agent):
        """Test agent has orchestrate capability."""
        caps = agent.get_capabilities()
        cap_names = [c.name for c in caps]
        assert "orchestrate" in cap_names

    @pytest.mark.asyncio
    async def test_analyze_task_database(self, agent):
        """Test task analysis for database issues."""
        result = await agent._analyze_task("Database is slow and queries timeout", {})
        # category is a TaskCategory enum
        assert result["category"].value == "database"

    @pytest.mark.asyncio
    async def test_analyze_task_network(self, agent):
        """Test task analysis for network issues."""
        result = await agent._analyze_task("Network connection timeout on server", {})
        assert result["category"].value == "network"

    @pytest.mark.asyncio
    async def test_analyze_task_infrastructure(self, agent):
        """Test task analysis for infrastructure issues."""
        result = await agent._analyze_task("Server disk full", {})
        assert result["category"].value == "infrastructure"

    @pytest.mark.asyncio
    async def test_create_plan(self, agent):
        """Test plan creation via orchestrate dry_run."""
        # Use the public orchestrate method with dry_run
        response = await agent.handle_orchestrate(
            task="Database slow",
            context={},
            dry_run=True
        )
        plan = response.data.get("plan", {})
        
        assert "agents" in plan
        assert "steps" in plan
        assert len(plan["steps"]) > 0

    @pytest.mark.asyncio
    async def test_orchestrate_dry_run(self, agent):
        """Test orchestration in dry run mode."""
        response = await agent.handle_orchestrate(
            task="Server returning errors",
            context={},
            dry_run=True
        )
        assert response.success is True
        assert response.data["mode"] == "dry_run"
        assert "plan" in response.data
        assert "analysis" in response.data
