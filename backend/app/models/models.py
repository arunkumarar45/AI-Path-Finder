"""SQLAlchemy ORM models for the AI Learning Path Recommender."""

from datetime import datetime
from typing import Optional, List
import enum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Enum as SAEnum,
    ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.core.database import Base


# ──────────────────────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────────────────────

class ExperienceLevel(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class LearningStyle(str, enum.Enum):
    VISUAL = "VISUAL"
    READING = "READING"
    HANDS_ON = "HANDS_ON"
    VIDEO = "VIDEO"
    MIXED = "MIXED"


class SkillCategory(str, enum.Enum):
    PROGRAMMING_LANGUAGE = "PROGRAMMING_LANGUAGE"
    FRAMEWORK = "FRAMEWORK"
    TOOL = "TOOL"
    CONCEPT = "CONCEPT"
    DATABASE = "DATABASE"
    CLOUD = "CLOUD"
    DEVOPS = "DEVOPS"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"


class SkillPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"


class SkillStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class ResourceType(str, enum.Enum):
    COURSE = "COURSE"
    VIDEO = "VIDEO"
    DOCUMENTATION = "DOCUMENTATION"
    ARTICLE = "ARTICLE"
    PROJECT = "PROJECT"
    PRACTICE = "PRACTICE"
    ASSESSMENT = "ASSESSMENT"
    BOOK = "BOOK"
    TUTORIAL = "TUTORIAL"


class ResourceDifficulty(str, enum.Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class ItemType(str, enum.Enum):
    LEARN = "LEARN"
    PRACTICE = "PRACTICE"
    PROJECT = "PROJECT"
    ASSESSMENT = "ASSESSMENT"
    MILESTONE = "MILESTONE"
    REVIEW = "REVIEW"


class ItemStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class RoadmapStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


class ScheduleStatus(str, enum.Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    AHEAD_OF_SCHEDULE = "AHEAD_OF_SCHEDULE"


class FeedbackType(str, enum.Enum):
    TOO_EASY = "TOO_EASY"
    TOO_DIFFICULT = "TOO_DIFFICULT"
    VERY_USEFUL = "VERY_USEFUL"
    SKIP = "SKIP"
    ALREADY_KNOW = "ALREADY_KNOW"
    NEED_MORE_PRACTICE = "NEED_MORE_PRACTICE"
    TIME_CONSTRAINT = "TIME_CONSTRAINT"
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    CUSTOM = "CUSTOM"


class AssessmentStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class MessageRole(str, enum.Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    SYSTEM = "SYSTEM"


# ──────────────────────────────────────────────────────────────────────────────
# Learner
# ──────────────────────────────────────────────────────────────────────────────

class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    career_goal: Mapped[Optional[str]] = mapped_column(Text)
    goal_description: Mapped[Optional[str]] = mapped_column(Text)  # natural language
    experience_level: Mapped[Optional[ExperienceLevel]] = mapped_column(SAEnum(ExperienceLevel))
    interests: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    completed_courses: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    previous_projects: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    preferred_learning_style: Mapped[Optional[LearningStyle]] = mapped_column(SAEnum(LearningStyle))
    weekly_hours_available: Mapped[Optional[int]] = mapped_column(Integer)
    target_timeline: Mapped[Optional[str]] = mapped_column(String(100))
    preferred_content_types: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    overall_progress: Mapped[float] = mapped_column(Float, default=0.0)
    total_hours_learned: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    is_demo_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    skills: Mapped[List["LearnerSkill"]] = relationship("LearnerSkill", back_populates="learner", cascade="all, delete-orphan")
    roadmap: Mapped[Optional["Roadmap"]] = relationship("Roadmap", back_populates="learner", uselist=False, cascade="all, delete-orphan")
    chat_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="learner", cascade="all, delete-orphan")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="learner", cascade="all, delete-orphan")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="learner", cascade="all, delete-orphan")


# ──────────────────────────────────────────────────────────────────────────────
# Skill
# ──────────────────────────────────────────────────────────────────────────────

class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[SkillCategory]] = mapped_column(SAEnum(SkillCategory))
    domain: Mapped[Optional[str]] = mapped_column(String(100))
    prerequisites: Mapped[Optional[str]] = mapped_column(Text)  # comma-separated skill names
    difficulty_level: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5

    learner_skills: Mapped[List["LearnerSkill"]] = relationship("LearnerSkill", back_populates="skill")
    assessments: Mapped[List["Assessment"]] = relationship("Assessment", back_populates="skill")


# ──────────────────────────────────────────────────────────────────────────────
# LearnerSkill (junction — tracks proficiency per learner per skill)
# ──────────────────────────────────────────────────────────────────────────────

class LearnerSkill(Base):
    __tablename__ = "learner_skills"
    __table_args__ = (UniqueConstraint("learner_id", "skill_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[int] = mapped_column(Integer, ForeignKey("learners.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id"), nullable=False)
    # Proficiency: 0=None, 1=Beginner, 2=Basic, 3=Intermediate, 4=Advanced, 5=Expert
    current_proficiency: Mapped[float] = mapped_column(Float, default=0.0)
    target_proficiency: Mapped[float] = mapped_column(Float, default=4.0)
    gap_score: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[Optional[SkillPriority]] = mapped_column(SAEnum(SkillPriority))
    status: Mapped[SkillStatus] = mapped_column(SAEnum(SkillStatus), default=SkillStatus.NOT_STARTED)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1 AI confidence in assessment

    learner: Mapped["Learner"] = relationship("Learner", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="learner_skills")


# ──────────────────────────────────────────────────────────────────────────────
# Resource
# ──────────────────────────────────────────────────────────────────────────────

class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    provider: Mapped[Optional[str]] = mapped_column(String(200))
    url: Mapped[Optional[str]] = mapped_column(String(2000))
    type: Mapped[ResourceType] = mapped_column(SAEnum(ResourceType))
    difficulty: Mapped[ResourceDifficulty] = mapped_column(SAEnum(ResourceDifficulty))
    skills_taught: Mapped[Optional[str]] = mapped_column(Text)  # comma-separated skill names
    prerequisite_skills: Mapped[Optional[str]] = mapped_column(Text)  # comma-separated
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    popularity_score: Mapped[int] = mapped_column(Integer, default=50)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True)


# ──────────────────────────────────────────────────────────────────────────────
# Roadmap
# ──────────────────────────────────────────────────────────────────────────────

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[int] = mapped_column(Integer, ForeignKey("learners.id"), nullable=False, unique=True)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    total_phases: Mapped[int] = mapped_column(Integer, default=1)
    current_phase: Mapped[int] = mapped_column(Integer, default=1)
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, default=0)
    completion_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[RoadmapStatus] = mapped_column(SAEnum(RoadmapStatus), default=RoadmapStatus.ACTIVE)
    estimated_completion_date: Mapped[Optional[str]] = mapped_column(String(50))
    schedule_status: Mapped[ScheduleStatus] = mapped_column(SAEnum(ScheduleStatus), default=ScheduleStatus.ON_TRACK)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    learner: Mapped["Learner"] = relationship("Learner", back_populates="roadmap")
    items: Mapped[List["RoadmapItem"]] = relationship(
        "RoadmapItem", back_populates="roadmap",
        order_by="RoadmapItem.phase_number, RoadmapItem.order_index",
        cascade="all, delete-orphan"
    )


# ──────────────────────────────────────────────────────────────────────────────
# RoadmapItem
# ──────────────────────────────────────────────────────────────────────────────

class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.id"), nullable=False)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("resources.id"))
    phase_number: Mapped[int] = mapped_column(Integer, default=1)
    phase_name: Mapped[Optional[str]] = mapped_column(String(200))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[ItemType] = mapped_column(SAEnum(ItemType), default=ItemType.LEARN)
    difficulty: Mapped[ResourceDifficulty] = mapped_column(SAEnum(ResourceDifficulty), default=ResourceDifficulty.INTERMEDIATE)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=2)
    skills_gained: Mapped[Optional[str]] = mapped_column(Text)  # comma-separated
    prerequisite_item_ids: Mapped[Optional[str]] = mapped_column(Text)  # comma-separated IDs
    milestone_text: Mapped[Optional[str]] = mapped_column(Text)
    is_milestone: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[ItemStatus] = mapped_column(SAEnum(ItemStatus), default=ItemStatus.NOT_STARTED)
    why_recommended: Mapped[Optional[str]] = mapped_column(Text)
    scoring_metadata: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    project_info: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="items")
    resource: Mapped[Optional["Resource"]] = relationship("Resource")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="roadmap_item")


# ──────────────────────────────────────────────────────────────────────────────
# Feedback
# ──────────────────────────────────────────────────────────────────────────────

class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[int] = mapped_column(Integer, ForeignKey("learners.id"), nullable=False)
    roadmap_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("roadmap_items.id"))
    type: Mapped[FeedbackType] = mapped_column(SAEnum(FeedbackType))
    message: Mapped[Optional[str]] = mapped_column(Text)
    system_response: Mapped[Optional[str]] = mapped_column(Text)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    learner: Mapped["Learner"] = relationship("Learner", back_populates="feedbacks")
    roadmap_item: Mapped[Optional["RoadmapItem"]] = relationship("RoadmapItem", back_populates="feedbacks")


# ──────────────────────────────────────────────────────────────────────────────
# Assessment
# ──────────────────────────────────────────────────────────────────────────────

class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[int] = mapped_column(Integer, ForeignKey("learners.id"), nullable=False)
    skill_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skills.id"))
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    total_questions: Mapped[int] = mapped_column(Integer, default=5)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    score_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_proficiency: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[AssessmentStatus] = mapped_column(SAEnum(AssessmentStatus), default=AssessmentStatus.NOT_STARTED)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    learner: Mapped["Learner"] = relationship("Learner", back_populates="assessments")
    skill: Mapped[Optional["Skill"]] = relationship("Skill", back_populates="assessments")
    questions: Mapped[List["AssessmentQuestion"]] = relationship("AssessmentQuestion", back_populates="assessment", cascade="all, delete-orphan")


# ──────────────────────────────────────────────────────────────────────────────
# AssessmentQuestion
# ──────────────────────────────────────────────────────────────────────────────

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assessment_id: Mapped[int] = mapped_column(Integer, ForeignKey("assessments.id"), nullable=False)
    question_number: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    correct_answer: Mapped[Optional[str]] = mapped_column(String(10))
    learner_answer: Mapped[Optional[str]] = mapped_column(String(10))
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), default="MEDIUM")

    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="questions")


# ──────────────────────────────────────────────────────────────────────────────
# ChatMessage
# ──────────────────────────────────────────────────────────────────────────────

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    learner_id: Mapped[int] = mapped_column(Integer, ForeignKey("learners.id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context_metadata: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    learner: Mapped["Learner"] = relationship("Learner", back_populates="chat_messages")
