from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_path: Path = BASE_DIR / "shopstock.db"
    api_key: SecretStr
    low_stock_default: int = Field(default=5, ge=0)
    debug: bool = False

    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("API_KEY must not be empty")
        return value.strip()

    @field_validator("database_path", mode="before")
    @classmethod
    def resolve_database_path(cls, value: str | Path) -> Path:
        if not str(value).strip():
            raise ValueError("DATABASE_PATH must not be empty")

        path = Path(value).expanduser()
        return path if path.is_absolute() else BASE_DIR / path


settings = Settings()
