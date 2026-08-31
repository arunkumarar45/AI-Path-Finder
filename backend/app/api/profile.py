"""Profile analysis API — natural language → structured profile."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Learner
from app.schemas.schemas import ProfileAnalyzeRequest, ExtractedProfile, LearnerResponse
from app.ai.profile_extraction import extract_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=ExtractedProfile)
async def analyze_profile(request: ProfileAnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """Extract structured profile from natural language goal description."""
    if not request.natural_language_goal.strip():
        raise HTTPException(status_code=400, detail="Goal description cannot be empty")

    extracted = await extract_profile(request.natural_language_goal)
    return extracted


@router.post("/analyze-and-create")
async def analyze_and_create_learner(
    request: ProfileAnalyzeRequest,
    name: str,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Extract profile and create a new learner in one step."""
    extracted = await extract_profile(request.natural_language_goal)

    # Check email
    result = await db.execute(select(Learner).where(Learner.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Email {email} already registered")

    learner = Learner(
        name=name,
        email=email,
        career_goal=extracted.career_goal,
        goal_description=request.natural_language_goal,
        experience_level=extracted.experience_level,
        interests=json.dumps(extracted.interests or []),
        completed_courses=json.dumps(extracted.completed_courses or []),
        previous_projects=json.dumps(extracted.projects or []),
        preferred_learning_style=extracted.learning_style,
        weekly_hours_available=extracted.weekly_hours,
        target_timeline=extracted.timeline,
    )
    db.add(learner)
    await db.commit()
    await db.refresh(learner)

    return {"learner_id": learner.id, "extracted_profile": extracted}
