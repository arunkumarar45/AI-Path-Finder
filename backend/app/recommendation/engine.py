"""
Recommendation Engine — scores and ranks learning items for each learner.

Score formula (weights configurable):
  score = 0.25 * goal_match
        + 0.25 * skill_gap_match
        + 0.15 * prerequisite_match
        + 0.10 * difficulty_match
        + 0.10 * preference_match
        + 0.05 * time_match
        + 0.05 * progress_match
        + 0.05 * feedback_adjustment
"""

import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from app.models.models import (
    Learner, LearnerSkill, RoadmapItem, Feedback, FeedbackType,
    ResourceDifficulty, ExperienceLevel, ItemStatus, SkillPriority
)

logger = logging.getLogger(__name__)

# Recommendation score weights
WEIGHTS = {
    "goal_match": 0.25,
    "skill_gap_match": 0.25,
    "prerequisite_match": 0.15,
    "difficulty_match": 0.10,
    "preference_match": 0.10,
    "time_match": 0.05,
    "progress_match": 0.05,
    "feedback_adjustment": 0.05,
}

# Level → numeric
EXPERIENCE_MAP = {
    ExperienceLevel.BEGINNER: 1,
    ExperienceLevel.INTERMEDIATE: 3,
    ExperienceLevel.ADVANCED: 4,
    ExperienceLevel.EXPERT: 5,
}

DIFFICULTY_MAP = {
    ResourceDifficulty.BEGINNER: 1,
    ResourceDifficulty.INTERMEDIATE: 3,
    ResourceDifficulty.ADVANCED: 4,
    ResourceDifficulty.EXPERT: 5,
}


class ScoringResult:
    def __init__(self):
        self.goal_match: float = 0.0
        self.skill_gap_match: float = 0.0
        self.prerequisite_match: float = 0.0
        self.difficulty_match: float = 0.0
        self.preference_match: float = 0.0
        self.time_match: float = 0.0
        self.progress_match: float = 0.0
        self.feedback_adjustment: float = 0.0
        self.total_score: float = 0.0

    def compute(self) -> float:
        self.total_score = (
            WEIGHTS["goal_match"] * self.goal_match
            + WEIGHTS["skill_gap_match"] * self.skill_gap_match
            + WEIGHTS["prerequisite_match"] * self.prerequisite_match
            + WEIGHTS["difficulty_match"] * self.difficulty_match
            + WEIGHTS["preference_match"] * self.preference_match
            + WEIGHTS["time_match"] * self.time_match
            + WEIGHTS["progress_match"] * self.progress_match
            + WEIGHTS["feedback_adjustment"] * self.feedback_adjustment
        )
        return self.total_score

    def to_dict(self) -> Dict[str, float]:
        return {
            "goal_match": round(self.goal_match, 3),
            "skill_gap_match": round(self.skill_gap_match, 3),
            "prerequisite_match": round(self.prerequisite_match, 3),
            "difficulty_match": round(self.difficulty_match, 3),
            "preference_match": round(self.preference_match, 3),
            "time_match": round(self.time_match, 3),
            "progress_match": round(self.progress_match, 3),
            "feedback_adjustment": round(self.feedback_adjustment, 3),
            "total_score": round(self.total_score, 3),
        }


def score_roadmap_item(
    item: RoadmapItem,
    learner: Learner,
    learner_skills: List[LearnerSkill],
    feedbacks: List[Feedback],
    completed_item_ids: List[int],
    all_items: List[RoadmapItem],
) -> ScoringResult:
    """Score a single roadmap item for a given learner."""
    score = ScoringResult()

    # ── 1. Goal match — critical items for the goal score highest ──
    # Use priority from skills gained
    if item.skills_gained:
        gained_lower = item.skills_gained.lower()
        # Check how many skills gained match high-priority learner skills
        critical_skills = {
            ls.skill.name.lower() for ls in learner_skills
            if ls.priority == SkillPriority.CRITICAL and ls.skill
        }
        gained_list = [s.strip().lower() for s in gained_lower.split(",")]
        critical_matches = len([s for s in gained_list if s in critical_skills])
        score.goal_match = min(1.0, critical_matches / max(1, len(gained_list)))
    else:
        score.goal_match = 0.5  # neutral

    # ── 2. Skill gap match — items targeting biggest gaps score highest ──
    if item.skills_gained:
        gained_list = [s.strip().lower() for s in item.skills_gained.split(",")]
        gap_scores = []
        for ls in learner_skills:
            if ls.skill and ls.skill.name.lower() in gained_list:
                gap_scores.append(ls.gap_score)
        if gap_scores:
            score.skill_gap_match = sum(gap_scores) / len(gap_scores)
        else:
            score.skill_gap_match = 0.3
    else:
        score.skill_gap_match = 0.3

    # ── 3. Prerequisite match — items with met prerequisites score higher ──
    if item.prerequisite_item_ids:
        try:
            prereq_ids = [int(x.strip()) for x in item.prerequisite_item_ids.split(",") if x.strip()]
            if prereq_ids:
                met = sum(1 for pid in prereq_ids if pid in completed_item_ids)
                score.prerequisite_match = met / len(prereq_ids)
            else:
                score.prerequisite_match = 1.0
        except ValueError:
            score.prerequisite_match = 1.0
    else:
        score.prerequisite_match = 1.0  # no prerequisites = always eligible

    # ── 4. Difficulty match — item difficulty vs learner level ──
    learner_level = EXPERIENCE_MAP.get(learner.experience_level, 3)
    item_level = DIFFICULTY_MAP.get(item.difficulty, 3)
    diff_delta = abs(item_level - learner_level)
    score.difficulty_match = max(0.0, 1.0 - (diff_delta / 4))

    # ── 5. Preference match — content type vs learner preferences ──
    if learner.preferred_content_types:
        try:
            prefs = [p.lower() for p in json.loads(learner.preferred_content_types)]
            item_type_str = item.type.value.lower() if item.type else ""
            if any(p in item_type_str or item_type_str in p for p in prefs):
                score.preference_match = 1.0
            else:
                score.preference_match = 0.5
        except Exception:
            score.preference_match = 0.6
    else:
        score.preference_match = 0.6

    # ── 6. Time match — short items score higher if learner has limited time ──
    if learner.weekly_hours_available:
        # Normalize: 2h item with 8h/week = good match, 10h item with 2h/week = poor
        available_per_session = (learner.weekly_hours_available / 4)  # ~4 sessions
        item_hours = item.estimated_hours or 2
        if item_hours <= available_per_session:
            score.time_match = 1.0
        else:
            score.time_match = max(0.1, available_per_session / item_hours)
    else:
        score.time_match = 0.7

    # ── 7. Progress match — items next in sequence after completed ──
    if item.order_index > 0:
        # Check if previous item in phase is done
        prev_items = [i for i in all_items
                      if i.phase_number == item.phase_number
                      and i.order_index == item.order_index - 1]
        if prev_items and prev_items[0].id in completed_item_ids:
            score.progress_match = 1.0
        elif not prev_items:
            score.progress_match = 0.8
        else:
            score.progress_match = 0.4
    else:
        score.progress_match = 0.8  # first item in phase

    # ── 8. Feedback adjustment — adjust for past feedback signals ──
    score.feedback_adjustment = _compute_feedback_adjustment(item, feedbacks)

    score.compute()
    return score


def _compute_feedback_adjustment(item: RoadmapItem, feedbacks: List[Feedback]) -> float:
    """Adjust score based on historical feedback patterns."""
    adjustment = 0.5  # neutral baseline

    for fb in feedbacks:
        if fb.roadmap_item_id == item.id:
            if fb.type == FeedbackType.TOO_EASY:
                adjustment -= 0.3  # deprioritize items marked too easy
            elif fb.type == FeedbackType.TOO_DIFFICULT:
                adjustment += 0.1  # slightly boost (still needed)
            elif fb.type == FeedbackType.VERY_USEFUL:
                adjustment += 0.4
            elif fb.type == FeedbackType.SKIP:
                adjustment -= 0.5
            elif fb.type == FeedbackType.ALREADY_KNOW:
                adjustment -= 0.5
            elif fb.type == FeedbackType.NEED_MORE_PRACTICE:
                adjustment += 0.3

    return max(0.0, min(1.0, adjustment))


def generate_recommendation_reason(
    item: RoadmapItem,
    score: ScoringResult,
    learner: Learner,
    learner_skills: List[LearnerSkill],
) -> str:
    """Generate a human-readable recommendation explanation from actual learner data."""
    reasons = []

    # Primary reason from highest scoring factor
    if score.skill_gap_match > 0.7:
        # Find which skills
        if item.skills_gained:
            high_gap_skills = []
            for ls in learner_skills:
                if ls.skill and ls.skill.name.lower() in item.skills_gained.lower():
                    if ls.gap_score > 0.5:
                        high_gap_skills.append(ls.skill.name)
            if high_gap_skills:
                reasons.append(
                    f"{', '.join(high_gap_skills[:2])} {'is' if len(high_gap_skills) == 1 else 'are'} "
                    f"a critical skill gap for your {learner.career_goal or 'goal'}"
                )

    if score.prerequisite_match >= 1.0:
        reasons.append("all prerequisites have been completed")

    if score.goal_match > 0.8:
        reasons.append(f"directly contributes to your goal of becoming a {learner.career_goal or 'developer'}")

    if score.difficulty_match > 0.8:
        exp_label = learner.experience_level.value.lower() if learner.experience_level else "intermediate"
        reasons.append(f"difficulty matches your {exp_label} experience level")

    # Mention existing skills that make this achievable
    if item.skills_gained:
        known_prereqs = []
        for ls in learner_skills:
            if ls.skill and ls.current_proficiency >= 2.0:
                known_prereqs.append(ls.skill.name)
        if known_prereqs[:2]:
            reasons.append(f"you already know {', '.join(known_prereqs[:2])} which are the required foundations")

    if not reasons:
        reasons.append(f"this is the logical next step in your learning sequence")

    reason = ". ".join(r.capitalize() for r in reasons[:3]) + "."
    return reason


def compute_next_best_action(
    items: List[RoadmapItem],
    scores: Dict[int, ScoringResult],
    learner: Learner,
    learner_skills: List[LearnerSkill],
) -> Optional[Dict[str, Any]]:
    """Compute the single best action for the learner right now."""
    # Filter to not-started or in-progress items
    eligible = [
        item for item in items
        if item.status in (ItemStatus.NOT_STARTED, ItemStatus.IN_PROGRESS)
    ]

    if not eligible:
        return None

    # Sort by score
    eligible.sort(key=lambda i: scores.get(i.id, ScoringResult()).total_score, reverse=True)
    top = eligible[0]
    top_score = scores.get(top.id, ScoringResult())

    reason = generate_recommendation_reason(top, top_score, learner, learner_skills)
    minutes = (top.estimated_hours or 2) * 60

    # Determine impact
    if top_score.skill_gap_match > 0.7:
        impact = "HIGH — closes a critical skill gap"
    elif top_score.goal_match > 0.7:
        impact = "HIGH — directly achieves your goal"
    else:
        impact = "MEDIUM — advances your learning progress"

    return {
        "action": top.title,
        "reason": reason,
        "skill": top.skills_gained.split(",")[0].strip() if top.skills_gained else None,
        "priority": "HIGH" if top_score.total_score > 0.75 else "MEDIUM",
        "estimated_time": int(minutes),
        "impact": impact,
        "confidence": round(top_score.total_score, 2),
        "roadmap_item_id": top.id,
    }
