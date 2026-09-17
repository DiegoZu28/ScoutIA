from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = APP_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_ROOT / ".env"), str(APP_ROOT / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    dataset_path: Path = REPO_ROOT / "data" / "processed" / "dataset.parquet"
    models_dir: Path = REPO_ROOT / "models"
    cors_origins: list[str] = ["http://localhost:4200"]
    top_n_contribuciones: int = 8
    openai_api_key: str | None = None
    llm_modelo: str = "gpt-4o-mini"


@lru_cache
def get_settings() -> Settings:
    return Settings()
