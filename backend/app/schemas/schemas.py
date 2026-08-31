"""Pydantic schemas for the AI Learning Path Recommender API."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field

from app.models.models import (
    ExperienceLevel, LearningStyle, SkillCategory, SkillPriority,
    SkillStatus, ResourceType, ResourceDifficulty, ItemType, ItemStatus,
    RoadmapStatus, ScheduleStatus, FeedbackType, AssessmentStatus, MessageRole
)


# ─────────────────────────── LEARNER ────────────────────────────────────────

class LearnerCreate(BaseModel):
    name: str
    email: str
    career_goal: Optional[str] = None
    goal_description: Optional[str] = None
    experience_level: Optional[ExperienceLevel] = None
    interests: Optional[List[str]] = None
    completed_courses: Optional[List[str]] = None
    previous_projects: Optional[List[str]] = None
    preferred_learning_style: Optional[LearningStyle] = None
    weekly_hours_available: Optional[int] = Field(None, ge=1, le=168)
    target_timeline: Optional[str] = None
    preferred_content_types: Optional[List[str]] = None


class LearnerUpdate(BaseModel):
    name: Optional[str] = None
    career_goal: Optional[str] = None
    goal_description: Optional[str] = None
    experience_level: Optional[ExperienceLevel] = None
    interests: Optional[List[str]] = None
    completed_courses: Optional[List[str]] = None
    previous_projects: Optional[List[str]] = None
    preferred_learning_style: Optional[LearningStyle] = None
    weekly_hours_available: Optional[int] = Field(None, ge=1, le=168)
    target_timeline: Optional[str] = None
    preferred_content_types: Optional[List[str]] = None


class LearnerResponse(BaseModel):
    id: int
    name: str
    email: str
    career_goal: Optional[str] = None
    goal_description: Optional[str] = None
    experience_level: Optional[ExperienceLevel] = None
    interests: Optional[List[str]] = None
    completed_courses: Optional[List[str]] = None
    previous_projects: Optional[List[str]] = None
    preferred_learning_style: Optional[LearningStyle] = None
    weekly_hours_available: Optional[int] = None
    target_timeline: Optional[str] = None
    preferred_content_types: Optional[List[str]] = None
    overall_progress: float = 0.0
    total_hours_learned: int = 0
    current_streak: int = 0
    is_demo_user: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── PROFILE ANALYSIS ───────────────────────────────

class ProfileAnalyzeRequest(BaseModel):
    natural_language_goal: str
    learner_id: Optional[int] = None  # if updating existing learner


class ExtractedProfile(BaseModel):
    career_goal: Optional[str] = None
    target_role: Optional[str] = None
    timeline: Optional[str] = None
    weekly_hours: Optional[int] = None
    experience_level: Optional[ExperienceLevel] = None
    existing_skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    completed_courses: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    learning_style: Optional[LearningStyle] = None
    confidence: float = 0.8
    raw_input: Optional[str] = None


# ─────────────────────────── SKILL ──────────────────────────────────────────

class SkillResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[SkillCategory] = None
    domain: Optional[str] = None
    prerequisites: Optional[List[str]] = None
    difficulty_level: Optional[int] = None

    class Config:
        from_attributes = True


class LearnerSkillResponse(BaseModel):
    id: int
    skill: SkillResponse
    current_proficiency: float  # 0-5
    target_proficiency: float   # 0-5
    gap_score: float            # 0-1
    priority: Optional[SkillPriority] = None
    status: SkillStatus
    confidence: float           # 0-1

    class Config:
        from_attributes = True


# ─────────────────────────── SKILL GAP ──────────────────────────────────────

class SkillGapAnalysisResponse(BaseModel):
    learner_id: int
    goal: str
    strong_skills: List[LearnerSkillResponse]
    critical_gaps: List[LearnerSkillResponse]
    recommended_gaps: List[LearnerSkillResponse]
    optional_gaps: List[LearnerSkillResponse]
    overall_readiness: float  # 0-1
    analysis_summary: str
    skill_graph_nodes: List[Dict[str, Any]]  # for 3D graph
    skill_graph_edges: List[Dict[str, Any]]  # for 3D graph


# ─────────────────────────── RESOURCE ────────────────────────────────────────

class ResourceResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    provider: Optional[str] = None
    url: Optional[str] = None
    type: ResourceType
    difficulty: ResourceDifficulty
    skills_taught: Optional[List[str]] = None
    prerequisite_skills: Optional[List[str]] = None
    estimated_hours: Optional[int] = None
    rating: Optional[float] = None
    popularity_score: int
    is_free: bool

    class Config:
        from_attributes = True


# ─────────────────────────── ROADMAP ────────────────────────────────────────

class ScoringMetadata(BaseModel):
    goal_match: float = 0.0
    skill_gap_match: float = 0.0
    prerequisite_match: float = 0.0
    difficulty_match: float = 0.0
    preference_match: float = 0.0
    time_match: float = 0.0
    progress_match: float = 0.0
    feedback_adjustment: float = 0.0
    total_score: float = 0.0


class RoadmapItemResponse(BaseModel):
    id: int
    phase_number: int
    phase_name: Optional[str] = None
    order_index: int
    title: str
    description: Optional[str] = None
    type: ItemType
    difficulty: ResourceDifficulty
    estimated_hours: int
    skills_gained: Optional[List[str]] = None
    prerequisite_item_ids: Optional[List[int]] = None
    milestone_text: Optional[str] = None
    is_milestone: bool
    status: ItemStatus
    why_recommended: Optional[str] = None
    scoring_metadata: Optional[ScoringMetadata] = None
    project_info: Optional[Dict[str, Any]] = None
    resource: Optional[ResourceResponse] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoadmapResponse(BaseModel):
    id: int
    learner_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    total_phases: int
    current_phase: int
    total_items: int
    completed_items: int
    completion_percentage: float
    status: RoadmapStatus
    estimated_completion_date: Optional[str] = None
    schedule_status: ScheduleStatus
    ai_reasoning: Optional[str] = None
    generated_at: datetime
    updated_at: datetime
    items: List[RoadmapItemResponse] = []

    class Config:
        from_attributes = True


class RoadmapGenerateRequest(BaseModel):
    learner_id: int
    regenerate: bool = False


class UpdateItemStatusRequest(BaseModel):
    status: ItemStatus


# ─────────────────────────── FEEDBACK ───────────────────────────────────────

class FeedbackCreate(BaseModel):
    learner_id: int
    roadmap_item_id: Optional[int] = None
    type: FeedbackType
    message: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    type: FeedbackType
    message: Optional[str] = None
    system_response: Optional[str] = None
    processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── ASSESSMENT ─────────────────────────────────────

class AssessmentQuestionResponse(BaseModel):
    id: int
    question_number: int
    question_text: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    learner_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    explanation: Optional[str] = None
    difficulty: str

    class Config:
        from_attributes = True


class AssessmentResponse(BaseModel):
    id: int
    skill: Optional[SkillResponse] = None
    title: Optional[str] = None
    description: Optional[str] = None
    total_questions: int
    correct_answers: int
    score_percentage: float
    estimated_proficiency: float
    status: AssessmentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    questions: List[AssessmentQuestionResponse] = []

    class Config:
        from_attributes = True


class AssessmentGenerateRequest(BaseModel):
    learner_id: int
    skill_id: int
    num_questions: int = 5


class AssessmentSubmitRequest(BaseModel):
    answers: Dict[int, str]  # question_id -> answer


# ─────────────────────────── CHAT ────────────────────────────────────────────

class ChatRequest(BaseModel):
    learner_id: int
    message: str


class ChatResponse(BaseModel):
    id: int
    role: MessageRole
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── RECOMMENDATIONS ────────────────────────────────

class RecommendationItem(BaseModel):
    item_id: int
    title: str
    type: ItemType
    score: float
    rank: int
    why_recommended: str
    scoring_metadata: ScoringMetadata
    resource: Optional[ResourceResponse] = None
    estimated_hours: int
    skills_gained: Optional[List[str]] = None


class RecommendationsResponse(BaseModel):
    learner_id: int
    recommendations: List[RecommendationItem]
    next_best_action: Optional[RecommendationItem] = None
    generated_at: datetime


# ─────────────────────────── DASHBOARD ──────────────────────────────────────

class DashboardResponse(BaseModel):
    learner: LearnerResponse
    overall_progress: float
    skills_developed: int
    total_hours_learned: int
    current_phase: int
    total_phases: int
    milestones_completed: int
    milestones_total: int
    deadline_status: ScheduleStatus
    streak: int
    skill_gap_summary: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    next_best_action: Optional[RecommendationItem] = None
    ai_insights: List[str]
    roadmap_summary: Dict[str, Any]


# ─────────────────────────── NEXT BEST ACTION ────────────────────────────────

class NextBestAction(BaseModel):
    action: str
    reason: str
    skill: Optional[str] = None
    priority: str
    estimated_time: int  # minutes
    impact: str
    confidence: float
    roadmap_item_id: Optional[int] = None


# ─────────────────────────── HEALTH ──────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    ai_available: bool
    database: str
    version: str = "1.0.0"
