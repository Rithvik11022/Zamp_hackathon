import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./vendor_db.sqlite"
    cors_origins_str: str = "http://localhost:3000,http://localhost:9000"
    ai_model_fast: str = "claude-haiku-4-5-20241022"
    ai_model_reasoning: str = "claude-sonnet-4-20250514"
    gemini_model: str = "gemini-2.0-flash-lite"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_str.split(",") if o.strip()]

    @property
    def ai_provider(self) -> str:
        if self.gemini_api_key:
            return "gemini"
        if self.anthropic_api_key:
            return "anthropic"
        return "fallback"

    class Config:
        env_file = ".env"


settings = Settings()
