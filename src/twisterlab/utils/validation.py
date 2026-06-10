import os
import logging

logger = logging.getLogger("twisterlab.validation")

def validate_environment():
    """
    Validates critical environment variables required for the platform to function.
    """
    required_vars = [
        "INFRA__NOTION_TOKEN",
        "INFRA__OLLAMA_BASE_URL"
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
            
    if missing:
        logger.warning(f"🚨 CRITICAL CONFIG MISSING: {', '.join(missing)}")
        logger.warning("Maestro might fail to orchestrate missions or report to Notion.")
        return False
        
    logger.info("✅ Environment validation successful. All critical secrets found.")
    return True
