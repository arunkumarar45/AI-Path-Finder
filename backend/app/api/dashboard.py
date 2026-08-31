"""Dashboard API — aggregated view of learner progress and insights."""

import json
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import (
    Learner, LearnerSkill, Roadmap, RoadmapItem, Feedback, Assessment,
    ItemStatus, SkillPriority
)
from app.recommendation.engine import score_roadmap_item, compute_next_best_action
from app.adaptation.engine import generate_ai_insights
from app.ai.skill_gap import calculate_overall_readiness

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)


@router.get("/{learner_id}")
async def get_dashboard(learner_id: int, db: AsyncSession = Depends(get_db)):
    """Get full dashboard data for a learner."""
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Load learner skills
    ls_result = await db.execute(
        select(LearnerSkill).where(LearnerSkill.learner_id == learner_id)
    )
    learner_skills: List[LearnerSkill] = ls_result.scalars().all()
    for ls in learner_skills:
        await db.refresh(ls, ["skill"])

    # Load roadmap
    rm_result = await db.execute(select(Roadmap).where(Roadmap.learner_id == learner_id))
    roadmap = rm_result.scalar_one_or_none()

    items: List[RoadmapItem] = []
    if roadmap:
        items_result = await db.execute(
            select(RoadmapItem)
            .where(RoadmapItem.roadmap_id == roadmap.id)
            .order_by(RoadmapItem.phase_number, RoadmapItem.order_index)
        )
        items = items_result.scalars().all()
        for item in items:
            if item.resource_id:
                await db.refresh(item, ["resource"])

    # Load feedbacks
    fb_result = await db.execute(
        select(Feedback).where(Feedback.learner_id == learner_id)
    )
    feedbacks: List[Feedback] = fb_result.scalars().all()

    # Compute next best action
    completed_ids = [item.id for item in items if item.status in (ItemStatus.COMPLETED, ItemStatus.SKIPPED)]
    next_best = None
    if items:
        # Score all items
        scores = {}
        for item in items:
            if item.status == ItemStatus.NOT_STARTED:
                s = score_roadmap_item(item, learner, learner_skills, feedbacks, completed_ids, items)
                scores[item.id] = s
        nba = compute_next_best_action(items, scores, learner, learner_skills)
        if nba:
            next_best = nba

    # Skill gap summary
    all_gaps = [
        {
            "skill_name": ls.skill.name if ls.skill else "Unknown",
            "current_proficiency": ls.current_proficiency,
            "target_proficiency": ls.target_proficiency,
            "gap_score": ls.gap_score,
            "priority": ls.priority,
        }
        for ls in learner_skills if ls.skill
    ]
    readiness = calculate_overall_readiness(all_gaps)
    critical_gaps = [g for g in all_gaps if str(g.get("priority", "")).endswith("CRITICAL") and g["gap_score"] > 0.1]

    # Milestones
    milestone_items = [item for item in items if item.is_milestone]
    completed_milestones = [m for m in milestone_items if m.status == ItemStatus.COMPLETED]

    # Recent activity
    recent_activity = []
    recently_completed = sorted(
        [i for i in items if i.completed_at],
        key=lambda x: x.completed_at,
        reverse=True
    )[:5]
    for item in recently_completed:
        recent_activity.append({
            "type": "completed",
            "title": item.title,
            "phase": item.phase_name,
            "date": item.completed_at.isoformat() if item.completed_at else None,
        })

    # AI insights
    insights = generate_ai_insights(learner, roadmap, all_gaps)

    # Skills developed (count skills with proficiency >= 3)
    skills_developed = sum(1 for ls in learner_skills if ls.current_proficiency >= 3.0)

    # Chart data
    skill_chart = [
        {
            "skill": ls.skill.name if ls.skill else "Unknown",
            "current": ls.current_proficiency,
            "target": ls.target_proficiency,
            "gap": ls.gap_score,
            "priority": str(ls.priority.value) if ls.priority else "OPTIONAL",
        }
        for ls in learner_skills if ls.skill
    ]

    return {
        "learner": {
            "id": learner.id,
            "name": learner.name,
            "email": learner.email,
            "career_goal": learner.career_goal,
            "experience_level": learner.experience_level,
            "weekly_hours_available": learner.weekly_hours_available,
            "target_timeline": learner.target_timeline,
            "overall_progress": learner.overall_progress,
            "total_hours_learned": learner.total_hours_learned,
            "current_streak": learner.current_streak,
            "is_demo_user": learner.is_demo_user,
        },
        "overall_progress": learner.overall_progress,
        "skills_developed": skills_developed,
        "total_hours_learned": learner.total_hours_learned,
        "current_phase": roadmap.current_phase if roadmap else 1,
        "total_phases": roadmap.total_phases if roadmap else 1,
        "milestones_completed": len(completed_milestones),
        "milestones_total": len(milestone_items),
        "deadline_status": roadmap.schedule_status.value if roadmap else "ON_TRACK",
        "streak": learner.current_streak,
        "overall_readiness": round(readiness, 3),
        "skill_gap_summary": {
            "critical_count": len(critical_gaps),
            "strong_count": sum(1 for ls in learner_skills if ls.current_proficiency >= ls.target_proficiency),
            "top_critical_gaps": [g["skill_name"] for g in critical_gaps[:3]],
        },
        "recent_activity": recent_activity,
        "next_best_action": next_best,
        "ai_insights": insights,
        "roadmap_summary": {
            "id": roadmap.id if roadmap else None,
            "title": roadmap.title if roadmap else None,
            "completion_percentage": roadmap.completion_percentage if roadmap else 0,
            "total_items": roadmap.total_items if roadmap else 0,
            "completed_items": roadmap.completed_items if roadmap else 0,
            "schedule_status": roadmap.schedule_status.value if roadmap else "ON_TRACK",
            "estimated_completion": roadmap.estimated_completion_date if roadmap else None,
        },
        "skill_chart_data": skill_chart,
    }


@router.get("/{learner_id}/recommendations")
async def get_recommendations(learner_id: int, limit: int = 5, db: AsyncSession = Depends(get_db)):
    """Get ranked recommendations for a learner."""
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    ls_result = await db.execute(
        select(LearnerSkill).where(LearnerSkill.learner_id == learner_id)
    )
    learner_skills = ls_result.scalars().all()
    for ls in learner_skills:
        await db.refresh(ls, ["skill"])

    rm_result = await db.execute(select(Roadmap).where(Roadmap.learner_id == learner_id))
    roadmap = rm_result.scalar_one_or_none()
    if not roadmap:
        return {"recommendations": [], "next_best_action": None}

    items_result = await db.execute(
        select(RoadmapItem)
        .where(RoadmapItem.roadmap_id == roadmap.id, RoadmapItem.status == ItemStatus.NOT_STARTED)
        .order_by(RoadmapItem.phase_number, RoadmapItem.order_index)
    )
    items = items_result.scalars().all()
    for item in items:
        if item.resource_id:
            await db.refresh(item, ["resource"])

    fb_result = await db.execute(select(Feedback).where(Feedback.learner_id == learner_id))
    feedbacks = fb_result.scalars().all()

    all_items_result = await db.execute(
        select(RoadmapItem).where(RoadmapItem.roadmap_id == roadmap.id)
    )
    all_items = all_items_result.scalars().all()
    completed_ids = [i.id for i in all_items if i.status in (ItemStatus.COMPLETED, ItemStatus.SKIPPED)]

    from app.recommendation.engine import score_roadmap_item, generate_recommendation_reason

    scored = []
    for item in items:
        score = score_roadmap_item(item, learner, learner_skills, feedbacks, completed_ids, all_items)
        reason = generate_recommendation_reason(item, score, learner, learner_skills)
        resource_data = None
        if item.resource:
            resource_data = {
                "id": item.resource.id,
                "title": item.resource.title,
                "provider": item.resource.provider,
                "url": item.resource.url,
                "type": item.resource.type,
                "estimated_hours": item.resource.estimated_hours,
                "rating": item.resource.rating,
                "is_free": item.resource.is_free,
            }
        scored.append({
            "item_id": item.id,
            "title": item.title,
            "type": item.type,
            "score": round(score.total_score, 3),
            "why_recommended": reason,
            "scoring_metadata": score.to_dict(),
            "resource": resource_data,
            "estimated_hours": item.estimated_hours,
            "skills_gained": [s.strip() for s in item.skills_gained.split(",")] if item.skills_gained else [],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    for i, item in enumerate(scored):
        item["rank"] = i + 1

    nba = compute_next_best_action(items, {i.id: score_roadmap_item(i, learner, learner_skills, feedbacks, completed_ids, all_items) for i in items}, learner, learner_skills)

    return {
        "learner_id": learner_id,
        "recommendations": scored[:limit],
        "next_best_action": nba,
    }
