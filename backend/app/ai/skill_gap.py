"""Skill Gap Analysis Engine — determines current vs required skills and priorities."""

import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import (
    Learner, Skill, LearnerSkill, SkillPriority, SkillStatus
)
from app.ai.provider import get_provider

logger = logging.getLogger(__name__)


# Goal → Required Skills mapping (deterministic knowledge base for major domains)
GOAL_SKILL_REQUIREMENTS: Dict[str, List[Dict[str, Any]]] = {
    "dbms and sql specialist": [
        {"name": "SQL", "target": 5, "priority": "CRITICAL"},
        {"name": "Relational Modeling", "target": 4, "priority": "CRITICAL"},
        {"name": "DDL & DML Queries", "target": 4, "priority": "CRITICAL"},
        {"name": "Advanced Joins & Subqueries", "target": 4, "priority": "CRITICAL"},
        {"name": "Indexing & Optimization", "target": 4, "priority": "CRITICAL"},
        {"name": "Transactions & ACID", "target": 4, "priority": "CRITICAL"},
        {"name": "Database Normalization", "target": 3, "priority": "RECOMMENDED"},
        {"name": "PostgreSQL", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Stored Procedures & Views", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Database Security & Backups", "target": 2, "priority": "OPTIONAL"},
        {"name": "NoSQL Basics", "target": 2, "priority": "OPTIONAL"},
    ],
    "backend java developer": [
        {"name": "Core Java", "target": 4, "priority": "CRITICAL"},
        {"name": "OOP", "target": 3, "priority": "CRITICAL"},
        {"name": "Spring Boot", "target": 4, "priority": "CRITICAL"},
        {"name": "REST APIs", "target": 4, "priority": "CRITICAL"},
        {"name": "SQL", "target": 3, "priority": "CRITICAL"},
        {"name": "JPA/Hibernate", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Spring Security", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Testing", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Maven/Gradle", "target": 2, "priority": "RECOMMENDED"},
        {"name": "Git", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Docker", "target": 2, "priority": "OPTIONAL"},
        {"name": "Microservices", "target": 2, "priority": "OPTIONAL"},
        {"name": "Redis", "target": 2, "priority": "OPTIONAL"},
    ],
    "fullstack developer": [
        {"name": "HTML/CSS", "target": 4, "priority": "CRITICAL"},
        {"name": "JavaScript", "target": 4, "priority": "CRITICAL"},
        {"name": "React", "target": 4, "priority": "CRITICAL"},
        {"name": "Node.js", "target": 3, "priority": "CRITICAL"},
        {"name": "REST APIs", "target": 4, "priority": "CRITICAL"},
        {"name": "SQL", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Git", "target": 3, "priority": "RECOMMENDED"},
        {"name": "TypeScript", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Docker", "target": 2, "priority": "OPTIONAL"},
    ],
    "data scientist": [
        {"name": "Python", "target": 4, "priority": "CRITICAL"},
        {"name": "Statistics", "target": 4, "priority": "CRITICAL"},
        {"name": "Machine Learning", "target": 4, "priority": "CRITICAL"},
        {"name": "Pandas", "target": 4, "priority": "CRITICAL"},
        {"name": "SQL", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Data Visualization", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Deep Learning", "target": 3, "priority": "OPTIONAL"},
        {"name": "Cloud (AWS/GCP)", "target": 2, "priority": "OPTIONAL"},
    ],
    "devops engineer": [
        {"name": "Linux", "target": 4, "priority": "CRITICAL"},
        {"name": "Docker", "target": 4, "priority": "CRITICAL"},
        {"name": "Kubernetes", "target": 4, "priority": "CRITICAL"},
        {"name": "CI/CD", "target": 4, "priority": "CRITICAL"},
        {"name": "Cloud (AWS/GCP)", "target": 3, "priority": "CRITICAL"},
        {"name": "Python", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Git", "target": 4, "priority": "CRITICAL"},
        {"name": "Monitoring", "target": 3, "priority": "RECOMMENDED"},
    ],
    "frontend developer": [
        {"name": "HTML/CSS", "target": 5, "priority": "CRITICAL"},
        {"name": "JavaScript", "target": 4, "priority": "CRITICAL"},
        {"name": "React", "target": 4, "priority": "CRITICAL"},
        {"name": "TypeScript", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Testing", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Git", "target": 3, "priority": "RECOMMENDED"},
        {"name": "REST APIs", "target": 3, "priority": "RECOMMENDED"},
    ],
    "backend python developer": [
        {"name": "Python", "target": 5, "priority": "CRITICAL"},
        {"name": "OOP", "target": 4, "priority": "CRITICAL"},
        {"name": "FastAPI", "target": 4, "priority": "CRITICAL"},
        {"name": "REST APIs", "target": 4, "priority": "CRITICAL"},
        {"name": "SQL", "target": 4, "priority": "CRITICAL"},
        {"name": "PostgreSQL", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Docker", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Testing", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Redis", "target": 2, "priority": "OPTIONAL"},
    ],
    "machine learning engineer": [
        {"name": "Python", "target": 5, "priority": "CRITICAL"},
        {"name": "Machine Learning", "target": 5, "priority": "CRITICAL"},
        {"name": "Deep Learning", "target": 4, "priority": "CRITICAL"},
        {"name": "Statistics", "target": 4, "priority": "CRITICAL"},
        {"name": "SQL", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Cloud (AWS/GCP)", "target": 3, "priority": "RECOMMENDED"},
        {"name": "MLOps", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Docker", "target": 3, "priority": "OPTIONAL"},
    ],
}

# Default fallback for unknown roles
DEFAULT_SKILL_REQUIREMENTS = [
    {"name": "Programming Fundamentals", "target": 3, "priority": "CRITICAL"},
    {"name": "Core Concepts", "target": 4, "priority": "CRITICAL"},
    {"name": "Hands-on Implementation", "target": 4, "priority": "CRITICAL"},
    {"name": "Best Practices & Optimization", "target": 3, "priority": "RECOMMENDED"},
    {"name": "Project Building", "target": 4, "priority": "RECOMMENDED"},
]


async def analyze_skill_gaps(
    learner: Learner,
    db: AsyncSession,
    use_ai: bool = True
) -> List[Dict[str, Any]]:
    """
    Analyze skill gaps for a learner.

    Returns list of skill gap records with:
    - skill info
    - current_proficiency
    - target_proficiency
    - gap_score
    - priority
    """
    # 1. Check if AI can analyze directly from learner's natural language goal
    required_skills = None
    if use_ai and get_provider().is_available():
        try:
            required_skills = await _ai_extract_skill_requirements(learner)
        except Exception as e:
            logger.warning(f"AI skill requirements extraction failed, using template/fallback: {e}")

    # 2. If AI didn't return or was unavailable, use domain template or keyword fallback
    if not required_skills:
        target_role = _extract_target_role(learner)
        required_skills = _get_required_skills(target_role, learner)

    # Load existing learner skills from database
    existing_stmt = select(LearnerSkill).where(
        LearnerSkill.learner_id == learner.id
    )
    result = await db.execute(existing_stmt)
    existing_skills: List[LearnerSkill] = result.scalars().all()

    # Map existing skills by name (lowercase)
    existing_map: Dict[str, LearnerSkill] = {}
    for ls in existing_skills:
        await db.refresh(ls, ["skill"])
        if ls.skill:
            existing_map[ls.skill.name.lower()] = ls

    # Parse learner's self-reported skills from profile
    self_reported = _parse_self_reported_skills(learner)

    # Compute gap analysis
    gaps = []
    for req in required_skills:
        skill_name = req["name"]
        target_prof = float(req.get("target", 4))
        priority_str = str(req.get("priority", "RECOMMENDED")).upper()

        # Find current proficiency
        current_prof = 0.0
        ls = existing_map.get(skill_name.lower())
        if ls:
            current_prof = ls.current_proficiency
        elif skill_name.lower() in self_reported:
            current_prof = self_reported[skill_name.lower()]

        gap = max(0.0, target_prof - current_prof)
        gap_score = gap / target_prof if target_prof > 0 else 0.0

        # Map priority string to enum
        try:
            priority = SkillPriority(priority_str)
        except ValueError:
            priority = SkillPriority.RECOMMENDED

        gaps.append({
            "skill_name": skill_name,
            "current_proficiency": current_prof,
            "target_proficiency": target_prof,
            "gap_score": gap_score,
            "gap_absolute": gap,
            "priority": priority,
            "status": SkillStatus.COMPLETED if current_prof >= target_prof else SkillStatus.NOT_STARTED,
        })

    return gaps


def _extract_target_role(learner: Learner) -> str:
    """Extract target role from learner's goal description using smart keyword matching."""
    texts = []
    if learner.career_goal:
        texts.append(learner.career_goal.lower())
    if learner.goal_description:
        texts.append(learner.goal_description.lower())
    combined = " ".join(texts)

    domain_matchers = [
        ("fullstack developer", ["fullstack", "full stack", "full-stack", "mern", "mean"]),
        ("frontend developer", ["frontend", "front end", "react developer", "ui/ux", "web design"]),
        ("data scientist", ["data science", "data scientist", "data analysis", "data analyst", "pandas", "statistics"]),
        ("machine learning engineer", ["machine learning", "ml engineer", "deep learning", "ai engineer", "artificial intelligence", "nlp", "computer vision", "llm"]),
        ("devops engineer", ["devops", "cloud engineer", "aws", "kubernetes", "k8s", "ci/cd", "infrastructure", "terraform"]),
        ("backend python developer", ["python developer", "python backend", "fastapi", "django", "flask"]),
        ("backend java developer", ["java developer", "spring boot", "spring framework", "backend java", "core java"]),
        ("dbms and sql specialist", ["dbms", "database", "sql", "queries", "query", "postgres", "postgresql", "mysql", "rdbms", "relational", "sqlite"]),
    ]

    best_role = None
    best_score = 0

    for role_name, keywords in domain_matchers:
        score = sum(len(kw) for kw in keywords if kw in combined)
        if score > best_score:
            best_score = score
            best_role = role_name

    if best_role:
        return best_role

    return "custom"


def _get_required_skills(target_role: str, learner: Optional[Learner] = None) -> List[Dict[str, Any]]:
    """Get required skills for a target role, or synthesize dynamically from learner's goal."""
    if target_role in GOAL_SKILL_REQUIREMENTS:
        return GOAL_SKILL_REQUIREMENTS[target_role]

    if learner:
        return _synthesize_skills_from_goal(learner)

    return DEFAULT_SKILL_REQUIREMENTS


def _synthesize_skills_from_goal(learner: Learner) -> List[Dict[str, Any]]:
    """Synthesize structured technical skills from any freeform learning goal."""
    goal_raw = learner.career_goal or learner.goal_description or "Software Engineering"
    # Clean goal title
    clean_title = goal_raw.replace("I want to learn", "").replace("I want to master", "").replace("I want to become a", "").replace("I want to become an", "").strip().title()
    if len(clean_title) > 30:
        clean_title = clean_title.split()[0] + " " + clean_title.split()[1] if len(clean_title.split()) > 1 else clean_title[:20]

    # Extract any tech tokens
    interests = []
    if learner.interests:
        try:
            interests = json.loads(learner.interests)
        except Exception:
            pass

    primary_tech = interests[0] if interests else clean_title

    return [
        {"name": f"{primary_tech} Core Fundamentals", "target": 4, "priority": "CRITICAL"},
        {"name": f"{primary_tech} Architecture & Design", "target": 4, "priority": "CRITICAL"},
        {"name": f"{primary_tech} Practical Tooling & Libraries", "target": 4, "priority": "CRITICAL"},
        {"name": f"Advanced {primary_tech} Techniques", "target": 3, "priority": "RECOMMENDED"},
        {"name": f"Testing & Debugging for {primary_tech}", "target": 3, "priority": "RECOMMENDED"},
        {"name": f"Performance Optimization & Production Delivery", "target": 3, "priority": "RECOMMENDED"},
        {"name": "Version Control & Project Management", "target": 3, "priority": "OPTIONAL"},
    ]


def _parse_self_reported_skills(learner: Learner) -> Dict[str, float]:
    """Parse self-reported skills from learner interests/profile and goal text."""
    skill_map: Dict[str, float] = {}

    goal_text = f"{learner.career_goal or ''} {learner.goal_description or ''}".lower()

    # If user mentions "I know X" or "familiar with X"
    tech_keywords = {
        "java": "core java", "python": "python", "sql": "sql", "queries": "sql",
        "react": "react", "javascript": "javascript", "html": "html/css", "css": "html/css",
        "docker": "docker", "git": "git", "spring": "spring boot", "linux": "linux",
        "postgres": "postgresql", "database": "sql", "oop": "oop", "fastapi": "fastapi",
    }
    for kw, skill in tech_keywords.items():
        if f"know {kw}" in goal_text or f"familiar with {kw}" in goal_text or f"basic {kw}" in goal_text:
            skill_map[skill] = 2.5
        elif f"experience in {kw}" in goal_text or f"expert in {kw}" in goal_text:
            skill_map[skill] = 4.0

    # Parse completed courses
    if learner.completed_courses:
        try:
            courses = json.loads(learner.completed_courses)
            for course in courses:
                cl = course.lower()
                for kw, sname in tech_keywords.items():
                    if kw in cl:
                        skill_map[sname] = max(skill_map.get(sname, 0), 3.0)
        except Exception:
            pass

    # Parse interests
    if learner.interests:
        try:
            interests = json.loads(learner.interests)
            for interest in interests:
                il = interest.lower()
                for kw, sname in tech_keywords.items():
                    if kw in il:
                        skill_map[sname] = max(skill_map.get(sname, 0), 2.0)
        except Exception:
            pass

    return skill_map


async def _ai_extract_skill_requirements(learner: Learner) -> Optional[List[Dict[str, Any]]]:
    """Use AI to extract precise required skills directly from any custom goal description."""
    provider = get_provider()
    if not provider.is_available():
        return None

    prompt = f"""Analyze this learner's specific goal and return the 6 to 10 most critical skills needed to master it:

GOAL: "{learner.career_goal or ''}"
DETAILED DESCRIPTION: "{learner.goal_description or ''}"
EXPERIENCE LEVEL: "{learner.experience_level or 'INTERMEDIATE'}"

Return ONLY a JSON array with this exact structure:
[
  {{
    "name": "Skill Name",
    "target": 4,
    "priority": "CRITICAL"
  }}
]

Rules:
- priority must be one of: "CRITICAL", "RECOMMENDED", "OPTIONAL"
- target must be a number between 2 and 5
- Ensure the skills are tightly tailored to their exact goal (e.g. if they asked for DBMS/SQL, include SQL, Relational Modeling, Indexing, Transactions, Query Optimization; if they asked for Flutter, include Dart, Flutter Widgets, State Management, etc.)
- Do NOT output any markdown blocks or explanation, ONLY the valid JSON array."""

    try:
        data = await provider.generate_json(prompt)
        if isinstance(data, list) and len(data) > 0:
            return data
        if isinstance(data, dict) and "skills" in data:
            return data["skills"]
    except Exception as e:
        logger.warning(f"AI skill requirements extraction failed: {e}")
    return None


def calculate_overall_readiness(gaps: List[Dict[str, Any]]) -> float:
    """Calculate overall readiness score (0-1) from gap analysis."""
    if not gaps:
        return 0.0

    critical = [g for g in gaps if g.get("priority") == SkillPriority.CRITICAL]
    if not critical:
        return 1.0

    total_gap = sum(g["gap_score"] for g in critical)
    readiness = 1.0 - (total_gap / len(critical))
    return max(0.0, min(1.0, readiness))


def build_skill_graph(skills_data: List[Dict], existing_skills: List[str]) -> Tuple[List[Dict], List[Dict]]:
    """Build nodes and edges for 3D skill dependency graph."""
    nodes = []
    edges = []

    PREREQUISITES = {
        "Spring Boot": ["Core Java", "OOP"],
        "REST APIs": ["Spring Boot", "HTTP Basics"],
        "JPA/Hibernate": ["SQL", "Spring Boot"],
        "Spring Security": ["Spring Boot", "REST APIs"],
        "Testing": ["Core Java", "Spring Boot"],
        "Microservices": ["Spring Boot", "Docker", "REST APIs"],
        "React": ["JavaScript", "HTML/CSS"],
        "TypeScript": ["JavaScript"],
        "Node.js": ["JavaScript"],
        "Deep Learning": ["Machine Learning", "Python"],
        "Machine Learning": ["Python", "Statistics"],
        "Kubernetes": ["Docker", "Linux"],
        "MLOps": ["Machine Learning", "Docker"],
        "Advanced Joins & Subqueries": ["SQL", "DDL & DML Queries"],
        "Indexing & Optimization": ["SQL", "Relational Modeling"],
        "Transactions & ACID": ["SQL", "Relational Modeling"],
        "Database Normalization": ["Relational Modeling"],
        "FastAPI": ["Python", "REST APIs"],
    }

    for i, skill_data in enumerate(skills_data):
        name = skill_data["skill_name"]
        current = skill_data["current_proficiency"]
        target = skill_data["target_proficiency"]
        priority = skill_data["priority"]
        gap = skill_data["gap_score"]

        # Determine node state
        if current >= target:
            state = "COMPLETED"
        elif current >= target * 0.5:
            state = "IN_PROGRESS"
        elif priority == SkillPriority.CRITICAL:
            state = "CRITICAL"
        elif priority == SkillPriority.OPTIONAL:
            state = "OPTIONAL"
        else:
            state = "MISSING"

        nodes.append({
            "id": name,
            "label": name,
            "state": state,
            "current_proficiency": current,
            "target_proficiency": target,
            "gap_score": gap,
            "priority": str(priority.value) if hasattr(priority, 'value') else str(priority),
            "x": (i % 5) * 2.5 - 5,
            "y": -(i // 5) * 2,
            "z": 0,
        })

        # Add edges for prerequisites
        prereqs = PREREQUISITES.get(name, [])
        for prereq in prereqs:
            edges.append({
                "source": prereq,
                "target": name,
                "type": "PREREQUISITE"
            })

    return nodes, edges
