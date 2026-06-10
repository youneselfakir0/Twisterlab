import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone
import json

from twisterlab.database.session import init_db, AsyncSessionLocal
from twisterlab.database.models.learning import Skill, AgentMemory, ScheduledTask, UserProfile
from twisterlab.services.learning import (
    MemoryService,
    LearningService,
    UserProfileService,
    SchedulerService,
    calculate_next_run,
    matches_cron
)

@pytest.fixture(autouse=True)
async def setup_database():
    # Initialize the database and create tables
    await init_db()
    # Clean tables before each test
    async with AsyncSessionLocal() as session:
        from sqlalchemy import delete
        await session.execute(delete(Skill))
        await session.execute(delete(AgentMemory))
        await session.execute(delete(ScheduledTask))
        await session.execute(delete(UserProfile))
        await session.commit()

@pytest.mark.asyncio
async def test_memory_service_save_and_search():
    # Mock LLM generation
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "Test summary for memory query."
    
    with patch("twisterlab.services.learning.get_service_registry") as mock_registry:
        mock_registry.return_value.get_llm.return_value = mock_llm
        
        # Save memory
        memory = await MemoryService.save_memory(
            task_description="Check database stats on server",
            execution_results=[{"step": 1, "agent": "classifier", "status": "success"}],
            session_id="test_session_1"
        )
        
        assert memory.id is not None
        assert memory.task_description == "Check database stats on server"
        assert memory.summary == "Test summary for memory query."
        
        # Search memories
        results = await MemoryService.search_memories("database")
        assert len(results) >= 1
        assert results[0].task_description == "Check database stats on server"

@pytest.mark.asyncio
async def test_learning_service_extract_and_match():
    # Mock LLM response for skill extraction
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = json.dumps({
        "id": "db_stats_skill",
        "name": "Database Stats Fetcher",
        "description": "Fetch status from DB",
        "trigger_keywords": ["database", "stats"],
        "steps": [
            {
                "order": 1,
                "agent": "real-desktop-commander",
                "capability": "execute_command",
                "params": {"command": "pg_stat_activity"},
                "purpose": "Check active queries"
            }
        ]
    })
    
    with patch("twisterlab.services.learning.get_service_registry") as mock_registry:
        mock_registry.return_value.get_llm.return_value = mock_llm
        
        execution_results = [
            {"step": 1, "agent": "sentiment-analyzer", "status": "success"},
            {"step": 2, "agent": "real-desktop-commander", "status": "success"}
        ]
        
        skill = await LearningService.extract_and_save_skill(
            task_description="Fetch database stats info",
            execution_results=execution_results
        )
        
        assert skill is not None
        assert skill.id == "db_stats_skill"
        assert skill.name == "Database Stats Fetcher"
        
        # Match skill
        matched = await LearningService.find_matching_skill("Can you query database stats?")
        assert matched is not None
        assert matched.id == "db_stats_skill"

@pytest.mark.asyncio
async def test_user_profile_refine():
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = json.dumps({
        "verbosity": "concise",
        "auto_approve": ["network"],
        "preferred_agents": {"database": "real-desktop-commander"},
        "rules": ["Always use concise answers"]
    })
    
    with patch("twisterlab.services.learning.get_service_registry") as mock_registry:
        mock_registry.return_value.get_llm.return_value = mock_llm
        
        # Refine profile
        prefs = await UserProfileService.refine_profile_from_interaction(
            user_message="Make your replies concise please",
            agent_response="Sure thing!"
        )
        
        assert prefs["verbosity"] == "concise"
        assert "Always use concise answers" in prefs["rules"]

@pytest.mark.asyncio
async def test_scheduler_service():
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = json.dumps({
        "description": "Network ping every 5 minutes",
        "cron_expression": "*/5 * * * *",
        "task_payload": "Perform a ping to edge router"
    })
    
    with patch("twisterlab.services.learning.get_service_registry") as mock_registry:
        mock_registry.return_value.get_llm.return_value = mock_llm
        
        task = await SchedulerService.parse_and_schedule("Ping router every 5 minutes")
        assert task is not None
        assert task.cron_expression == "*/5 * * * *"
        assert task.next_run_at is not None
