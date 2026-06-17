from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging
import os
import json

from twisterlab.agents.registry import get_agent_registry
from twisterlab.api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

MISSION_DIR = "/app/archives/missions"
FALLBACK_DIR = "data/missions"

def get_mission_dir():
    if os.path.exists(MISSION_DIR):
        return MISSION_DIR
    return FALLBACK_DIR

@router.get("/missions")
async def list_missions():
    """List all mission traces from disk."""
    try:
        missions = []
        mission_dir = get_mission_dir()
        if not os.path.exists(mission_dir):
            return {"missions": []}
            
        for filename in os.listdir(mission_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(mission_dir, filename), "r") as f:
                        data = json.load(f)
                        missions.append({
                            "id": data.get("task_id"),
                            "task": data.get("description", "Unknown"),
                            "status": data.get("status"),
                            "completed_at": data.get("completed_at"),
                            "summary": data.get("synthesis", {}).get("summary", "No summary"),
                            "category": data.get("analysis", {}).get("category"),
                            "priority": data.get("analysis", {}).get("priority"),
                        })
                except Exception as e:
                    logger.warning(f"Error reading mission file {filename}: {e}")
                    
        # Sort by completion time (newest first)
        missions.sort(key=lambda x: x.get("completed_at") or "", reverse=True)
        return {"missions": missions}
    except Exception as e:
        logger.error(f"Failed to list missions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/missions/{mission_id}")
async def get_mission_detail(mission_id: str):
    """Get full detail of a specific mission trace."""
    mission_dir = get_mission_dir()
    file_path = os.path.join(mission_dir, f"{mission_id}.json")
    if not os.path.exists(file_path):
        # Check fallback
        file_path = os.path.join(FALLBACK_DIR, f"{mission_id}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Mission not found")
        
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read mission {mission_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
