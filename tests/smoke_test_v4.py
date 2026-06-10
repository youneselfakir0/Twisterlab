import asyncio
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("smoke-test")

async def run_smoke_test():
    logger.info("🚀 Starting TwisterLab v4.0.0-stable Smoke Test...")
    errors = []

    # 1. Test Configuration (Sprint A)
    try:
        from twisterlab.config.unified_settings import settings
        logger.info(f"✅ Config: Loaded {settings.core.app_name} (v{settings.core.version})")
    except Exception as e:
        errors.append(f"Config Failure: {e}")

    # 2. Test Database Manager (Sprint B)
    try:
        from twisterlab.database.manager import db_manager
        db_manager.init()
        logger.info("✅ Database: Manager initialized")
    except Exception as e:
        errors.append(f"DB Manager Failure: {e}")

    # 3. Test Agent Registry (Sprint D)
    try:
        from twisterlab.agents.registry import AgentRegistry
        registry = AgentRegistry()
        registry.discover()
        status = registry.get_registry_status()
        logger.info(f"✅ Registry: Discovery active (Found {status['total']} agents)")
    except Exception as e:
        errors.append(f"Registry Failure: {e}")

    # 4. Test PromptLoader (Sprint D)
    try:
        from twisterlab.agents.prompts.loader import PromptLoader
        # Note: planning.jinja2 content starts with "Tu es le Master Orchestrator..."
        rendered = PromptLoader.render("maestro/planning", {"task": "test", "agents": []})
        if "Master Orchestrator" in rendered or "Analyze" in rendered:
            logger.info("✅ Prompts: Rendering operational")
        else:
            errors.append(f"Prompt Failure: Content mismatch (Got: {rendered[:20]}...)")
    except Exception as e:
        errors.append(f"Prompt Loader Failure: {e}")

    if not errors:
        logger.info("🏆 ALL SYSTEMS OPERATIONAL. Phase 21 Validation PASSED.")
        return True
    else:
        logger.error("❌ Smoke Test FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_smoke_test())
    sys.exit(0 if success else 1)
