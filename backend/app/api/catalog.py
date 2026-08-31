"""Skills and resources catalog API."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.models import Skill, Resource

router = APIRouter(prefix="/api", tags=["catalog"])
logger = logging.getLogger(__name__)


@router.get("/skills")
async def list_skills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).order_by(Skill.name))
    skills = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "domain": s.domain,
            "prerequisites": [p.strip() for p in s.prerequisites.split(",")] if s.prerequisites else [],
            "difficulty_level": s.difficulty_level,
        }
        for s in skills
    ]


@router.get("/skills/{skill_id}")
async def get_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Skill not found")
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "domain": skill.domain,
        "prerequisites": [p.strip() for p in skill.prerequisites.split(",")] if skill.prerequisites else [],
        "difficulty_level": skill.difficulty_level,
    }


@router.get("/resources")
async def list_resources(
    skill: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    is_free: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(Resource)
    if skill:
        from sqlalchemy import or_
        query = query.where(Resource.skills_taught.ilike(f"%{skill}%"))
    if type:
        try:
            from app.models.models import ResourceType
            query = query.where(Resource.type == ResourceType(type))
        except ValueError:
            pass
    if is_free is not None:
        query = query.where(Resource.is_free == is_free)

    result = await db.execute(query.order_by(Resource.rating.desc()))
    resources = result.scalars().all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "description": r.description,
            "provider": r.provider,
            "url": r.url,
            "type": r.type,
            "difficulty": r.difficulty,
            "skills_taught": [s.strip() for s in r.skills_taught.split(",")] if r.skills_taught else [],
            "estimated_hours": r.estimated_hours,
            "rating": r.rating,
            "popularity_score": r.popularity_score,
            "is_free": r.is_free,
        }
        for r in resources
    ]


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    try:
        await db.execute(select(Skill).limit(1))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    from app.ai.provider import get_provider
    ai_available = get_provider().is_available()

    return {
        "status": "healthy",
        "ai_available": ai_available,
        "database": db_status,
        "version": "1.0.0"
    }
