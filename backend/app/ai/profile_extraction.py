"""Profile extraction service — parses natural language goals into structured profiles."""

import json
import logging
from typing import Optional

from app.ai.provider import get_provider
from app.schemas.schemas import ExtractedProfile
from app.models.models import ExperienceLevel, LearningStyle

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an expert learning profile analyzer.
Extract structured learning profile information from natural language descriptions.
Be smart — infer experience level from context clues.
Always respond with valid JSON matching the exact schema provided."""

EXTRACTION_PROMPT_TEMPLATE = """Analyze this learning goal and extract a structured profile:

GOAL: "{goal}"

Return a JSON object with these exact fields:
{{
  "career_goal": "full career goal statement",
  "target_role": "specific role name (e.g. Backend Java Developer)",
  "timeline": "timeline string (e.g. '4 months')",
  "weekly_hours": integer or null,
  "experience_level": "BEGINNER|INTERMEDIATE|ADVANCED|EXPERT",
  "existing_skills": ["list", "of", "skills"],
  "interests": ["list", "of", "interests"],
  "completed_courses": ["list", "of", "completed", "courses"],
  "projects": ["list", "of", "past", "projects"],
  "learning_style": "VISUAL|READING|HANDS_ON|VIDEO|MIXED",
  "confidence": 0.0 to 1.0
}}

Rules:
- If they mention knowing a technology, add it to existing_skills
- Infer experience_level from language: "beginner"/"new to"=BEGINNER, "basic knowledge"=INTERMEDIATE, "experience with"=INTERMEDIATE/ADVANCED
- If no timeline mentioned, set to null
- confidence should reflect how clear the input was (0.5 for vague, 0.9 for clear)
- learning_style: default to MIXED if not specified"""


async def extract_profile(natural_language_goal: str) -> ExtractedProfile:
    """Extract structured profile from natural language using AI."""
    provider = get_provider()
    prompt = EXTRACTION_PROMPT_TEMPLATE.format(goal=natural_language_goal)

    try:
        data = await provider.generate_json(prompt, EXTRACTION_SYSTEM_PROMPT)
        # Validate and normalize
        exp_str = data.get("experience_level", "INTERMEDIATE")
        try:
            exp = ExperienceLevel(exp_str)
        except ValueError:
            exp = ExperienceLevel.INTERMEDIATE

        style_str = data.get("learning_style", "MIXED")
        try:
            style = LearningStyle(style_str)
        except ValueError:
            style = LearningStyle.MIXED

        return ExtractedProfile(
            career_goal=data.get("career_goal"),
            target_role=data.get("target_role"),
            timeline=data.get("timeline"),
            weekly_hours=data.get("weekly_hours"),
            experience_level=exp,
            existing_skills=data.get("existing_skills", []),
            interests=data.get("interests", []),
            completed_courses=data.get("completed_courses", []),
            projects=data.get("projects", []),
            learning_style=style,
            confidence=float(data.get("confidence", 0.8)),
            raw_input=natural_language_goal
        )
    except Exception as e:
        logger.error(f"Profile extraction error: {e}")
        # Return minimal parsed profile
        return _fallback_parse(natural_language_goal)


def _fallback_parse(goal: str) -> ExtractedProfile:
    """Simple keyword-based fallback parser."""
    goal_lower = goal.lower()

    # Experience level detection
    if any(w in goal_lower for w in ["beginner", "new to", "just started", "no experience"]):
        exp = ExperienceLevel.BEGINNER
    elif any(w in goal_lower for w in ["advanced", "expert", "senior", "years of experience"]):
        exp = ExperienceLevel.ADVANCED
    else:
        exp = ExperienceLevel.INTERMEDIATE

    # Skill extraction (common technologies)
    tech_keywords = [
        "java", "python", "javascript", "typescript", "sql", "mysql", "postgresql",
        "spring", "spring boot", "react", "angular", "vue", "node", "docker",
        "kubernetes", "aws", "git", "rest", "api", "html", "css", "c++", "c#",
        "mongodb", "redis", "kafka", "microservices", "oop", "data structures"
    ]
    found_skills = [t for t in tech_keywords if t in goal_lower]

    # Hours detection
    hours = None
    for phrase in ["hours per week", "hours a week", "hours/week"]:
        idx = goal_lower.find(phrase)
        if idx > 0:
            words = goal_lower[:idx].split()
            if words and words[-1].isdigit():
                hours = int(words[-1])
                break

    # Timeline detection
    timeline = None
    for unit in ["month", "week", "year"]:
        idx = goal_lower.find(unit)
        if idx > 0:
            words = goal_lower[:idx].split()
            if words and words[-1].isdigit():
                timeline = f"{words[-1]} {unit}s"
                break

    return ExtractedProfile(
        career_goal=goal[:200],
        target_role=None,
        timeline=timeline,
        weekly_hours=hours,
        experience_level=exp,
        existing_skills=found_skills,
        interests=[],
        completed_courses=[],
        projects=[],
        learning_style=LearningStyle.MIXED,
        confidence=0.5,
        raw_input=goal
    )
