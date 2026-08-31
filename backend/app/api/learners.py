"""Learner CRUD API endpoints."""

import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Learner
from app.schemas.schemas import LearnerCreate, LearnerUpdate, LearnerResponse
from app.ai.profile_extraction import extract_profile

router = APIRouter(prefix="/api/learners", tags=["learners"])
logger = logging.getLogger(__name__)


def _serialize_learner(learner: Learner) -> dict:
    """Convert learner model to dict with proper JSON field parsing."""
    d = {
        "id": learner.id,
        "name": learner.name,
        "email": learner.email,
        "career_goal": learner.career_goal,
        "goal_description": learner.goal_description,
        "experience_level": learner.experience_level,
        "preferred_learning_style": learner.preferred_learning_style,
        "weekly_hours_available": learner.weekly_hours_available,
        "target_timeline": learner.target_timeline,
        "overall_progress": learner.overall_progress,
        "total_hours_learned": learner.total_hours_learned,
        "current_streak": learner.current_streak,
        "is_demo_user": learner.is_demo_user,
        "created_at": learner.created_at,
        "updated_at": learner.updated_at,
    }
    # Parse JSON fields
    for field in ["interests", "completed_courses", "previous_projects", "preferred_content_types"]:
        val = getattr(learner, field)
        try:
            d[field] = json.loads(val) if val else []
        except Exception:
            d[field] = []
    return d


@router.post("", response_model=LearnerResponse, status_code=status.HTTP_201_CREATED)
async def create_learner(data: LearnerCreate, db: AsyncSession = Depends(get_db)):
    # Check if email exists — if so, update learner with new goal & profile
    result = await db.execute(select(Learner).where(Learner.email == data.email))
    existing_learner = result.scalar_one_or_none()
    
    if existing_learner:
        existing_learner.name = data.name
        existing_learner.career_goal = data.career_goal
        existing_learner.goal_description = data.goal_description
        existing_learner.experience_level = data.experience_level
        existing_learner.weekly_hours_available = data.weekly_hours_available or existing_learner.weekly_hours_available
        existing_learner.target_timeline = data.target_timeline or existing_learner.target_timeline
        db.add(existing_learner)
        await db.commit()
        await db.refresh(existing_learner)
        return _serialize_learner(existing_learner)

    learner = Learner(
        name=data.name,
        email=data.email,
        career_goal=data.career_goal,
        goal_description=data.goal_description,
        experience_level=data.experience_level,
        interests=json.dumps(data.interests or []),
        completed_courses=json.dumps(data.completed_courses or []),
        previous_projects=json.dumps(data.previous_projects or []),
        preferred_learning_style=data.preferred_learning_style,
        weekly_hours_available=data.weekly_hours_available,
        target_timeline=data.target_timeline,
        preferred_content_types=json.dumps(data.preferred_content_types or []),
    )
    db.add(learner)
    await db.commit()
    await db.refresh(learner)
    return _serialize_learner(learner)


@router.get("/demo", response_model=LearnerResponse)
async def get_demo_learner(db: AsyncSession = Depends(get_db)):
    """Get the pre-configured demo learner."""
    result = await db.execute(select(Learner).where(Learner.is_demo_user == True))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Demo learner not found")
    return _serialize_learner(learner)


@router.get("/{learner_id}", response_model=LearnerResponse)
async def get_learner(learner_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")
    return _serialize_learner(learner)


@router.put("/{learner_id}", response_model=LearnerResponse)
async def update_learner(learner_id: int, data: LearnerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ["interests", "completed_courses", "previous_projects", "preferred_content_types"]:
            setattr(learner, key, json.dumps(value) if value is not None else "[]")
        elif value is not None:
            setattr(learner, key, value)

    db.add(learner)
    await db.commit()
    await db.refresh(learner)
    return _serialize_learner(learner)
