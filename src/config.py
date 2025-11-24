"""
Configuration management for Ring Ring Who's There.
Loads environment variables and provides type-safe settings.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Ring API
    ring_username: str
    ring_password: str
    ring_2fa_token: str = ""

    # ElevenLabs (TTS and STT)
    elevenlabs_api_key: str
    elevenlabs_voice_id: str

    # Langfuse
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str = "https://cloud.langfuse.com"

    # Application
    passwords: str  # Comma-separated string, will be parsed to list
    fuzzy_threshold: int = 80
    recording_duration: int = 8
    max_attempts: int = 3
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def password_list(self) -> List[str]:
        """Parse comma-separated passwords into a list."""
        return [p.strip() for p in self.passwords.split(",") if p.strip()]


# Global settings instance
settings = Settings()
