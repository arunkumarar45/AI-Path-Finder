"""Skill gap analysis API."""

import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.models.models import Learner, Skill, LearnerSkill, SkillStatus
from app.schemas.schemas import SkillGapAnalysisResponse, LearnerSkillResponse, SkillResponse
from app.ai.skill_gap import analyze_skill_gaps, calculate_overall_readiness, build_skill_graph

router = APIRouter(prefix="/api/skill-gaps", tags=["skill-gaps"])
logger = logging.getLogger(__name__)


@router.post("/analyze/{learner_id}", response_model=SkillGapAnalysisResponse)
async def run_skill_gap_analysis(learner_id: int, db: AsyncSession = Depends(get_db)):
    """Run full skill gap analysis for a learner and persist results."""
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Run analysis
    gaps = await analyze_skill_gaps(learner, db)

    # Upsert LearnerSkill records
    for gap in gaps:
        skill_name = gap["skill_name"]
        # Find or create skill
        skill_result = await db.execute(select(Skill).where(Skill.name == skill_name))
        skill = skill_result.scalar_one_or_none()
        if not skill:
            skill = Skill(name=skill_name)
            db.add(skill)
            await db.flush()

        # Upsert learner skill
        ls_result = await db.execute(
            select(LearnerSkill).where(
                LearnerSkill.learner_id == learner_id,
                LearnerSkill.skill_id == skill.id
            )
        )
        ls = ls_result.scalar_one_or_none()
        if not ls:
            ls = LearnerSkill(
                learner_id=learner_id,
                skill_id=skill.id,
                current_proficiency=gap["current_proficiency"],
                target_proficiency=gap["target_proficiency"],
                gap_score=gap["gap_score"],
                priority=gap["priority"],
                status=gap["status"],
                confidence=0.8,
            )
            db.add(ls)
        else:
            ls.current_proficiency = gap["current_proficiency"]
            ls.target_proficiency = gap["target_proficiency"]
            ls.gap_score = gap["gap_score"]
            ls.priority = gap["priority"]
            ls.status = gap["status"]
            db.add(ls)

    await db.commit()

    return await get_skill_gaps(learner_id, db)


@router.get("/{learner_id}", response_model=SkillGapAnalysisResponse)
async def get_skill_gaps(learner_id: int, db: AsyncSession = Depends(get_db)):
    """Get current skill gap analysis for a learner."""
    result = await db.execute(select(Learner).where(Learner.id == learner_id))
    learner = result.scalar_one_or_none()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found")

    # Load learner skills
    ls_result = await db.execute(
        select(LearnerSkill).where(LearnerSkill.learner_id == learner_id)
    )
    learner_skills: List[LearnerSkill] = ls_result.scalars().all()

    # Eager load skills
    for ls in learner_skills:
        await db.refresh(ls, ["skill"])

    strong, critical, recommended, optional = [], [], [], []
    all_gaps = []

    for ls in learner_skills:
        if not ls.skill:
            continue
        skill_resp = SkillResponse(
            id=ls.skill.id,
            name=ls.skill.name,
            description=ls.skill.description,
            category=ls.skill.category,
            domain=ls.skill.domain,
            prerequisites=[p.strip() for p in ls.skill.prerequisites.split(",")] if ls.skill.prerequisites else [],
            difficulty_level=ls.skill.difficulty_level,
        )
        ls_resp = LearnerSkillResponse(
            id=ls.id,
            skill=skill_resp,
            current_proficiency=ls.current_proficiency,
            target_proficiency=ls.target_proficiency,
            gap_score=ls.gap_score,
            priority=ls.priority,
            status=ls.status,
            confidence=ls.confidence,
        )

        from app.models.models import SkillPriority
        if ls.current_proficiency >= ls.target_proficiency:
            strong.append(ls_resp)
        elif ls.priority == SkillPriority.CRITICAL:
            critical.append(ls_resp)
        elif ls.priority == SkillPriority.RECOMMENDED:
            recommended.append(ls_resp)
        else:
            optional.append(ls_resp)

        all_gaps.append({
            "skill_name": ls.skill.name,
            "current_proficiency": ls.current_proficiency,
            "target_proficiency": ls.target_proficiency,
            "gap_score": ls.gap_score,
            "priority": ls.priority,
        })

    # Sort by gap score descending
    critical.sort(key=lambda x: x.gap_score, reverse=True)
    recommended.sort(key=lambda x: x.gap_score, reverse=True)

    readiness = calculate_overall_readiness(all_gaps)

    # Build graph data
    existing_skill_names = [ls.skill.name for ls in learner_skills if ls.skill and ls.current_proficiency >= 2]
    nodes, edges = build_skill_graph(all_gaps, existing_skill_names)

    goal = learner.career_goal or "your learning goal"
    summary = (
        f"For your goal of {goal}: "
        f"{len(strong)} skills are strong, "
        f"{len(critical)} critical gaps, "
        f"{len(recommended)} recommended gaps. "
        f"Overall readiness: {readiness:.0%}"
    )

    return SkillGapAnalysisResponse(
        learner_id=learner_id,
        goal=goal,
        strong_skills=strong,
        critical_gaps=critical,
        recommended_gaps=recommended,
        optional_gaps=optional,
        overall_readiness=round(readiness, 3),
        analysis_summary=summary,
        skill_graph_nodes=nodes,
        skill_graph_edges=edges,
    )


@router.put("/{learner_id}/skill/{skill_id}")
async def update_skill_proficiency(
    learner_id: int, skill_id: int,
    current_proficiency: float,
    db: AsyncSession = Depends(get_db)
):
    """Manually update a learner's skill proficiency (e.g., after 'I already know this')."""
    result = await db.execute(
        select(LearnerSkill).where(
            LearnerSkill.learner_id == learner_id,
            LearnerSkill.skill_id == skill_id
        )
    )
    ls = result.scalar_one_or_none()
    if not ls:
        raise HTTPException(status_code=404, detail="Learner skill not found")

    ls.current_proficiency = min(5.0, max(0.0, current_proficiency))
    ls.gap_score = max(0.0, ls.target_proficiency - ls.current_proficiency) / ls.target_proficiency
    if ls.current_proficiency >= ls.target_proficiency:
        ls.status = SkillStatus.COMPLETED
    db.add(ls)
    await db.commit()
    return {"message": "Proficiency updated", "new_proficiency": ls.current_proficiency}
