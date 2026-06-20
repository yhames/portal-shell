from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    # Application
    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = "data/master.db"
    health_check_interval_seconds: float = Field(default=30, gt=0)
    health_check_timeout_seconds: float = Field(default=3, gt=0)
    health_check_failure_threshold: int = Field(default=3, gt=0)
    health_check_max_concurrency: int = Field(default=10, gt=0)
    health_check_jitter_ratio: float = Field(default=0.2, ge=0, le=1)

_settings = Settings()


def get_settings():
    return _settings
