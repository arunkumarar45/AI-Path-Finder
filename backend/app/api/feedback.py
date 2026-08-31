"""Feedback and adaptive learning API."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Learner, Feedback, RoadmapItem
from app.schemas.schemas import FeedbackCreate, FeedbackResponse
from app.adaptation.engine import process_feedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(data: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    """Submit feedback about a learning item — triggers adaptive changes."""
    result = await db.execute(select(Learner).where(Learner.id == data.learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    feedback = Feedback(
        learner_id=data.learner_id,
        roadmap_item_id=data.roadmap_item_id,
        type=data.type,
        message=data.message,
    )
    db.add(feedback)
    await db.flush()

    # Process feedback — triggers adaptation
    system_response = await process_feedback(learner, feedback, db)
    feedback.system_response = system_response
    feedback.processed = True
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return FeedbackResponse(
        id=feedback.id,
        type=feedback.type,
        message=feedback.message,
        system_response=feedback.system_response,
        processed=feedback.processed,
        created_at=feedback.created_at,
    )


@router.get("/{learner_id}")
async def get_feedback_history(learner_id: int, db: AsyncSession = Depends(get_db)):
    """Get all feedback submitted by a learner."""
    result = await db.execute(
        select(Feedback)
        .where(Feedback.learner_id == learner_id)
        .order_by(Feedback.created_at.desc())
        .limit(20)
    )
    feedbacks = result.scalars().all()
    return [
        {
            "id": f.id,
            "type": f.type,
            "message": f.message,
            "system_response": f.system_response,
            "processed": f.processed,
            "created_at": f.created_at,
            "roadmap_item_id": f.roadmap_item_id,
        }
        for f in feedbacks
    ]
