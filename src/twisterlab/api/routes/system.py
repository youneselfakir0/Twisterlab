import os
import json
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from twisterlab.monitoring_utils import get_metric_values


router = APIRouter()


@router.post("/domain/sync")
async def domain_sync():
    """Trigger the Active Directory synchronization process."""
    try:
        from twisterlab.agents.registry import get_agent_registry
        registry = get_agent_registry()
        sync_agent = registry.get_agent("sync")
        if not sync_agent:
            raise HTTPException(status_code=503, detail="Sync agent not available")
        
        result = await sync_agent.execute("sync_domain")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SettingsUpdate(BaseModel):
    kucoin_api_key: str
    kucoin_secret: str
    kucoin_passphrase: str
    kucoin_is_sandbox: bool
    kucoin_market_type: str


@router.get("/health")
async def health_check():
    import psutil
    import socket
    try:
        disk = psutil.disk_usage("/")
        disk_pct = disk.percent
        disk_used_gb = round(disk.used / (1024 ** 3), 2)
        disk_total_gb = round(disk.total / (1024 ** 3), 2)
    except Exception:
        disk_pct = 0.0
        disk_used_gb = 0.0
        disk_total_gb = 0.0

    return {
        "status": "healthy",
        "hostname": socket.gethostname(),
        "disk": {
            "percent_used": disk_pct,
            "used_gb": disk_used_gb,
            "total_gb": disk_total_gb
        }
    }


@router.get("/status")
async def system_status():
    return {"status": "running", "version": "1.0.0"}


@router.get("/metrics")
async def metrics():
    # returns monitored metrics as JSON mapping metric name to current value
    vals = get_metric_values()
    return {"metrics": vals}


@router.get("/settings")
async def get_settings():
    """Retrieve current settings (masked for security)."""
    try:
        from twisterlab.config.settings import Settings
        settings = Settings()
        
        def mask(s):
            if not s: return ""
            if len(s) <= 8: return "****"
            return s[:4] + "...." + s[-4:]

        return {
            "kucoin_api_key": mask(settings.kucoin_api_key),
            "kucoin_secret": mask(settings.kucoin_secret),
            "kucoin_passphrase": mask(settings.kucoin_passphrase),
            "kucoin_is_sandbox": settings.kucoin_is_sandbox,
            "kucoin_market_type": settings.kucoin_market_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings")
async def update_settings(update: SettingsUpdate):
    """Update settings in .env file."""
    env_path = ".env"
    try:
        # 1. Read existing .env
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        
        # 2. Update lines or append
        updates = {
            "KUCOIN_API_KEY": update.kucoin_api_key,
            "KUCOIN_SECRET": update.kucoin_secret,
            "KUCOIN_PASSPHRASE": update.kucoin_passphrase,
            "KUCOIN_IS_SANDBOX": str(update.kucoin_is_sandbox).lower(),
            "KUCOIN_MARKET_TYPE": update.kucoin_market_type.lower()
        }
        
        new_lines = []
        found_keys = set()
        
        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#"):
                new_lines.append(line)
                continue
            
            key_val = trimmed.split("=", 1)
            if len(key_val) == 2:
                key = key_val[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    found_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Append missing keys
        for key, val in updates.items():
            if key not in found_keys:
                if not new_lines or not new_lines[-1].endswith("\n"):
                    new_lines.append("\n")
                new_lines.append(f"{key}={val}\n")
        
        # 3. Write back to .env
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
            
        return {"status": "success", "message": "Settings updated. Please restart server to apply changes."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update .env: {str(e)}")

