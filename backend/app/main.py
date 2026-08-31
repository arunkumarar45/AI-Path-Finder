"""Main FastAPI application — AI-Powered Personalized Learning Path Recommender."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 Starting AI Learning Path Recommender...")

    # Initialize database tables
    await init_db()
    logger.info("✅ Database initialized")

    # Seed demo data if configured
    if settings.SEED_DEMO_DATA:
        from app.core.database import AsyncSessionLocal
        from app.seed.seed_data import seed_database
        async with AsyncSessionLocal() as db:
            await seed_database(db)

    logger.info(f"✅ AI Provider: {settings.AI_PROVIDER} (key configured: {bool(settings.AI_API_KEY)})")
    logger.info("✅ Application ready")

    yield

    logger.info("👋 Shutting down...")


app = FastAPI(
    title="AI-Powered Personalized Learning Path Recommender",
    description="Intelligent learning assistant that creates personalized learning experiences",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.learners import router as learners_router
from app.api.profile import router as profile_router
from app.api.skill_gaps import router as skill_gaps_router
from app.api.roadmaps import router as roadmaps_router
from app.api.assistant import router as assistant_router
from app.api.feedback import router as feedback_router
from app.api.assessments import router as assessments_router
from app.api.dashboard import router as dashboard_router
from app.api.catalog import router as catalog_router

app.include_router(learners_router)
app.include_router(profile_router)
app.include_router(skill_gaps_router)
app.include_router(roadmaps_router)
app.include_router(assistant_router)
app.include_router(feedback_router)
app.include_router(assessments_router)
app.include_router(dashboard_router)
app.include_router(catalog_router)


@app.get("/")
async def root():
    return {
        "message": "AI-Powered Personalized Learning Path Recommender",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
