"""AI Provider abstraction — swap between Gemini, OpenAI, or fallback."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json
import httpx
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract AI provider interface."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text response."""
        ...

    @abstractmethod
    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate a structured JSON response."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI provider is available."""
        ...


class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self._available = bool(api_key)

    def is_available(self) -> bool:
        return self._available

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self._available:
            raise RuntimeError("Gemini API key not configured")

        parts = []
        if system_prompt:
            parts.append({"text": f"[SYSTEM INSTRUCTIONS]\n{system_prompt}\n\n[USER REQUEST]\n{prompt}"})
        else:
            parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 8192,
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Empty response from Gemini")
            return candidates[0]["content"]["parts"][0]["text"]

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        json_prompt = f"{prompt}\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation, no code blocks."
        text = await self.generate(json_prompt, system_prompt)
        # Strip markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip().strip("```").strip()
        return json.loads(text)


class FallbackProvider(AIProvider):
    """Deterministic fallback — works without any API key."""

    def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return self._deterministic_response(prompt)

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        return self._deterministic_json_response(prompt)

    def _deterministic_response(self, prompt: str) -> str:
        p = prompt.lower()
        if "what should i learn next" in p or "next" in p:
            return (
                "Based on your profile and current progress, I recommend focusing on "
                "Spring Boot fundamentals next. You have completed Java and SQL, which are "
                "the required prerequisites. Spring Boot is the highest-priority gap for your "
                "Backend Java Developer goal."
            )
        if "skip" in p and "rest" in p:
            return (
                "I've analyzed your profile. If you already know REST APIs, I'll increase your "
                "REST proficiency and deprioritize introductory REST content. Your roadmap will "
                "adapt accordingly, and you can proceed directly to JPA and Spring Security."
            )
        if "too easy" in p:
            return (
                "Understood. I've noted that this material is too easy for you. I'll increase "
                "your estimated proficiency for this topic and skip beginner-level content, "
                "moving you directly to intermediate material."
            )
        if "time" in p or "hours" in p:
            return (
                "I've adjusted your roadmap for your new availability. Optional content has been "
                "deprioritized to protect the critical learning path. Your estimated completion "
                "date has been updated accordingly."
            )
        return (
            "Based on your current learning profile, I recommend continuing with your active "
            "roadmap items. Focus on the highest-priority skill gaps first — these are the "
            "skills most critical to achieving your goal. Let me know if you'd like specific "
            "guidance on any topic."
        )

    def _deterministic_json_response(self, prompt: str) -> Dict[str, Any]:
        p = prompt.lower()
        if "extract" in p or "profile" in p or "parse" in p:
            return {
                "career_goal": "Backend Java Developer",
                "target_role": "Backend Java Developer",
                "timeline": "4 months",
                "weekly_hours": 8,
                "experience_level": "INTERMEDIATE",
                "existing_skills": ["Java", "SQL", "OOP"],
                "interests": ["backend development", "APIs"],
                "completed_courses": [],
                "projects": [],
                "learning_style": "MIXED",
                "confidence": 0.85
            }
        if "skill" in p and ("gap" in p or "require" in p):
            return {
                "required_skills": [
                    {"name": "Spring Boot", "target_proficiency": 4, "priority": "CRITICAL"},
                    {"name": "REST APIs", "target_proficiency": 4, "priority": "CRITICAL"},
                    {"name": "JPA/Hibernate", "target_proficiency": 3, "priority": "RECOMMENDED"},
                    {"name": "Spring Security", "target_proficiency": 3, "priority": "RECOMMENDED"},
                    {"name": "Testing", "target_proficiency": 3, "priority": "RECOMMENDED"},
                    {"name": "Docker", "target_proficiency": 2, "priority": "OPTIONAL"},
                ]
            }
        if "roadmap" in p or "phase" in p:
            return {
                "phases": [
                    {"name": "Foundation", "description": "Java & SQL Mastery"},
                    {"name": "Spring Framework", "description": "Spring Boot & REST"},
                    {"name": "Data Layer", "description": "JPA, Hibernate & Databases"},
                    {"name": "Security & Testing", "description": "Spring Security & Testing"},
                    {"name": "Production", "description": "Docker & Deployment"},
                ]
            }
        return {"result": "fallback", "message": "AI not available, using deterministic response"}


def get_ai_provider() -> AIProvider:
    """Factory — return appropriate AI provider based on configuration."""
    if settings.AI_PROVIDER.lower() == "gemini" and settings.AI_API_KEY:
        logger.info(f"Using Gemini AI provider (model: {settings.AI_MODEL})")
        return GeminiProvider(settings.AI_API_KEY, settings.AI_MODEL)
    logger.warning("AI API key not configured — using deterministic fallback provider")
    return FallbackProvider()


# Module-level singleton
_ai_provider: Optional[AIProvider] = None


def get_provider() -> AIProvider:
    global _ai_provider
    if _ai_provider is None:
        _ai_provider = get_ai_provider()
    return _ai_provider
