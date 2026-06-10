from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete

from twisterlab.database.session import AsyncSessionLocal
from twisterlab.database.models.learning import Skill as SkillModel, AgentMemory, ScheduledTask, UserProfile
from twisterlab.services.learning import MemoryService, LearningService, UserProfileService, SchedulerService, calculate_next_run

logger = logging.getLogger(__name__)
router = APIRouter()

# =========================================================================
# SCHEMAS
# =========================================================================

class MemoryResponseSchema(BaseModel):
    id: int
    session_id: Optional[str]
    task_description: str
    summary: str
    details: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class SkillCreateSchema(BaseModel):
    id: str
    name: str
    description: str
    trigger_keywords: Optional[str] = None
    steps: List[Dict[str, Any]]

class SkillResponseSchema(BaseModel):
    id: str
    name: str
    description: str
    trigger_keywords: Optional[str]
    steps: List[Dict[str, Any]]
    success_count: int
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScheduleRequestSchema(BaseModel):
    prompt: str

class ScheduledTaskResponseSchema(BaseModel):
    id: str
    description: str
    cron_expression: str
    task_payload: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class ProfileUpdateSchema(BaseModel):
    preferences: Dict[str, Any]

# =========================================================================
# ENDPOINTS: MEMORY
# =========================================================================

@router.get("/memories", response_model=List[MemoryResponseSchema])
async def get_memories(q: Optional[str] = Query(None, description="Search term for FTS memories search")):
    """Get all agent memories, with optional Full-Text Search (FTS) query filtering."""
    try:
        if q:
            memories = await MemoryService.search_memories(q)
            return memories
        else:
            async with AsyncSessionLocal() as db:
                stmt = select(AgentMemory).order_by(AgentMemory.created_at.desc()).limit(50)
                result = await db.execute(stmt)
                return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error fetching memories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# ENDPOINTS: SKILLS
# =========================================================================

@router.get("/skills", response_model=List[SkillResponseSchema])
async def get_skills():
    """Get all auto-generated and manual skills."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(SkillModel).order_by(SkillModel.created_at.desc())
            result = await db.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error fetching skills: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/skills", response_model=SkillResponseSchema)
async def create_skill(skill_in: SkillCreateSchema):
    """Manually add or update a skill in the registry."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(SkillModel).where(SkillModel.id == skill_in.id)
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if existing:
                existing.name = skill_in.name
                existing.description = skill_in.description
                existing.trigger_keywords = skill_in.trigger_keywords
                existing.steps = skill_in.steps
                existing.updated_at = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(existing)
                return existing
            else:
                new_skill = SkillModel(
                    id=skill_in.id,
                    name=skill_in.name,
                    description=skill_in.description,
                    trigger_keywords=skill_in.trigger_keywords,
                    steps=skill_in.steps,
                    success_count=0,
                    usage_count=0
                )
                db.add(new_skill)
                await db.commit()
                await db.refresh(new_skill)
                return new_skill
    except Exception as e:
        logger.error(f"Error saving skill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/skills/{skill_id}")
async def delete_skill(skill_id: str):
    """Delete a skill from the registry."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(SkillModel).where(SkillModel.id == skill_id))
            await db.commit()
            return {"status": "success", "message": f"Skill '{skill_id}' deleted."}
    except Exception as e:
        logger.error(f"Error deleting skill: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# ENDPOINTS: SCHEDULER
# =========================================================================

@router.get("/scheduler", response_model=List[ScheduledTaskResponseSchema])
async def get_scheduled_tasks():
    """List all scheduled tasks."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(ScheduledTask).order_by(ScheduledTask.created_at.desc())
            result = await db.execute(stmt)
            return list(result.scalars().all())
    except Exception as e:
        logger.error(f"Error fetching scheduled tasks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler", response_model=ScheduledTaskResponseSchema)
async def schedule_task(request: ScheduleRequestSchema):
    """Schedule a recurring task using natural language prompt (e.g., 'every 5 minutes run database health check')."""
    try:
        task = await SchedulerService.parse_and_schedule(request.prompt)
        if not task:
            raise HTTPException(status_code=400, detail="Failed to parse natural language scheduling prompt.")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/{task_id}/trigger")
async def trigger_scheduled_task(task_id: str):
    """Manually trigger the execution of a scheduled task right now."""
    try:
        await SchedulerService.trigger_task(task_id)
        return {"status": "success", "message": f"Task '{task_id}' triggered successfully."}
    except Exception as e:
        logger.error(f"Error triggering task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/scheduler/{task_id}")
async def delete_scheduled_task(task_id: str):
    """Delete/cancel a scheduled task."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(ScheduledTask).where(ScheduledTask.id == task_id))
            await db.commit()
            return {"status": "success", "message": f"Scheduled task '{task_id}' deleted."}
    except Exception as e:
        logger.error(f"Error deleting scheduled task: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================================
# ENDPOINTS: USER PROFILE & PREFERENCES
# =========================================================================

@router.get("/profile")
async def get_profile():
    """Retrieve current user profile preferences."""
    try:
        prefs = await UserProfileService.get_preferences()
        return {"preferences": prefs}
    except Exception as e:
        logger.error(f"Error fetching profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile")
async def update_profile(profile_in: ProfileUpdateSchema):
    """Update user profile preferences directly."""
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(UserProfile).where(UserProfile.id == "default")
            res = await db.execute(stmt)
            profile = res.scalar_one_or_none()
            
            if profile:
                profile.preferences = profile_in.preferences
                profile.updated_at = datetime.now(timezone.utc)
            else:
                profile = UserProfile(id="default", preferences=profile_in.preferences)
                db.add(profile)
            await db.commit()
            return {"status": "success", "preferences": profile.preferences}
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
