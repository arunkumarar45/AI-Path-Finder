"""Roadmap generation and management API."""

import json
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import (
    Learner, LearnerSkill, Resource, Roadmap, RoadmapItem,
    ItemStatus, ItemType, ResourceDifficulty, RoadmapStatus, SkillPriority
)
from app.schemas.schemas import (
    RoadmapResponse, RoadmapGenerateRequest, RoadmapItemResponse,
    UpdateItemStatusRequest, ScoringMetadata, ResourceResponse
)
from app.roadmap.generator import generate_roadmap, compute_schedule_status, estimate_completion_date
from app.ai.skill_gap import analyze_skill_gaps

router = APIRouter(prefix="/api/roadmaps", tags=["roadmaps"])
logger = logging.getLogger(__name__)


def _parse_item(item: RoadmapItem) -> dict:
    """Convert RoadmapItem to dict for response."""
    scoring = None
    if item.scoring_metadata:
        try:
            sm = json.loads(item.scoring_metadata)
            scoring = ScoringMetadata(**sm)
        except Exception:
            pass

    project_info = None
    if item.project_info:
        try:
            project_info = json.loads(item.project_info)
        except Exception:
            pass

    prereq_ids = None
    if item.prerequisite_item_ids:
        try:
            prereq_ids = [int(x.strip()) for x in item.prerequisite_item_ids.split(",") if x.strip()]
        except Exception:
            prereq_ids = []

    skills_gained = None
    if item.skills_gained:
        skills_gained = [s.strip() for s in item.skills_gained.split(",")]

    resource_resp = None
    if item.resource:
        resource_resp = ResourceResponse(
            id=item.resource.id,
            title=item.resource.title,
            description=item.resource.description,
            provider=item.resource.provider,
            url=item.resource.url,
            type=item.resource.type,
            difficulty=item.resource.difficulty,
            skills_taught=[s.strip() for s in item.resource.skills_taught.split(",")] if item.resource.skills_taught else None,
            prerequisite_skills=[s.strip() for s in item.resource.prerequisite_skills.split(",")] if item.resource.prerequisite_skills else None,
            estimated_hours=item.resource.estimated_hours,
            rating=item.resource.rating,
            popularity_score=item.resource.popularity_score,
            is_free=item.resource.is_free,
        )

    return {
        "id": item.id,
        "phase_number": item.phase_number,
        "phase_name": item.phase_name,
        "order_index": item.order_index,
        "title": item.title,
        "description": item.description,
        "type": item.type,
        "difficulty": item.difficulty,
        "estimated_hours": item.estimated_hours,
        "skills_gained": skills_gained,
        "prerequisite_item_ids": prereq_ids,
        "milestone_text": item.milestone_text,
        "is_milestone": item.is_milestone,
        "status": item.status,
        "why_recommended": item.why_recommended,
        "scoring_metadata": scoring,
        "project_info": project_info,
        "resource": resource_resp,
        "started_at": item.started_at,
        "completed_at": item.completed_at,
    }


@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_learner_roadmap(
    request: RoadmapGenerateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a personalized roadmap for a learner."""
    result = await db.execute(select(Learner).where(Learner.id == request.learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Check existing roadmap
    existing = await db.execute(select(Roadmap).where(Roadmap.learner_id == request.learner_id))
    existing_roadmap = existing.scalar_one_or_none()

    if existing_roadmap and not request.regenerate:
        return {"message": "Roadmap already exists", "roadmap_id": existing_roadmap.id}

    if existing_roadmap and request.regenerate:
        await db.delete(existing_roadmap)
        await db.commit()

    # Get skill gaps
    gaps = await analyze_skill_gaps(learner, db, use_ai=True)

    # Load resources
    resources_result = await db.execute(select(Resource))
    resources: List[Resource] = resources_result.scalars().all()

    # Generate roadmap structure
    title, description, phases_data = await generate_roadmap(learner, gaps, resources, db)

    # Persist roadmap
    total_items = sum(len(phase["items"]) for phase in phases_data)
    roadmap = Roadmap(
        learner_id=learner.id,
        title=title,
        description=description,
        total_phases=len(phases_data),
        current_phase=1,
        total_items=total_items,
        completed_items=0,
        completion_percentage=0.0,
        status=RoadmapStatus.ACTIVE,
        estimated_completion_date=estimate_completion_date(learner, sum(
            item["hours"] for phase in phases_data for item in phase["items"]
        )),
        schedule_status=compute_schedule_status(learner, None) if False else "ON_TRACK",
        ai_reasoning=description,
    )
    db.add(roadmap)
    await db.flush()

    # Create roadmap items
    for phase in phases_data:
        for item_data in phase["items"]:
            # Find matching resource
            resource_id = None
            keywords = item_data.get("resource_keywords", [])
            if keywords:
                for res in resources:
                    if res.skills_taught and any(kw.lower() in res.skills_taught.lower() for kw in keywords):
                        resource_id = res.id
                        break

            item = RoadmapItem(
                roadmap_id=roadmap.id,
                phase_number=phase["phase"],
                phase_name=phase["name"],
                order_index=item_data.get("order_index", 0),
                title=item_data["title"],
                description=item_data.get("desc", ""),
                type=item_data["type"],
                difficulty=item_data["difficulty"],
                estimated_hours=item_data["hours"],
                skills_gained=item_data.get("skills", ""),
                is_milestone=bool(item_data.get("milestone")),
                milestone_text=item_data.get("milestone"),
                status=ItemStatus.NOT_STARTED,
                why_recommended=item_data.get("why", "Based on your skill gaps and learning preferences"),
                project_info=json.dumps(item_data["project"]) if "project" in item_data else None,
                resource_id=resource_id,
            )
            db.add(item)

    await db.commit()
    return {"message": "Roadmap generated", "roadmap_id": roadmap.id}


@router.get("/{learner_id}")
async def get_roadmap(learner_id: int, db: AsyncSession = Depends(get_db)):
    """Get the current roadmap for a learner."""
    result = await db.execute(
        select(Roadmap).where(Roadmap.learner_id == learner_id)
    )
    roadmap = result.scalar_one_or_none()
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found for this learner")

    # Eager load items and resources
    items_result = await db.execute(
        select(RoadmapItem)
        .where(RoadmapItem.roadmap_id == roadmap.id)
        .order_by(RoadmapItem.phase_number, RoadmapItem.order_index)
    )
    items: List[RoadmapItem] = items_result.scalars().all()

    for item in items:
        if item.resource_id:
            await db.refresh(item, ["resource"])

    # Build phases
    phases = {}
    for item in items:
        key = (item.phase_number, item.phase_name)
        if key not in phases:
            phases[key] = []
        phases[key].append(_parse_item(item))

    return {
        "id": roadmap.id,
        "learner_id": roadmap.learner_id,
        "title": roadmap.title,
        "description": roadmap.description,
        "total_phases": roadmap.total_phases,
        "current_phase": roadmap.current_phase,
        "total_items": roadmap.total_items,
        "completed_items": roadmap.completed_items,
        "completion_percentage": roadmap.completion_percentage,
        "status": roadmap.status,
        "estimated_completion_date": roadmap.estimated_completion_date,
        "schedule_status": roadmap.schedule_status,
        "ai_reasoning": roadmap.ai_reasoning,
        "generated_at": roadmap.generated_at,
        "updated_at": roadmap.updated_at,
        "items": [item for items_list in sorted(phases.items()) for item in items_list[1]],
    }


@router.put("/items/{item_id}/status")
async def update_item_status(
    item_id: int,
    request: UpdateItemStatusRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update the status of a roadmap item (complete, skip, etc.)."""
    result = await db.execute(select(RoadmapItem).where(RoadmapItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Roadmap item not found")

    old_status = item.status
    item.status = request.status

    if request.status == ItemStatus.IN_PROGRESS and not item.started_at:
        item.started_at = datetime.utcnow()
    elif request.status == ItemStatus.COMPLETED:
        item.completed_at = datetime.utcnow()
        if not item.started_at:
            item.started_at = item.completed_at

    db.add(item)

    # Update roadmap statistics
    roadmap_result = await db.execute(select(Roadmap).where(Roadmap.id == item.roadmap_id))
    roadmap = roadmap_result.scalar_one_or_none()
    if roadmap:
        items_result = await db.execute(
            select(RoadmapItem).where(RoadmapItem.roadmap_id == roadmap.id)
        )
        all_items: List[RoadmapItem] = items_result.scalars().all()
        # Mark the current item's status
        for i in all_items:
            if i.id == item_id:
                i.status = request.status
        completed = sum(1 for i in all_items if i.status in (ItemStatus.COMPLETED, ItemStatus.SKIPPED))
        roadmap.completed_items = completed
        roadmap.total_items = len(all_items)
        roadmap.completion_percentage = (completed / max(1, len(all_items))) * 100

        # Update learner overall progress
        learner_result = await db.execute(select(Learner).where(Learner.id == roadmap.learner_id))
        learner = learner_result.scalar_one_or_none()
        if learner:
            learner.overall_progress = roadmap.completion_percentage
            if request.status == ItemStatus.COMPLETED:
                learner.total_hours_learned += (item.estimated_hours or 0)
            db.add(learner)

        db.add(roadmap)

    await db.commit()

    return {
        "message": f"Item status updated to {request.status.value}",
        "item_id": item_id,
        "old_status": old_status.value,
        "new_status": request.status.value,
        "roadmap_progress": roadmap.completion_percentage if roadmap else 0,
    }
