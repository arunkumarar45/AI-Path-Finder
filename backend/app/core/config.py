from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./learning_path.db"
    AI_PROVIDER: str = "gemini"
    AI_API_KEY: str = ""
    AI_MODEL: str = "gemini-1.5-flash"
    SEED_DEMO_DATA: bool = True
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    DEBUG: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
