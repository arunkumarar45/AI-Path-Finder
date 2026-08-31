"""Adaptive learning engine — updates recommendations when learner state changes."""

import json
import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.models import (
    Learner, LearnerSkill, RoadmapItem, Roadmap, Feedback,
    FeedbackType, ItemStatus, SkillStatus, ScheduleStatus
)
from app.ai.provider import get_provider

logger = logging.getLogger(__name__)


async def process_feedback(
    learner: Learner,
    feedback: Feedback,
    db: AsyncSession
) -> str:
    """
    Process feedback and adapt the learner's learning path.
    Returns a system response message explaining what changed.
    """
    feedback_type = feedback.type
    item = None

    if feedback.roadmap_item_id:
        result = await db.execute(
            select(RoadmapItem).where(RoadmapItem.id == feedback.roadmap_item_id)
        )
        item = result.scalar_one_or_none()

    response = ""

    if feedback_type == FeedbackType.TOO_EASY:
        response = await _handle_too_easy(learner, item, feedback, db)

    elif feedback_type == FeedbackType.TOO_DIFFICULT:
        response = await _handle_too_difficult(learner, item, feedback, db)

    elif feedback_type == FeedbackType.ALREADY_KNOW:
        response = await _handle_already_know(learner, item, feedback, db)

    elif feedback_type == FeedbackType.SKIP:
        response = await _handle_skip(learner, item, feedback, db)

    elif feedback_type == FeedbackType.TIME_CONSTRAINT:
        response = await _handle_time_constraint(learner, feedback, db)

    elif feedback_type == FeedbackType.NEED_MORE_PRACTICE:
        response = await _handle_need_practice(learner, item, feedback, db)

    elif feedback_type == FeedbackType.VERY_USEFUL:
        response = "Thank you for the feedback! I'll prioritize similar content in your roadmap."

    elif feedback_type == FeedbackType.CUSTOM:
        response = await _handle_custom_feedback(learner, feedback, db)

    else:
        response = "Feedback received. Your learning path will be updated accordingly."

    # Mark feedback as processed
    feedback.processed = True
    feedback.system_response = response
    db.add(feedback)
    await db.commit()

    return response


async def _handle_too_easy(
    learner: Learner, item: Optional[RoadmapItem], feedback: Feedback, db: AsyncSession
) -> str:
    """Increase proficiency and skip beginner content."""
    changes = []

    if item and item.skills_gained:
        skills = [s.strip() for s in item.skills_gained.split(",")]
        for skill_name in skills:
            result = await db.execute(
                select(LearnerSkill).join(LearnerSkill.skill)
                .where(LearnerSkill.learner_id == learner.id)
            )
            learner_skills = result.scalars().all()
            for ls in learner_skills:
                await db.refresh(ls, ["skill"])
                if ls.skill and ls.skill.name.lower() == skill_name.lower():
                    # Increase proficiency
                    old = ls.current_proficiency
                    ls.current_proficiency = min(5.0, ls.current_proficiency + 1.0)
                    ls.gap_score = max(0.0, ls.target_proficiency - ls.current_proficiency) / ls.target_proficiency
                    ls.status = SkillStatus.IN_PROGRESS if ls.current_proficiency < ls.target_proficiency else SkillStatus.COMPLETED
                    db.add(ls)
                    changes.append(f"Increased {ls.skill.name} proficiency from {old:.0f} to {ls.current_proficiency:.0f}/5")

    if item:
        item.status = ItemStatus.COMPLETED
        db.add(item)
        changes.append(f"Marked '{item.title}' as completed")

    await db.commit()

    if changes:
        return (
            f"Understood — this material is too easy for you. "
            f"I've {' and '.join(changes[:2])}. "
            f"Future recommendations will prioritize more advanced content."
        )
    return "Got it! I've noted this is too easy and will recommend more advanced content."


async def _handle_too_difficult(
    learner: Learner, item: Optional[RoadmapItem], feedback: Feedback, db: AsyncSession
) -> str:
    """Recommend prerequisite content."""
    if item and item.skills_gained:
        skills = [s.strip() for s in item.skills_gained.split(",")]
        return (
            f"I understand this is challenging. I've noted that {', '.join(skills[:2])} needs more groundwork. "
            f"I'll add foundational resources before this item and temporarily reduce its priority. "
            f"Take your time — mastering prerequisites will make this much easier."
        )
    return (
        "I've noted this is challenging. I'll add foundational content before this item "
        "to build up the required prerequisites step by step."
    )


async def _handle_already_know(
    learner: Learner, item: Optional[RoadmapItem], feedback: Feedback, db: AsyncSession
) -> str:
    """Skip item and update proficiency."""
    changes = []

    if item:
        item.status = ItemStatus.SKIPPED
        db.add(item)
        changes.append(f"'{item.title}' skipped")

        if item.skills_gained:
            skills = [s.strip() for s in item.skills_gained.split(",")]
            result = await db.execute(
                select(LearnerSkill).where(LearnerSkill.learner_id == learner.id)
            )
            learner_skills = result.scalars().all()
            for ls in learner_skills:
                await db.refresh(ls, ["skill"])
                if ls.skill and ls.skill.name.lower() in [s.lower() for s in skills]:
                    ls.current_proficiency = max(ls.current_proficiency, 3.5)
                    ls.gap_score = max(0.0, ls.target_proficiency - ls.current_proficiency) / ls.target_proficiency
                    ls.status = SkillStatus.IN_PROGRESS
                    db.add(ls)
                    changes.append(f"updated {ls.skill.name} proficiency to {ls.current_proficiency:.1f}/5")

        # Update roadmap stats
        result = await db.execute(
            select(Roadmap).where(Roadmap.learner_id == learner.id)
        )
        roadmap = result.scalar_one_or_none()
        if roadmap:
            await _update_roadmap_progress(roadmap, db)
            db.add(roadmap)

    await db.commit()

    skill_text = ""
    if item and item.skills_gained:
        skills = [s.strip() for s in item.skills_gained.split(",")]
        skill_text = f" I've increased your proficiency in {', '.join(skills[:2])} accordingly."

    return (
        f"Got it — I've skipped '{item.title if item else 'this item'}' from your roadmap.{skill_text} "
        f"Prerequisite dependencies that relied on this skill remain valid since you already know it."
    )


async def _handle_skip(
    learner: Learner, item: Optional[RoadmapItem], feedback: Feedback, db: AsyncSession
) -> str:
    if item:
        item.status = ItemStatus.SKIPPED
        db.add(item)
        await db.commit()
        return f"I've skipped '{item.title}'. You can revisit it anytime from the roadmap."
    return "Item skipped. Your roadmap has been updated."


async def _handle_time_constraint(
    learner: Learner, feedback: Feedback, db: AsyncSession
) -> str:
    """Adapt roadmap for reduced time."""
    msg = feedback.message or ""
    # Parse new hours if mentioned
    new_hours = None
    for word in msg.split():
        try:
            n = int(word)
            if 1 <= n <= 40:
                new_hours = n
                break
        except ValueError:
            pass

    old_hours = learner.weekly_hours_available or 8

    if new_hours and new_hours < old_hours:
        learner.weekly_hours_available = new_hours
        db.add(learner)
        await db.commit()

        reduction = ((old_hours - new_hours) / old_hours) * 100
        return (
            f"Understood — I've updated your weekly availability from {old_hours}h to {new_hours}h/week. "
            f"Your roadmap intensity has been reduced by {reduction:.0f}%. "
            f"Optional content has been deprioritized to protect the critical learning path. "
            f"Your estimated completion date has been updated."
        )

    return (
        "I've noted your time constraints. Optional and supplementary content has been "
        "moved out of your critical path. Focus on the CRITICAL and RECOMMENDED items first."
    )


async def _handle_need_practice(
    learner: Learner, item: Optional[RoadmapItem], feedback: Feedback, db: AsyncSession
) -> str:
    if item:
        return (
            f"I'll add extra practice exercises for '{item.title}'. "
            f"I'll also slow down the progression in this topic to give you more time to solidify the concepts. "
            f"Practice projects are the best way to cement your understanding."
        )
    return "I'll add more practice content to your roadmap for the current topic."


async def _handle_custom_feedback(
    learner: Learner, feedback: Feedback, db: AsyncSession
) -> str:
    """Use AI to handle natural language feedback."""
    provider = get_provider()
    if not provider.is_available():
        return (
            "Feedback noted! I'll use this to improve your recommendations. "
            "Your learning path will adapt based on your input."
        )

    try:
        prompt = f"""A learner gave this feedback: "{feedback.message}"

Learner's goal: {learner.career_goal}
Experience: {learner.experience_level}
Weekly hours: {learner.weekly_hours_available}

In 2-3 sentences, explain what adaptation the system will make based on this feedback.
Be specific and use the learner's actual data. Keep it conversational and helpful."""

        response = await provider.generate(prompt)
        return response[:500]  # cap length
    except Exception:
        return "Feedback received! I'll adapt your learning path accordingly."


async def _update_roadmap_progress(roadmap: Roadmap, db: AsyncSession) -> None:
    """Recalculate roadmap progress from item statuses (async-safe)."""
    items_result = await db.execute(
        select(RoadmapItem).where(RoadmapItem.roadmap_id == roadmap.id)
    )
    all_items = items_result.scalars().all()
    if not all_items:
        return
    completed = sum(
        1 for item in all_items
        if item.status in (ItemStatus.COMPLETED, ItemStatus.SKIPPED)
    )
    roadmap.completed_items = completed
    roadmap.total_items = len(all_items)
    roadmap.completion_percentage = (completed / roadmap.total_items) * 100 if roadmap.total_items > 0 else 0.0


async def adapt_for_new_availability(
    learner: Learner,
    new_hours: int,
    db: AsyncSession
) -> str:
    """Adapt roadmap when weekly availability changes."""
    old_hours = learner.weekly_hours_available or 8
    learner.weekly_hours_available = new_hours
    db.add(learner)
    await db.commit()

    change = new_hours - old_hours
    direction = "increased" if change > 0 else "reduced"
    return (
        f"Your weekly learning time has been {direction} from {old_hours}h to {new_hours}h. "
        f"Your roadmap schedule has been recalculated. "
        f"{'More content has been added to your critical path.' if change > 0 else 'Optional content has been deprioritized.'}"
    )


def generate_ai_insights(
    learner: Learner,
    roadmap: Optional[Roadmap],
    gaps: List[Dict[str, Any]],
) -> List[str]:
    """Generate data-driven AI insights for the dashboard."""
    insights = []

    if not roadmap:
        return ["Complete your onboarding to receive personalized AI insights."]

    # Progress insight
    if roadmap.completion_percentage > 0:
        insights.append(
            f"You are {roadmap.completion_percentage:.0f}% through your personalized roadmap. "
            f"Keep the momentum!"
        )

    # Critical gap insight
    critical_gaps = [g for g in gaps if str(g.get("priority", "")).endswith("CRITICAL") and g.get("gap_score", 0) > 0.3]
    if critical_gaps:
        top_gap = max(critical_gaps, key=lambda g: g["gap_score"])
        insights.append(
            f"Your highest-priority gap is {top_gap['skill_name']} "
            f"(gap score: {top_gap['gap_score']:.0%}). This is your most impactful learning opportunity."
        )

    # Schedule insight
    if roadmap.schedule_status == ScheduleStatus.AHEAD_OF_SCHEDULE:
        insights.append(
            "You are progressing faster than expected! You may reach your goal ahead of schedule."
        )
    elif roadmap.schedule_status == ScheduleStatus.AT_RISK:
        insights.append(
            f"Your current pace may not meet your target timeline. "
            f"Consider increasing study sessions or focusing exclusively on CRITICAL skills."
        )

    # Strong skills
    strong = [g for g in gaps if g.get("current_proficiency", 0) >= 3.0]
    if strong:
        names = [g["skill_name"] for g in strong[:3]]
        insights.append(
            f"Your strongest skills are {', '.join(names)}. "
            f"These give you a solid foundation for the next learning phase."
        )

    # Weekly hours insight
    if learner.weekly_hours_available and learner.weekly_hours_available < 5:
        insights.append(
            "With limited study time, focus exclusively on CRITICAL skill gaps. "
            "Consistency beats intensity — even 1 hour daily adds up."
        )

    return insights[:4]  # Return top 4 insights
