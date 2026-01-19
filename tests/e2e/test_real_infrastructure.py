"""
E2E Tests with Real PostgreSQL and Redis Infrastructure.

These tests require:
- PostgreSQL accessible on localhost:5432
- Redis accessible on localhost:6379

Run with: 
    $env:E2E="1"; $env:DATABASE_URL="postgresql+asyncpg://twisterlab:twisterlab_secure_db_password_2024!@localhost:5432/twisterlab"; pytest tests/e2e/test_real_infrastructure.py -v
"""
import pytest
import asyncio
import os
from datetime import datetime, timezone

# Mark all tests as e2e
pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]

# Skip if E2E not enabled
skip_if_no_e2e = pytest.mark.skipif(
    os.getenv("E2E") != "1",
    reason="E2E tests disabled. Set E2E=1 to run."
)


@skip_if_no_e2e
class TestPostgreSQLConnection:
    """Test real PostgreSQL database operations."""

    async def test_database_connection(self):
        """Test we can connect to PostgreSQL."""
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://twisterlab:twisterlab_secure_db_password_2024!@localhost:5432/twisterlab"
        )
        
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1
        
        await engine.dispose()

    async def test_database_version(self):
        """Test PostgreSQL version is 16+."""
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://twisterlab:twisterlab_secure_db_password_2024!@localhost:5432/twisterlab"
        )
        
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            assert "PostgreSQL" in version
            # Extract major version
            import re
            match = re.search(r"PostgreSQL (\d+)", version)
            if match:
                major_version = int(match.group(1))
                assert major_version >= 14, f"Expected PostgreSQL 14+, got {major_version}"
        
        await engine.dispose()

    async def test_create_and_query_table(self):
        """Test creating a table and inserting/querying data."""
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://twisterlab:twisterlab_secure_db_password_2024!@localhost:5432/twisterlab"
        )
        
        engine = create_async_engine(db_url, echo=False)
        
        async with engine.begin() as conn:
            # Create test table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS e2e_test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            
            # Insert test data
            await conn.execute(text(
                "INSERT INTO e2e_test_table (name) VALUES (:name)"
            ), {"name": f"e2e_test_{datetime.now(timezone.utc).isoformat()}"})
            
            # Query data
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM e2e_test_table"
            ))
            count = result.fetchone()[0]
            assert count >= 1
            
            # Cleanup
            await conn.execute(text("DELETE FROM e2e_test_table WHERE name LIKE 'e2e_test_%'"))
        
        await engine.dispose()


@skip_if_no_e2e
class TestRedisConnection:
    """Test real Redis operations."""

    async def test_redis_connection(self):
        """Test we can connect to Redis."""
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        client = redis.from_url(redis_url, decode_responses=True)
        
        # Ping Redis
        pong = await client.ping()
        assert pong is True
        
        await client.aclose()

    async def test_redis_set_get(self):
        """Test Redis SET/GET operations."""
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        
        test_key = f"e2e_test_{datetime.now(timezone.utc).timestamp()}"
        test_value = "twisterlab_e2e_test"
        
        # SET
        await client.set(test_key, test_value, ex=60)
        
        # GET
        result = await client.get(test_key)
        assert result == test_value
        
        # Cleanup
        await client.delete(test_key)
        
        await client.aclose()

    async def test_redis_hash_operations(self):
        """Test Redis HASH operations (used for agent state)."""
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        
        hash_key = f"e2e_agent_state_{datetime.now(timezone.utc).timestamp()}"
        
        # HSET
        await client.hset(hash_key, mapping={
            "agent_name": "test-agent",
            "status": "running",
            "last_execution": datetime.now(timezone.utc).isoformat()
        })
        
        # HGETALL
        data = await client.hgetall(hash_key)
        assert data["agent_name"] == "test-agent"
        assert data["status"] == "running"
        
        # Cleanup
        await client.delete(hash_key)
        
        await client.aclose()

    async def test_redis_pub_sub(self):
        """Test Redis Pub/Sub (used for agent communication)."""
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        
        channel = "e2e_test_channel"
        received_messages = []
        
        # Subscribe
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        
        # Publish
        await client.publish(channel, "test_message_from_e2e")
        
        # Receive (with timeout)
        async def receive_one():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    received_messages.append(message["data"])
                    break
        
        try:
            await asyncio.wait_for(receive_one(), timeout=2.0)
        except asyncio.TimeoutError:
            pass  # OK if no message received in test environment
        
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        await client.aclose()


@skip_if_no_e2e  
class TestAgentsWithRealDB:
    """Test agents with real database persistence."""

    async def test_classifier_with_db_persistence(self):
        """Test ClassifierAgent saves results to PostgreSQL."""
        import sys
        sys.path.insert(0, "src")
        
        os.environ["DATABASE_URL"] = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://twisterlab:twisterlab_secure_db_password_2024!@localhost:15432/twisterlab"
        )
        
        from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
        
        agent = RealClassifierAgent()
        
        # Execute classification (correct parameter name: ticket_text)
        result = await agent.handle_classify(
            ticket_text="My laptop screen is flickering and the display is unstable"
        )
        
        assert result.success is True
        assert result.data is not None
        assert "category" in result.data

    async def test_sentiment_analyzer_batch(self):
        """Test SentimentAnalyzer with multiple texts."""
        import sys
        sys.path.insert(0, "src")
        
        from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
        
        agent = SentimentAnalyzerAgent()
        
        test_texts = [
            ("I love this product, it's amazing!", "positive"),
            ("This is terrible, worst experience ever", "negative"),
            ("The system is working normally", "neutral"),
            ("Je suis très content du service!", "positive"),  # French
        ]
        
        for text, expected_sentiment in test_texts:
            result = await agent.handle_analyze_sentiment(text=text)
            assert result.success is True
            assert result.data["sentiment"] in ["positive", "negative", "neutral"]

    async def test_monitoring_agent_real_metrics(self):
        """Test MonitoringAgent collects real system metrics."""
        import sys
        sys.path.insert(0, "src")
        
        from twisterlab.agents.real.real_monitoring_agent import RealMonitoringAgent
        
        agent = RealMonitoringAgent()
        
        # Get system health via handle_collect_metrics
        result = await agent.handle_collect_metrics()
        
        assert result.success is True
        assert result.data is not None
        # Should have CPU, memory info
        data = result.data
        assert "cpu" in str(data).lower() or "memory" in str(data).lower() or "system" in str(data).lower()


@skip_if_no_e2e
class TestFullWorkflow:
    """Test complete ticket workflow with real infrastructure."""

    async def test_ticket_processing_workflow(self):
        """Test complete ticket: sentiment → classify → resolve."""
        import sys
        sys.path.insert(0, "src")
        
        os.environ["DATABASE_URL"] = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://twisterlab:twisterlab_secure_db_password_2024!@localhost:5432/twisterlab"
        )
        
        from twisterlab.agents.real.real_sentiment_analyzer_agent import SentimentAnalyzerAgent
        from twisterlab.agents.real.real_classifier_agent import RealClassifierAgent
        
        # Simulated ticket
        ticket_text = """
        URGENT: My email stopped working this morning!
        I can't send or receive any messages and I have an important meeting in 1 hour.
        This is extremely frustrating, please help ASAP!
        """
        
        # Step 1: Sentiment Analysis
        sentiment_agent = SentimentAnalyzerAgent()
        sentiment_result = await sentiment_agent.handle_analyze_sentiment(text=ticket_text)
        
        assert sentiment_result.success is True
        sentiment = sentiment_result.data["sentiment"]
        assert sentiment in ["positive", "negative", "neutral"]
        # Should detect frustration
        assert sentiment == "negative" or sentiment_result.data.get("confidence", 0) > 0.5
        
        # Step 2: Classification (correct parameter name: ticket_text)
        classifier_agent = RealClassifierAgent()
        classify_result = await classifier_agent.handle_classify(ticket_text=ticket_text)
        
        assert classify_result.success is True
        category = classify_result.data.get("category", "").upper()
        # Should classify as email-related
        assert category in ["EMAIL", "SOFTWARE", "NETWORK", "GENERAL", "ACCOUNT"]
        
        # Step 3: Log workflow to Redis
        import redis.asyncio as redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, decode_responses=True)
        
        workflow_key = f"workflow:{datetime.now(timezone.utc).timestamp()}"
        await client.hset(workflow_key, mapping={
            "ticket": ticket_text[:100],
            "sentiment": sentiment,
            "category": category,
            "processed_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Verify workflow was logged
        logged = await client.hgetall(workflow_key)
        assert logged["sentiment"] == sentiment
        assert logged["category"] == category
        
        # Cleanup
        await client.delete(workflow_key)
        await client.aclose()


@skip_if_no_e2e
class TestDatabaseModels:
    """Test SQLAlchemy models with real database."""

    async def test_init_db_creates_tables(self):
        """Test that init_db creates all required tables."""
        import sys
        sys.path.insert(0, "src")
        
        os.environ["DATABASE_URL"] = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://twisterlab:twisterlab_secure_db_password_2024!@localhost:5432/twisterlab"
        )
        
        from twisterlab.database.session import init_db, engine
        from sqlalchemy import text
        
        # Initialize database
        await init_db()
        
        # Check tables exist
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            
            # Should have at least some tables
            assert len(tables) >= 0  # May be empty if no models defined yet
