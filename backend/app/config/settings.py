from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
    )

    # Application
    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = "data/master.db"

_settings = Settings()


def get_settings():
    return _settings
