import json
import logging
import time
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """
    Custom formatter to output logs in JSON format for production observability.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }
        
        # Include exception info if available
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Include extra attributes if provided via 'extra' param
        if hasattr(record, "extra_data"):
            log_record["extra"] = record.extra_data
            
        return json.dumps(log_record)

def setup_production_logging(level=logging.INFO):
    """
    Configures the root logger to use JSON formatting.
    """
    root_logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    
    # Also silence some verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
