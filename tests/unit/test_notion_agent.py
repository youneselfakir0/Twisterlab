"""
Tests unitaires pour RealNotionAgent
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from twisterlab.agents.real.real_notion_agent import RealNotionAgent

pytestmark = pytest.mark.unit


@pytest.fixture
def agent():
    a = RealNotionAgent()
    a._token = "test-token-123"
    a._default_db_id = "db-parent-id-456"
    return a


@pytest.fixture
def agent_no_token():
    a = RealNotionAgent()
    a._token = ""
    a._default_db_id = ""
    return a


# ── Capabilities ──────────────────────────────────────────────────────────────

class TestNotionAgentMetadata:

    def test_name(self, agent):
        assert agent.name == "notion"

    def test_description(self, agent):
        assert "Notion" in agent.description or "notion" in agent.description.lower()

    def test_capabilities_count(self, agent):
        caps = agent.get_capabilities()
        assert len(caps) == 5

    def test_capability_names(self, agent):
        names = {c.name for c in agent.get_capabilities()}
        assert names == {"create_page", "search_pages", "update_page", "log_mission", "get_page"}


# ── No Token ──────────────────────────────────────────────────────────────────

class TestNotionAgentNoToken:

    @pytest.mark.asyncio
    async def test_create_page_no_token(self, agent_no_token):
        result = await agent_no_token.handle_create_page(title="Test", content="# Hello")
        assert result.success is False
        assert "NOTION_TOKEN" in result.error

    @pytest.mark.asyncio
    async def test_search_no_token(self, agent_no_token):
        result = await agent_no_token.handle_search(query="test")
        assert result.success is False
        assert "NOTION_TOKEN" in result.error

    @pytest.mark.asyncio
    async def test_update_no_token(self, agent_no_token):
        result = await agent_no_token.handle_update_page(page_id="abc", content="content")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_get_page_no_token(self, agent_no_token):
        result = await agent_no_token.handle_get_page(page_id="abc")
        assert result.success is False


# ── Markdown → Blocks ────────────────────────────────────────────────────────

class TestMarkdownToBlocks:

    def test_h1_block(self, agent):
        blocks = agent._markdown_to_blocks("# Titre principal")
        assert len(blocks) == 1
        assert blocks[0]["type"] == "heading_1"

    def test_h2_block(self, agent):
        blocks = agent._markdown_to_blocks("## Sous-titre")
        assert blocks[0]["type"] == "heading_2"

    def test_h3_block(self, agent):
        blocks = agent._markdown_to_blocks("### Section")
        assert blocks[0]["type"] == "heading_3"

    def test_bullet_block(self, agent):
        blocks = agent._markdown_to_blocks("- Item 1")
        assert blocks[0]["type"] == "bulleted_list_item"
        text = blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        assert text == "Item 1"

    def test_paragraph_block(self, agent):
        blocks = agent._markdown_to_blocks("Texte normal")
        assert blocks[0]["type"] == "paragraph"

    def test_divider_block(self, agent):
        blocks = agent._markdown_to_blocks("---")
        assert blocks[0]["type"] == "divider"

    def test_empty_lines_skipped(self, agent):
        blocks = agent._markdown_to_blocks("# Titre\n\n\nParagraphe")
        assert len(blocks) == 2  # Titres + paragraphe, lignes vides ignorées

    def test_complex_markdown(self, agent):
        md = "# Mission\n\n## Findings\n\n- Finding 1\n- Finding 2\n\n---\nConclusion"
        blocks = agent._markdown_to_blocks(md)
        types = [b["type"] for b in blocks]
        assert "heading_1" in types
        assert "heading_2" in types
        assert "bulleted_list_item" in types
        assert "divider" in types
        assert "paragraph" in types


# ── Build Page Payload ────────────────────────────────────────────────────────

class TestBuildPagePayload:

    def test_page_parent(self, agent):
        payload = agent._build_page_payload("Title", "page-id-123", [], is_database=False)
        assert payload["parent"] == {"page_id": "page-id-123"}
        assert "title" in payload["properties"]

    def test_database_parent(self, agent):
        payload = agent._build_page_payload("Title", "db-id-456", [], is_database=True)
        assert payload["parent"] == {"database_id": "db-id-456"}
        assert "Name" in payload["properties"]


# ── API Calls (mocked) ────────────────────────────────────────────────────────

class TestNotionAPIIntegration:

    @pytest.mark.asyncio
    async def test_create_page_success(self, agent):
        mock_response = {
            "id": "page-id-abc123",
            "url": "https://notion.so/page-abc123",
        }
        with patch.object(agent, "_notion_request", new=AsyncMock(return_value=mock_response)):
            result = await agent.handle_create_page(
                title="Test Mission",
                content="## Contexte\nTest content",
            )
        assert result.success is True
        assert result.data["page_id"] == "page-id-abc123"
        assert result.data["url"] == "https://notion.so/page-abc123"
        assert result.data["title"] == "Test Mission"

    @pytest.mark.asyncio
    async def test_search_success(self, agent):
        mock_response = {
            "results": [
                {
                    "id": "page-123",
                    "url": "https://notion.so/page-123",
                    "created_time": "2026-04-15T00:00:00.000Z",
                    "last_edited_time": "2026-04-15T00:00:00.000Z",
                    "properties": {
                        "title": [{"plain_text": "Mon page"}]
                    },
                }
            ]
        }
        with patch.object(agent, "_notion_request", new=AsyncMock(return_value=mock_response)):
            result = await agent.handle_search(query="test", limit=5)
        assert result.success is True
        assert result.data["count"] == 1
        assert result.data["query"] == "test"

    @pytest.mark.asyncio
    async def test_update_page_success(self, agent):
        mock_response = {"object": "list"}
        with patch.object(agent, "_notion_request", new=AsyncMock(return_value=mock_response)):
            result = await agent.handle_update_page(
                page_id="page-abc", content="## Update\n- New finding"
            )
        assert result.success is True
        assert result.data["page_id"] == "page-abc"
        assert result.data["blocks_added"] >= 1

    @pytest.mark.asyncio
    async def test_get_page_success(self, agent):
        mock_response = {
            "id": "page-xyz",
            "url": "https://notion.so/page-xyz",
            "created_time": "2026-04-15T00:00:00.000Z",
            "last_edited_time": "2026-04-15T00:00:00.000Z",
            "archived": False,
            "properties": {
                "title": [{"plain_text": "Ma Super Page"}]
            },
        }
        with patch.object(agent, "_notion_request", new=AsyncMock(return_value=mock_response)):
            result = await agent.handle_get_page(page_id="page-xyz")
        assert result.success is True
        assert result.data["page_id"] == "page-xyz"
        assert result.data["archived"] is False

    @pytest.mark.asyncio
    async def test_create_page_api_error(self, agent):
        with patch.object(
            agent,
            "_notion_request",
            new=AsyncMock(side_effect=RuntimeError("Notion API Error 403: Unauthorized")),
        ):
            result = await agent.handle_create_page(title="Fail", content="content")
        assert result.success is False
        assert "403" in result.error or "Unauthorized" in result.error


# ── Log Mission ───────────────────────────────────────────────────────────────

class TestLogMission:

    @pytest.mark.asyncio
    async def test_log_mission_creates_page(self, agent):
        mock_response = {"id": "mission-page-id", "url": "https://notion.so/mission"}
        with patch.object(agent, "_notion_request", new=AsyncMock(return_value=mock_response)):
            result = await agent.handle_log_mission(
                mission_id="M-20260415-042",
                task="Application web ne répond plus",
                status="completed",
                findings=["Nginx KO", "HTTP 502"],
                resolution="Nginx redémarré",
                agents_used=["monitoring", "browser", "real-desktop-commander"],
            )
        assert result.success is True
        assert result.data["page_id"] == "mission-page-id"

    @pytest.mark.asyncio
    async def test_log_mission_title_format(self, agent):
        """Le titre doit contenir le mission_id."""
        captured_title = []

        async def mock_create(title, content, parent_id=None, tags=None):
            captured_title.append(title)
            from twisterlab.agents.core.base import AgentResponse
            return AgentResponse(success=True, data={"page_id": "x", "url": "y", "title": title, "blocks_created": 1, "parent_id": "p"})

        with patch.object(agent, "handle_create_page", new=mock_create):
            await agent.handle_log_mission(
                mission_id="M-20260415-999",
                task="Test task",
            )
        assert "M-20260415-999" in captured_title[0]

    @pytest.mark.asyncio
    async def test_log_mission_long_task_truncated(self, agent):
        """Les longs titres doivent être tronqués."""
        long_task = "A" * 200
        captured_title = []

        async def mock_create(title, content, parent_id=None, tags=None):
            captured_title.append(title)
            from twisterlab.agents.core.base import AgentResponse
            return AgentResponse(success=True, data={"page_id": "x", "url": "y", "title": title, "blocks_created": 1, "parent_id": "p"})

        with patch.object(agent, "handle_create_page", new=mock_create):
            await agent.handle_log_mission(
                mission_id="M-TEST",
                task=long_task,
            )
        # Le titre complet (avec mission_id) ne doit pas exploser
        assert len(captured_title[0]) < 300
