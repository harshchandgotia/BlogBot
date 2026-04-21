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

    def validate_keys(self, *, require_tavily: bool = False) -> None:
        """Fail fast with a readable message if required API keys are missing.

        Called at import time (GROQ only) and again in the research node
        (with require_tavily=True) before any network call.
        """
        missing: list[str] = []
        if not self.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if require_tavily and not self.TAVILY_API_KEY:
            missing.append("TAVILY_API_KEY")
        if missing:
            raise RuntimeError(
                "Missing required API key(s): "
                + ", ".join(missing)
                + f". Copy .env.example to .env at {_ROOT} and fill in the values."
            )


settings = Settings()
settings.ensure_dirs()
settings.validate_keys(require_tavily=False)
