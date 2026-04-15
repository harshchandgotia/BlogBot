"""Central configuration loaded from environment + .env file."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API keys
    GROQ_API_KEY: str = ""
    TAVILY_API_KEY: str = ""

    # LLM
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.5
    LLM_MAX_RETRIES: int = 3

    # Research
    MAX_RESEARCH_RESULTS_PER_QUERY: int = 10
    MAX_QUERIES: int = 10

    # Images
    IMAGE_COUNT_TARGET: int = 3

    # Directories (relative to repo root)
    OUTPUT_DIR: Path = _ROOT / "outputs"
    IMAGE_DIR: Path = _ROOT / "images"
    HISTORY_DIR: Path = _ROOT / "history"

    def ensure_dirs(self) -> None:
        for d in (self.OUTPUT_DIR, self.IMAGE_DIR, self.HISTORY_DIR):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
