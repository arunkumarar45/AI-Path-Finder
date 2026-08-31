"""AI Learning Mentor — context-aware conversational assistant."""

import json
import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import (
    Learner, LearnerSkill, Roadmap, RoadmapItem, ChatMessage,
    ItemStatus, MessageRole, SkillPriority
)
from app.ai.provider import get_provider

logger = logging.getLogger(__name__)


async def build_learner_context(learner: Learner, db: AsyncSession) -> dict:
    """Build structured context from learner's current state."""
    context = {
        "learner": {
            "name": learner.name,
            "goal": learner.career_goal,
            "experience_level": learner.experience_level.value if learner.experience_level else "INTERMEDIATE",
            "weekly_hours": learner.weekly_hours_available,
            "target_timeline": learner.target_timeline,
            "overall_progress": f"{learner.overall_progress:.0f}%",
        },
        "skills": [],
        "roadmap": None,
        "next_items": [],
        "completed_items": [],
        "critical_gaps": [],
    }

    # Load skills
    result = await db.execute(
        select(LearnerSkill).where(LearnerSkill.learner_id == learner.id)
    )
    learner_skills: List[LearnerSkill] = result.scalars().all()

    for ls in learner_skills:
        await db.refresh(ls, ["skill"])
        if ls.skill:
            context["skills"].append({
                "name": ls.skill.name,
                "current": ls.current_proficiency,
                "target": ls.target_proficiency,
                "gap": ls.gap_score,
                "priority": ls.priority.value if ls.priority else "RECOMMENDED",
                "status": ls.status.value,
            })
            if ls.priority == SkillPriority.CRITICAL and ls.gap_score > 0.3:
                context["critical_gaps"].append({
                    "skill": ls.skill.name,
                    "gap": f"{ls.gap_score:.0%}"
                })

    # Load roadmap
    result = await db.execute(
        select(Roadmap).where(Roadmap.learner_id == learner.id)
    )
    roadmap: Optional[Roadmap] = result.scalar_one_or_none()

    if roadmap:
        context["roadmap"] = {
            "title": roadmap.title,
            "completion": f"{roadmap.completion_percentage:.0f}%",
            "current_phase": roadmap.current_phase,
            "total_phases": roadmap.total_phases,
            "schedule_status": roadmap.schedule_status.value,
        }

        # Explicitly query roadmap items (async-safe)
        items_result = await db.execute(
            select(RoadmapItem)
            .where(RoadmapItem.roadmap_id == roadmap.id)
            .order_by(RoadmapItem.phase_number, RoadmapItem.order_index)
        )
        all_items: List[RoadmapItem] = items_result.scalars().all()

        # Get next items
        next_items = [i for i in all_items if i.status == ItemStatus.NOT_STARTED][:3]
        context["next_items"] = [
            {
                "title": item.title,
                "phase": item.phase_name,
                "hours": item.estimated_hours,
                "skills": item.skills_gained,
                "why": item.why_recommended,
            }
            for item in next_items
        ]

        # Completed items
        completed = [i for i in all_items if i.status == ItemStatus.COMPLETED]
        context["completed_items"] = [item.title for item in completed[:5]]

    return context


SYSTEM_PROMPT = """You are an expert AI learning mentor for an adaptive learning platform.
You help learners understand their personalized learning path, skill gaps, and progress.

Your responses must:
1. Be SPECIFIC to the learner's actual data provided in the context
2. Be encouraging but honest
3. Give actionable advice
4. Reference specific skills, courses, and roadmap items from the context
5. Be concise (3-5 sentences unless the question requires more detail)
6. NEVER make up skills, courses, or progress data not in the context

You are NOT a generic AI assistant — you are this specific learner's dedicated mentor."""


async def get_mentor_response(
    learner: Learner,
    user_message: str,
    db: AsyncSession
) -> str:
    """Get an AI mentor response grounded in learner context."""
    provider = get_provider()

    # Build structured context
    context = await build_learner_context(learner, db)
    context_json = json.dumps(context, indent=2)

    # Get recent chat history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.learner_id == learner.id)
        .order_by(ChatMessage.timestamp.desc())
        .limit(6)
    )
    recent_messages: List[ChatMessage] = list(reversed(result.scalars().all()))

    history_text = ""
    for msg in recent_messages[-4:]:  # last 4 messages for context
        role_label = "Learner" if msg.role == MessageRole.USER else "Mentor"
        history_text += f"{role_label}: {msg.content}\n"

    prompt = f"""LEARNER CONTEXT (use this data to give specific answers):
{context_json}

CONVERSATION HISTORY:
{history_text}

LEARNER QUESTION: {user_message}

Answer the learner's question using ONLY data from their actual context above.
Be specific — mention their actual skills, goals, and roadmap items by name.
If they ask about skipping something, reference their actual proficiency scores.
If they ask about time, reference their {context['learner']['weekly_hours']} hours/week.
"""

    if provider.is_available():
        try:
            response = await provider.generate(prompt, SYSTEM_PROMPT)
            # Ensure response is not too long
            if len(response) > 1000:
                response = response[:997] + "..."
            return response
        except Exception as e:
            logger.error(f"AI mentor error: {e}")

    # Fallback — deterministic response based on keywords
    return _fallback_mentor_response(user_message, context)


def _fallback_mentor_response(message: str, context: dict) -> str:
    """Deterministic fallback mentor using learner context."""
    msg_lower = message.lower()
    learner_name = context.get("learner", {}).get("name", "")
    goal = context.get("learner", {}).get("goal", "your goal")
    critical_gaps = context.get("critical_gaps", [])
    next_items = context.get("next_items", [])
    completed = context.get("completed_items", [])

    if "next" in msg_lower or "what should" in msg_lower:
        if next_items:
            item = next_items[0]
            gap_info = ""
            if critical_gaps:
                gap_info = f" This addresses {critical_gaps[0]['skill']} which is your most critical gap."
            return (
                f"Your next recommended action is: **{item['title']}** ({item['hours']} hours).{gap_info} "
                f"{item.get('why', 'This is the highest-priority item in your current roadmap phase.')}"
            )
        return f"You've completed all current roadmap items! Your roadmap may need updating based on your progress."

    if "skip" in msg_lower:
        # Find the skill being mentioned
        for skill_data in context.get("skills", []):
            if skill_data["name"].lower() in msg_lower:
                current = skill_data["current"]
                if current >= 3.0:
                    return (
                        f"Yes! Since your {skill_data['name']} proficiency is {current:.0f}/5, "
                        f"you can safely skip the beginner {skill_data['name']} content. "
                        f"I'll mark it as known and adjust your roadmap. "
                        f"You'll still need to complete the advanced {skill_data['name']} material though."
                    )
                else:
                    return (
                        f"Based on your profile, your {skill_data['name']} is at {current:.0f}/5 — "
                        f"I'd recommend at least completing the intermediate material before moving on. "
                        f"It's foundational for {', '.join(g['skill'] for g in critical_gaps[:2])}."
                    )
        return "I can check if you can skip that topic. Which specific skill or course are you referring to?"

    if "why" in msg_lower and ("spring" in msg_lower or "boot" in msg_lower or "recommend" in msg_lower):
        if next_items:
            item = next_items[0]
            return (
                f"Spring Boot is recommended because it's the most critical skill gap for {goal}. "
                f"Your current proficiency shows you know the prerequisites (Java, OOP, SQL), "
                f"making this the perfect next step. "
                f"It unlocks REST APIs, JPA, and Spring Security — all critical for your goal."
            )

    if "on track" in msg_lower or "deadline" in msg_lower or "timeline" in msg_lower:
        schedule = context.get("roadmap", {}).get("schedule_status", "ON_TRACK") if context.get("roadmap") else "ON_TRACK"
        progress = context.get("learner", {}).get("overall_progress", "0%")
        timeline = context.get("learner", {}).get("target_timeline", "your target timeline")
        status_msg = {
            "ON_TRACK": "on track",
            "AHEAD_OF_SCHEDULE": "ahead of schedule",
            "AT_RISK": "slightly behind schedule"
        }.get(schedule, "on track")
        return (
            f"Based on your current progress ({progress}) and {context['learner']['weekly_hours']} hours/week, "
            f"you are {status_msg} for {timeline}. "
            f"Focus on CRITICAL skills first to protect your timeline."
        )

    if "time" in msg_lower or "hour" in msg_lower:
        hours = context.get("learner", {}).get("weekly_hours", 8)
        return (
            f"With {hours} hours per week, I recommend breaking your study sessions into "
            f"2-3 hour blocks for maximum retention. "
            f"Focus on your critical gaps first: {', '.join(g['skill'] for g in critical_gaps[:3])}. "
            f"Even a consistent 1 hour daily is more effective than irregular long sessions."
        )

    if "explain" in msg_lower or "what is" in msg_lower or "how does" in msg_lower:
        return (
            f"Great question! Based on your {goal} goal, understanding this concept is important "
            f"because it's a foundational skill for your target role. "
            f"I'd recommend checking the resources attached to this topic in your roadmap "
            f"for detailed explanations with practical examples."
        )

    # Default response with context
    gap_text = f"Your top priority gap is {critical_gaps[0]['skill']}. " if critical_gaps else ""
    progress_text = f"You are {context.get('learner', {}).get('overall_progress', '0%')} complete on your roadmap. "
    return (
        f"Hi {learner_name}! {progress_text}{gap_text}"
        f"Based on your goal to become {goal}, I recommend focusing on your next roadmap item: "
        f"{next_items[0]['title'] if next_items else 'reviewing your current phase'}. "
        f"Let me know if you have specific questions about your learning path!"
    )
